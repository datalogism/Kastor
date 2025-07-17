"""
KD1_initializeKastorFromShape.py

This module is responsible for initializing KaSTOR by loading and processing shape files into a SPARQL endpoint.
It handles the creation of new shape namespaces and manages the storage of shape definitions.
"""

import sys
from argparse import ArgumentParser
import logging

# Import custom modules for handling signatures and triple shapes
import src.class_signatures as cs
import src.triple_shapes as ts

# Import required RDF and SPARQL handling libraries
from rdflib import Graph
from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
import json

def sparql_service_update(service, update_query):
    """
    Execute a SPARQL update query against a SPARQL endpoint.
    
    Args:
        service (str): The URL of the SPARQL endpoint
        update_query (str): The SPARQL update query to execute
        
    Returns:
        str: 'Done' if successful, raises exception otherwise
    """
    sparql = SPARQLWrapper(service)
    sparql.setMethod(POST)
    sparql.setRequestMethod(POSTDIRECTLY)
    sparql.setQuery(update_query)
    sparql.query()
    return 'Done'

def sparql_service_to_int(service, query):
    """
    Execute a SPARQL query and return the result as an integer.
    
    Args:
        service (str): The URL of the SPARQL endpoint
        query (str): The SPARQL query to execute
        
    Returns:
        int: The integer result of the query
        
    Note:
        This function expects the query to return a single numeric value.
    """
    sparql = SPARQLWrapper(service)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()

    processed_results = json.load(result.response)
    cols = processed_results['head']['vars']

    out = None
    for row in processed_results['results']['bindings']:
        for c in cols:
            out = int(row.get(c, {}).get('value'))

    return out

if __name__ == '__main__':
    # Set up command line argument parsing
    parser = ArgumentParser(description='Initialize KaSTOR by loading shape files into the SPARQL endpoint')
    parser.add_argument("-s", "--shape_file_path", default=None, 
                       help="Path to the shape file to be loaded")
    args = parser.parse_args()
    
    # Initialize SPARQL endpoint connection
    sparql_ep_uri = 'http://localhost:8080/sparql'
    sparql_ep = SPARQLWrapper(sparql_ep_uri)

    # Process shape file if provided
    if args.shape_file_path:
        print("Loading shape file...")
        # Parse the shape file
        shape = Graph()
        shape.parse(args.shape_file_path)
        
        # Extract shape type and create namespaces
        type_triples = ts.getShapeType(shape)
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        content_shape = shape.serialize(format="nt").replace("\n", "")

        # Define namespaces for the new shape and class IDs
        ns_shape = "http://ns.inria.fr/kstor/shapes/" + shape_name
        ns_class_ids = "http://ns.inria.fr/kstor/class_randoms_id/" + type_triples_name

        print(f"New Shape Namespace: {ns_shape}")
        print(f"New Type ID Namespace: {ns_class_ids}")

        # Check if shape already exists in the endpoint
        count_query = f"""
        SELECT (COUNT(DISTINCT ?s) as ?nb) 
        FROM <{ns_shape}> 
        WHERE {{ ?s ?p ?o. }}
        """
        sparql_ep.setQuery(count_query)
        sparql_ep.setReturnFormat(JSON)
        qres = sparql_ep.query().convert()
        nb_triples = int(qres["results"]["bindings"][0]["nb"]["value"])

        # If shape doesn't exist, create it
        if nb_triples == 0:
            logging.info("Creating new shape namespace")
            insert_query = f"""
            INSERT DATA {{ 
                GRAPH <{ns_shape}> {{ {content_shape} }}
            }}
            """
            sparql_ep.setMethod(POST)
            sparql_ep.setRequestMethod(POSTDIRECTLY)
            sparql_ep.setQuery(insert_query)
            sparql_ep.query()

            # Verify the shape was created
            count_query = f"""
            SELECT (COUNT(DISTINCT ?s) as ?nb) 
            FROM <{ns_shape}> 
            WHERE {{ ?s ?p ?o. }}
            """
            sparql_ep.setQuery(count_query)
            sparql_ep.setReturnFormat(JSON)
            qres = sparql_ep.query().convert()
            print("DATA INSERTED:")
            print(qres)

        # Check if class IDs already exist in the endpoint
        count_query = f"""
        SELECT (COUNT(DISTINCT ?s) as ?nb) 
        FROM <{ns_class_ids}> 
        WHERE {{ ?s ?p ?o. }}
        """
        print(count_query)
        sparql_ep.setQuery(count_query)
        sparql_ep.setReturnFormat(JSON)
        qres = sparql_ep.query().convert()
        nb_triples = int(qres["results"]["bindings"][0]["nb"]["value"])
        print("NB ALREADY ADDED IN TYPE IDS >", nb_triples)

        # Create UUID class entities
        res = cs.CreateUUIDClassEntities2(type_triples, ns_class_ids, sparql_ep_uri)
        logging.info("END uuid creation process")
    else:
        logging.error("Shape file path not provided")
