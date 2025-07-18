#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1_KD-31_Wikicheck_plain_dt_only.py

This script processes RDF shape files and checks for property values in abstracts of entities.
It compares property values from a knowledge graph with values found in entity abstracts,
and stores the results in a named graph for further analysis.

Created on Fri Sep 27 10:35:40 2024
"""

from rdflib import Graph
from argparse import ArgumentParser

# Import custom modules for RDF processing and SPARQL operations
import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct
import src.class_signatures as cs

import sys

if __name__ == '__main__':
    # Set up command line argument parsing
    parser = ArgumentParser(description='Process RDF shapes and check property values in abstracts.')
    parser.add_argument("-s", "--shape_file_path", default=None,
                       help="Path to the RDF shape file containing property definitions")
    parser.add_argument("-ng", "--searchspace_namedgraph", 
                       default="http://ns.inria.fr/kstor/#inferences",
                       help="Named graph URI to search for entities")
    args = parser.parse_args()

    # Check if required arguments are provided
    if args.shape_file_path and args.searchspace_namedgraph:
        # Parse the RDF shape file
        shape = Graph()
        shape.parse(args.shape_file_path)

        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        # SPARQL endpoint configuration
        sparql_ep = 'http://localhost:8080/sparql'
        search_ng = args.searchspace_namedgraph
        #found_ng = "http://ns.inria.fr/kstor/#found_in_abtract"

        found_ng = "http://ns.inria.fr/kstor/wikichecked/" + shape_name + "/abtract_clean"

        # Get property information from the shape file
        print(">> get useful data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        
        # Create a mapping between simplified and full property names
        dict_simply_real = {}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)] = p
            
        # Get property types and type triples from the shape
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)
        
        # Clean flag - if True, will clear the found_ng graph before processing
        clean = False

        # Clean the target graph if clean flag is True
        if clean:
            # Count entities before cleaning
            query = f"""PREFIX dbo: <http://dbpedia.org/ontology/> 
                       PREFIX ks: <http://ns.inria.fr/kstor/#> 
                       SELECT (COUNT(DISTINCT ?s) as ?nb) 
                       FROM <{found_ng}> 
                       WHERE {{ ?s ?p ?o }}"""
            res = ct.get_sparql_dataframe(sparql_ep, query)
            print("BEFORE>", res)
            
            # Clear the found_ng graph
            query = f"PREFIX ks: <http://ns.inria.fr/kstor/#> DROP GRAPH {found_ng}"
            res = ct.sparql_service_update(sparql_ep, query)
            
            # Count entities after cleaning
            query = f"""PREFIX dbo: <http://dbpedia.org/ontology/> 
                       PREFIX ks: <http://ns.inria.fr/kstor/#> 
                       SELECT (COUNT(DISTINCT ?s) as ?nb) 
                       FROM <{found_ng}> 
                       WHERE {{ ?s ?p ?o }}"""
            res = ct.get_sparql_dataframe(sparql_ep, query)
            print("AFTER>", res)

        # Get total number of entities to process
        nb_entities = cs.get_NbEntitiesNG(search_ng, sparql_ep)
        size_sample = nb_entities
        nb_loop = 0
        count_ent_checked = 0
        offset = 0
        limit = 100  # Process entities in batches of 100
        done = []  # Track processed entities
        
        # Get total number of entities that need processing
        to_do = cs.get_NbEntitiesNGToDo(search_ng, found_ng, sparql_ep)

        # Main processing loop
        while count_ent_checked != to_do:
            print(">>>>>>>>>>>>>>>>>>>>>LOOP :", nb_loop, ">", count_ent_checked, "/", to_do)
            
            # Get a batch of entities to process
            sample = cs.get_sampleNG_to_update(search_ng, found_ng, sparql_ep, limit, offset)

            # Process each entity in the current batch
            for index, row in sample.iterrows():
                # Clean the entity URI
                uri = rs.cleanEntURL(row["s"])
                
                # Track processed entities
                if uri not in done:
                    count_ent_checked += 1
                    done.append(uri)
                
                # Get the abstract for the current entity
                abs_ = cs.get_abstract(row["s"], sparql_ep)
                
                if len(abs_) > 0:
                    abstract = abs_["abstract"][0]
                    current_prop = row["p"]
                    val = str(row["o"])

                    # Clean the property value
                    if val not in ["nan", "NaN", ""]:
                        val = rs.cleanTxt(val)
                    
                    # Check if the property value appears in the abstract
                    if val != "":
                        val = rs.cleanTxt(val)
                        found = ts.find_in_abstract(abstract, current_prop, val, type_prop[current_prop])
                        
                        # If found, store the result in the found_ng graph
                        if found:
                            # Prepare the data for insertion
                            temp_new = {
                                "ent_uri": uri,
                                "type": type_prop[current_prop],
                                "prop": current_prop,
                                "value": [val]
                            }

                            # Escape quotes in the value for SPARQL query
                            if '"' in val or "'" in val:
                                val = val.translate(str.maketrans({"'": r"\'", '"': r'\"'}))
                            
                            # Insert the found property value into the results graph
                            query = f"""PREFIX dbo: <http://dbpedia.org/ontology/> 
                                       PREFIX ks: <http://ns.inria.fr/kstor/#> 
                                       INSERT DATA {{ 
                                           GRAPH <{found_ng}> {{ 
                                               <{uri}> <{current_prop}> '{val}'^^{type_prop[current_prop]}
                                           }}
                                       }}"""
                            res = ct.sparql_service_update(sparql_ep, query)
            
            # Update the count of remaining entities to process
            to_do = cs.get_NbEntitiesNGToDo(search_ng, found_ng, sparql_ep)
            nb_loop += 1  # Increment loop counter
            
            # Update offset for the next batch
            offset += limit
