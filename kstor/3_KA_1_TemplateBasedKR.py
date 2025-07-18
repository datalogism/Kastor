#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KD4_getExampleSpecificAbstractTemplate.py

This script generates synthetic RDF data by analyzing patterns in existing knowledge graphs.
It creates new entities based on property patterns found in a given shape file and sample data.

Created on Wed Oct  9 09:28:16 2024
"""
# Standard library imports
import sys
import json
import random
from datetime import datetime
from os.path import isfile, join
from argparse import ArgumentParser

# Third-party imports
from rdflib import Graph
import pandas as pd
from bs4 import BeautifulSoup  # For HTML parsing
from markdown import markdown  # For markdown to text conversion

# Local application imports
import src.rdf_synthax_fct as rs  # RDF syntax helper functions
import src.triple_shapes as ts  # For working with RDF shapes
import src.class_signatures as cs  # For class signature operations
import src.corese_tools as ct  # For SPARQL queries


def md_to_text(md):
    """
    Convert markdown text to plain text by first converting to HTML and then extracting text.

    Args:
        md (str): Markdown formatted string

    Returns:
        str: Plain text with HTML tags removed
    """
    # Convert markdown to HTML
    html = markdown(md)
    # Parse HTML
    soup = BeautifulSoup(html, features='html.parser')
    # Extract plain text from HTML
    return soup.get_text()


if __name__ == '__main__':
    # Set up command line argument parsing
    parser = ArgumentParser(description='Generate synthetic RDF data based on patterns in a knowledge graph.')

    # Define command line arguments
    parser.add_argument("-s", "--shape_file_path",
                        help="Path to the shape file defining the RDF structure")
    parser.add_argument("-size_gen", "--size_sample_togen", default=1000,
                        help="Number of samples to generate")
    parser.add_argument("-ng", "--named_graph_sample",
                        help="Named graph containing the sample data")
    parser.add_argument("-ref_prop", "--ref_prop", default="http://dbpedia.org/ontology/alias",
                        help="Reference property for generating new entities")
    parser.add_argument("-gs", "--generation_strategy", default="KR_same_level",
                        choices=["KR_same_level", "KR_low_level"],
                        help="Strategy for generating new entities")

    # Parse command line arguments
    args = parser.parse_args()

    # Check if required arguments are provided
    if args.shape_file_path:
        # Initialize RDF graph and load the shape file
        shape = Graph()
        shape.parse(args.shape_file_path)

        # Configuration parameters
        sparql_ep = 'http://localhost:8080/sparql'  # SPARQL endpoint for querying the knowledge graph
        size_sample_togen = args.size_sample_togen  # Number of samples to generate
        ref_prop = args.ref_prop  # Reference property for generating new entities
        ref_prop_simply = ref_prop.split("/")[-1]  # Simplified property name (last part of URI)
        gen_strat = args.generation_strategy  # Strategy for generating new entities
        found_ng = args.named_graph_sample  # Source named graph
        new_ng = found_ng + "/synthetic/" + gen_strat + "_" + ref_prop_simply  # Target named graph for synthetic data

        print("================================ CURRENT SAMPLE :", new_ng)

        default_ng = "<urn:x-arq:DefaultGraph>"
        print(">> get usefull data")
        # Extract namespaces from the shape file
        namespaces = shape.namespaces()

        # Get all properties defined in the shape
        prop_focus = ts.getShapeProp(shape)
        prop_focus2 = []  # Will store properties that exist in the actual data
        dict_simply_real = {}  # Maps simplified property names to full URIs

        # Create a mapping from simplified property names to full URIs
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)] = p

        # Get properties with their types and the main type of the shape
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)  # Main type defined in the shape

        # Extract shape name from the file path
        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")

        # Count total number of subjects in the named graph
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/> 
        PREFIX ks: <http://ns.inria.fr/kstor/#> 
        SELECT (COUNT(DISTINCT ?s) as ?nb) 
        FROM <{found_ng}> 
        WHERE {{ ?s ?p ?o }}
        """
        res = ct.get_sparql_dataframe(sparql_ep, query)
        print(f"Total entities in graph: {res['nb'][0]}")

        # Calculate statistics for each property
        prop_stats = {}
        for prop in prop_focus:
            # Count how many times each property is used in the graph
            nb = cs.get_PropertiesRealised(prop, found_ng, sparql_ep)
            if int(nb) > 0:
                prop_focus2.append(prop)  # Only keep properties that exist in the data
                # Calculate the ratio of entities that have this property
                prop_stats[prop] = nb / res["nb"][0]

        # Get all possible class signatures based on the shape and existing properties
        class_sign_all = cs.get_All_ClassSignatures(shape, prop_focus2)

        # Get a random sample of entities that have the reference property
        # This helps in finding representative examples for template generation
        entities = cs.get_PropertyRandomSample_NG(
            type_triples,  # Type of entities to sample
            [ref_prop],  # Required properties
            prop_focus2,  # All properties to consider
            found_ng,  # Source named graph
            sparql_ep,  # SPARQL endpoint
            size_sample=size_sample_togen  # Number of samples to get
        )

        # Analyze property patterns in the sampled entities
        pattern_count = {}
        for uri in entities:
            # Query all properties for the current entity
            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>  
            SELECT ?p ?o 
            FROM <{found_ng}> 
            WHERE {{ 
                <{uri}> ?p ?o.
            }}
            """
            res = ct.get_sparql_dataframe(sparql_ep, query)

            # Extract all properties for this entity
            pattern = []
            for index, row2 in res.iterrows():
                real_prop = row2["p"]
                pattern.append(real_prop)

            # Create a sorted tuple of unique properties as a pattern key
            unique_props = list(set(pattern))
            unique_props.sort()
            pattern_key = tuple(unique_props)

            # Count occurrences of each pattern
            pattern_count[pattern_key] = pattern_count.get(pattern_key, 0) + 1
        print(pattern_count)

        # TO UNCOMMENT IF YOU WANT TO CREATE A CSV FILE WITH THE PATTERN COUNT
        # class_sign_freq_dt = []
        # list_prop = list(dict_simply_real.keys())
        # n = 0
        # for pattern in pattern_count.keys():
        #    print(pattern)
        #    tempo = ["pattern" + str(n)]
        #    for prop in list_prop:
        #        if (prop in str(pattern)):
        #            tempo.append(1)
        #        else:
        #            tempo.append(0)
        #    tempo.append(pattern_count[pattern])
        #    class_sign_freq_dt.append(tempo)
        #    n += 1
        # colnames_ = ["pattern"] + list_prop + ["nb_real"]
        # df = pd.DataFrame(class_sign_freq_dt, columns=colnames_)
        # df.to_csv(dir_out + 'RDF_stats_alias_based_' + shape_name + '_sample1X10.csv', encoding='utf-8', index=True)

        #### RETRIEVE ALREADY CREATED DATA
        selected_couples = []

        # Query for existing synthetic data in the target graph
        query = f"""
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX dbo: <http://dbpedia.org/ontology/>  
        SELECT ?uri_0 ?uri_1 
        FROM <{new_ng}> 
        WHERE {{ 
            ?uri_0 prov:wasDerivedFrom ?uri_1.
        }}
        """
        res = ct.get_sparql_dataframe(sparql_ep, query)

        # Store existing URI pairs to avoid regenerating them
        for index, row in res.iterrows():
            key = f"{row['uri_0']}|{row['uri_1']}"
            if key not in selected_couples:
                selected_couples.append(key)

        print(f"Found {len(selected_couples)} existing synthetic examples")

        # Prepare named graph for storing abstract templates
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        abstract_ng = f"http://ns.inria.fr/kstor/wiki_md/{type_triples_name}"  # Named graph for markdown abstracts

        # Main loop to generate synthetic data until we have enough samples
        while len(selected_couples) < size_sample_togen:
            new_couples = []
            print(f"\nCurrent progress: {len(selected_couples)}/{size_sample_togen} samples generated")

            # Strategy 1: Replace with lower-level pattern (sub-pattern)
            if gen_strat == "KR_low_level":
                # Randomly select a pattern from those we've observed
                random_patt = random.choice(list(pattern_count.keys()))

                # Find all patterns that are subsets of the selected pattern
                smaller_patt = [k for k in pattern_count.keys()
                                if len(k) < len(random_patt)]

                # Filter to only keep patterns that are proper subsets
                accepted_patt = []
                for sp in smaller_patt:
                    set_rp = set(random_patt)
                    set_sp = set(sp)
                    # Check if sp is a subset of random_patt
                    if len(set_sp - set_rp) == 0:
                        accepted_patt.append(list(set_sp))

                # If we found valid sub-patterns
                if len(accepted_patt) > 0:
                    # Randomly select one sub-pattern
                    randomlow_patt = random.choice(accepted_patt)

                    # Get entities matching the original and sub-pattern
                    entity_0 = cs.get_ClassSignatureRandomSample_NG(
                        type_triples, list(random_patt), prop_focus2,
                        found_ng, sparql_ep, size_sample=1
                    )
                    entity_1 = cs.get_ClassSignatureRandomSample_NG(
                        type_triples, list(randomlow_patt), prop_focus2,
                        found_ng, sparql_ep, size_sample=1
                    )

                    # Create a key for this pair
                    key = f"{entity_1[0]}|{entity_0[0]}"

                    # Add to our collections if not already present
                    if key not in selected_couples:
                        selected_couples.append(key)
                        new_couples.append(key)

            # Strategy 2: Replace with same-level pattern (different entities with same pattern)
            elif gen_strat == "KR_same_level":
                # Only consider patterns that appear multiple times
                class_sign_freq_with_duo = [
                    k for k in pattern_count.keys()
                    if pattern_count[k] > 1  # Ensure we have multiple examples
                ]

                try:
                    # Randomly select a pattern with multiple occurrences
                    random_patt = random.choice(class_sign_freq_with_duo)
                except IndexError:
                    # No valid patterns found
                    random_patt = None

                if random_patt is not None:
                    # Get two random entities that match this pattern
                    entities = cs.get_ClassSignatureRandomSample_NG(
                        type_triples, list(random_patt), prop_focus2,
                        found_ng, sparql_ep, size_sample=2
                    )

                    # Create both possible orderings of the pair
                    key1 = f"{entities[0]}|{entities[1]}"
                    key2 = f"{entities[1]}|{entities[0]}"

                    # Add both orderings if not already present
                    if key1 not in selected_couples:
                        selected_couples.append(key1)
                        new_couples.append(key1)

                    if key2 not in selected_couples:
                        selected_couples.append(key2)
                        new_couples.append(key2)

            print(f"Generated {len(new_couples)} new pairs in this iteration")

            # Process each new pair of entities
            for couples_raw in new_couples:
                print(f"\nProcessing pair: {couples_raw}")

                # Split the pair into individual URIs
                couples = couples_raw.split('|')
                print(f"Source: {couples[0]}")
                print(f"Target: {couples[1]}")

                # Process the URIs (template and new entity)
                uri_template_0 = rs.uncodeurl(couples[0])  # Decode URL-encoded characters
                uri_template = rs.cleanEntURL(couples[0])  # Clean the URI
                uri_new_0 = rs.uncodeurl(couples[1])
                uri_new = rs.cleanEntURL(couples[1])

                # Get the abstract for the template entity
                print(f"Fetching abstract for template: {uri_template}")
                template_abs = cs.get_abstractMD(uri_template, abstract_ng, sparql_ep)

                # Query for the template's property values
                query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>  
                SELECT ?p ?o 
                FROM <{found_ng}> 
                WHERE {{ 
                    <{uri_template}> ?p ?n. 
                    ?n rdf:value ?o.
                }}
                """
                print("Executing query:", query)
                template_graph = ct.get_sparql_dataframe(sparql_ep, query)

                # Sort values by length (longest first) to prioritize more descriptive values
                if not template_graph.empty:
                    template_graph['length'] = template_graph['o'].str.len()
                    template_graph.sort_values('length', ascending=False, inplace=True)
                    print(f"Found {len(template_graph)} property values for template")
                print("~~~~~~~~~~~~~~")
                template_abs = template_abs["abstract"][0]
                print("ORIG:")
                print(md_to_text(template_abs))

                for index, row2 in template_graph.iterrows():
                    # print(row2)
                    real_prop = row2["p"]

                    if (real_prop in type_prop.keys()):
                        val = str(row2["o"])
                        # print(real_prop,">",val)
                        template_abs = ts.find_in_abstractAndPropTag(template_abs, real_prop, val, type_prop[real_prop])

                        # abstract=ts.find_in_abstractAndMASK(abstract, real_prop, val, type_prop[real_prop])
                print("PATTERN ABS")
                print(template_abs)

                template_abs = md_to_text(template_abs)

                print("uri new >", uri_new)
                query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <" + found_ng + "> { <" + uri_new + "> ?p ?n. ?n rdf:value ?o. }"
                new_graph0 = ct.get_sparql_dataframe(sparql_ep, query)
                new_graph = new_graph0.copy()
                new_graph['length'] = new_graph['o'].str.len()
                new_graph.sort_values('length', ascending=False, inplace=True)
                print("~~~~~~~~~~~~~~")
                print(new_graph)
                new_abs = template_abs
                for index, row2 in new_graph.iterrows():
                    real_prop = row2["p"]
                    if (real_prop in type_prop.keys()):
                        if ("dbo:" in type_prop[real_prop]):
                            uri = str(row2["o"])
                            query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?label FROM " + default_ng + " { <" + uri + "> <http://www.w3.org/2000/01/rdf-schema#label>  ?label. }"
                            res_label = ct.get_sparql_dataframe(sparql_ep, query)
                            val = res_label["label"][0]
                        elif ("Date" in real_prop):
                            val = str(row2["o"])
                            val = datetime.strptime(val, "%Y-%m-%d").strftime('%d %B %Y')
                        else:
                            val = str(row2["o"])
                        if ("http://dbpedia.org/resource/" in val or "https://dbpedia.org/resource/" in val):
                            val = val.replace("http://dbpedia.org/resource/", "").replace(
                                "https://dbpedia.org/resource/", "").replace("_", " ")

                        if ("$" + real_prop + "$" in new_abs):
                            new_abs = new_abs.replace("$" + real_prop + "$", val)

                print(">>>>>>>>>>>>>")
                print(new_abs)
                print("derived from ", uri_template)
                print("using >", new_graph0)
                print("xxxxxxxxxxxxx")

                if ('"' in new_abs or "'" in new_abs or "\\" in new_abs):
                    new_abs = new_abs.translate(str.maketrans({"'": r"\'", '"': r'\"', "\\": "\\\\"}))

                ##################################### ABSTRACT AND META INFO
                query = "PREFIX prov: <http://www.w3.org/ns/prov#> PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + new_ng + "> { <" + uri_new + "> prov:wasDerivedFrom <" + uri_template_0 + ">. <" + uri_new_0 + "> <http://www.w3.org/2000/01/rdf-schema#comment>  '" + new_abs + "'.  }}"
                print(query)
                res = ct.sparql_service_update(sparql_ep, query)
                print(res)

