#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1_KD-321_RetrieveWikiMD.py

This script retrieves Wikipedia markdown abstracts for entities in a knowledge graph.
It connects to a SPARQL endpoint, finds entities without markdown abstracts, fetches
the markdown from Wikipedia API, and stores it back in the knowledge graph.

Usage Example:
    python 1_KD-321_RetrieveWikiMD.py \
        --shape_file_path "/path/to/shape_file.ttl" \

Arguments:
    -s, --shape_file_path:       Path to the RDF shape file (.ttl) containing property definitions

"""

from rdflib import Graph
from argparse import ArgumentParser

# Import custom modules
import src.triple_shapes as ts
import src.corese_tools as ct
import src.abstractExtended as ae
from SPARQLWrapper import JSON, SPARQLWrapper


def getNbEntToDO(sparql_ep, search_ng, current_ng):
    """
    Count the number of entities that need markdown abstracts.

    Args:
        sparql_ep (str): SPARQL endpoint URL
        search_ng (str): Named graph to search for entities
        current_ng (str): Named graph containing existing markdown abstracts

    Returns:
        int: Number of entities that need markdown abstracts
    """
    sparql = SPARQLWrapper(sparql_ep)
    query = """PREFIX dcat: <http://www.w3.org/ns/dcat#> 
             SELECT (COUNT(DISTINCT ?s) as ?nb) 
             FROM <{0}> 
             WHERE {{ 
                 ?s dcat:resource_identifier ?uid. 
                 FILTER NOT EXISTS {{ 
                     GRAPH <{1}> {{ ?s ?p ?o }}  
                 }} 
             }}""".format(search_ng, current_ng)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    return int(qres["results"]["bindings"][0]["nb"]["value"])


def get_SubjectsToRetrieveWithIDAndIdNS(sparql_ep, search_ng, id_ng, current_ng, limit):
    """
    Retrieve entities that need markdown abstracts with their Wikipedia revision IDs.

    Args:
        sparql_ep (str): SPARQL endpoint URL
        search_ng (str): Named graph to search for entities
        id_ng (str): Named graph containing entity IDs
        current_ng (str): Named graph containing existing markdown abstracts
        limit (int): Maximum number of entities to retrieve

    Returns:
        list: List of dictionaries containing subject URIs and their Wikipedia revision IDs
    """
    sparql = SPARQLWrapper(sparql_ep)
    query = """PREFIX dcat: <http://www.w3.org/ns/dcat#> 
             SELECT ?s ?id 
             FROM <{0}> 
             WHERE {{ 
                 GRAPH <{1}> {{ ?s dcat:resource_identifier ?uid }}.
                 ?s <http://dbpedia.org/ontology/wikiPageRevisionID> ?id. 
                 FILTER NOT EXISTS {{ 
                     GRAPH <{2}> {{ ?s ?p ?o }}  
                 }}
             }} 
             ORDER BY ASC(?uid) 
             LIMIT {3}""".format(search_ng, id_ng, current_ng, limit)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    return [{"subj": row["s"]["value"], "id": row["id"]["value"]}
            for row in qres["results"]["bindings"]]


if __name__ == '__main__':
    # Parse command line arguments
    parser = ArgumentParser(description='Retrieve Wikipedia markdown abstracts for entities in the knowledge graph.')
    parser.add_argument("-s", "--shape_file_path", default=None,
                        help="Path to the shape file defining the entity types to process")
    args = parser.parse_args()

    # Configuration
    wikipedia_agent = "(WEBSITE; MAIL) AgentName"  # User agent for Wikipedia API
    sparql_ep = 'http://localhost:8080/sparql'  # SPARQL endpoint
    search_ng = "urn:x-arq:DefaultGraph"  # Default graph to search for entities

    if args.shape_file_path:
        print("Loading shape file...")
        # Load the shape file to determine which types of entities to process
        shape = Graph()
        shape.parse(args.shape_file_path)
        type_triples = ts.getShapeType(shape)
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")

        # Define named graphs for IDs and markdown storage
        ns_class_ids = "http://ns.inria.fr/kstor/class_randoms_id/" + type_triples_name
        current_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name

        # Initialize counters and pagination
        nb_loop = 0
        count_ent_checked = 0
        limit = 10000  # Process entities in batches of 10,000

        # Get initial count of entities needing processing
        to_do = getNbEntToDO(sparql_ep, ns_class_ids, current_ng)
        print(f">>> Processing {to_do} entities that need markdown abstracts")

        # Process entities in batches
        while to_do > 0:
            print(f">>> Loop {nb_loop}: Processed {count_ent_checked}/{to_do} entities")

            # Get a batch of entities that need markdown
            sample = get_SubjectsToRetrieveWithIDAndIdNS(
                sparql_ep, search_ng, ns_class_ids, current_ng, limit)

            # Process each entity in the batch
            for node in sample:
                uri = node["subj"]
                wiki_id = node["id"]

                # Extract entity name from URI
                entity_splm = uri.replace('http://dbpedia.org/resource/', '') \
                    .replace('https://dbpedia.org/resource/', '')

                print(f"Processing entity: {entity_splm}")

                # Get markdown abstract from Wikipedia
                md_entity = ae.getAbstractMD2(entity_splm, wiki_id, wikipedia_agent)

                # Escape special characters in markdown for SPARQL
                if any(char in md_entity for char in ['"', "'", "\\"]):
                    md_entity = md_entity.translate(
                        str.maketrans({"'": r"\'", '"': r'\"', "\\": "\\\\"}))

                # Insert markdown into the knowledge graph
                query = """PREFIX dbo: <http://dbpedia.org/ontology/> 
                         PREFIX ks: <http://ns.inria.fr/kstor/#> 
                         INSERT DATA {{ 
                             GRAPH <{0}> {{ 
                                 <{1}> <http://www.w3.org/2000/01/rdf-schema#comment> '{2}' 
                             }}
                         }}""".format(current_ng, uri, md_entity)

                try:
                    # Execute the update query
                    res = ct.sparql_service_update(sparql_ep, query)
                    count_ent_checked += 1
                except Exception as e:
                    print(f"Error processing entity {uri}:")
                    print(f"Query: {query}")
                    print(f"Error: {str(e)}")
                    print("=" * 50)

            # Update the count of remaining entities
            to_do = getNbEntToDO(sparql_ep, ns_class_ids, current_ng)
            nb_loop += 1

        print(f"Processing complete. Processed {count_ent_checked} entities in total.")
