import sys
from argparse import ArgumentParser
import logging

import src.class_signatures as cs
import src.triple_shapes as ts


from rdflib import Graph
from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
import json

def sparql_service_update(service, update_query):
    """
    Helper function to update (DELETE DATA, INSERT DATA, DELETE/INSERT) data.

    """
    sparql = SPARQLWrapper(service)
    sparql.setMethod(POST)
    sparql.setRequestMethod(POSTDIRECTLY)
    sparql.setQuery(update_query)
    sparql.query()

    # SPARQLWrapper is going to throw an exception if result.response.status != 200:

    return 'Done'

def sparql_service_to_int(service, query):
    """
    Helper function to convert SPARQL results into a Pandas DataFrame.

    Credit to Ted Lawless https://lawlesst.github.io/notebook/sparql-dataframe.html
    """
    sparql = SPARQLWrapper(service)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()

    processed_results = json.load(result.response)
    cols = processed_results['head']['vars']

    out = None
    for row in processed_results['results']['bindings']:
        item = []
        for c in cols:
            out=int(row.get(c, {}).get('value'))

    return out
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    args = parser.parse_args()
    print("HEY")

    sparql_ep_uri = 'http://localhost:8080/sparql'

    sparql_ep = SPARQLWrapper(sparql_ep_uri)
    if args.shape_file_path:
        print("shape load")
        shape = Graph()
        shape.parse(args.shape_file_path)
        type_triples = ts.getShapeType(shape)
        type_triples_name= type_triples.replace("http://dbpedia.org/ontology/","")

        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        content_shape = shape.serialize(format="nt").replace("\n", "")

        ns_shape = "http://ns.inria.fr/kstor/shapes/" + shape_name
        ns_class_ids = "http://ns.inria.fr/kstor/class_randoms_id/"+type_triples_name



        ########## TEST

       # count_query = " select ?abs FROM  <urn:x-arq:DefaultGraph>  where { ?s a <"+type_triples+">. ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abs.  } LIMIT 1000"
      #  sparql_ep.setQuery(count_query)
       # sparql_ep.setReturnFormat(JSON)
        #qres = sparql_ep.query().convert()
        #print(qres)
        print("NEW SHAPE NS ?",ns_shape)
        print("NEW TYPE ID NS ?",ns_class_ids)
        #sys.exit()

        #################### NG CREATION
        count_query = "SELECT  (COUNT( DISTINCT ?s) as ?nb)  FROM <" + ns_shape + "> WHERE { ?s ?p ?o. }"
        sparql_ep.setQuery(count_query)
        sparql_ep.setReturnFormat(JSON)
        qres = sparql_ep.query().convert()
        nb_triples=int(qres["results"]["bindings"][0]["nb"]["value"])

        if(nb_triples==0):
            logging.info("CREATE NEW SHAPE NAMESPACE")
            insert_query = "INSERT DATA { GRAPH <" + ns_shape + "> { " + content_shape + " }}"
            sparql_ep.setMethod(POST)
            sparql_ep.setRequestMethod(POSTDIRECTLY)
            sparql_ep.setQuery(insert_query)
            sparql_ep.query()

            count_query = "SELECT  (COUNT( DISTINCT ?s) as ?nb)  FROM <" + ns_shape + "> WHERE { ?s ?p ?o. }"
            sparql_ep.setQuery(count_query)
            sparql_ep.setReturnFormat(JSON)
            qres = sparql_ep.query().convert()
            print("DATA INSERTED:")
            print(qres)

        count_query = "SELECT  (COUNT( DISTINCT ?s) as ?nb)  FROM <" + ns_class_ids + "> WHERE { ?s ?p ?o. }"
        print(count_query)
        sparql_ep.setQuery(count_query)
        sparql_ep.setReturnFormat(JSON)
        qres = sparql_ep.query().convert()
        nb_triples=int(qres["results"]["bindings"][0]["nb"]["value"])
        print("NB ALREADY ADDED IN TYPE IDS >",nb_triples)
        res = cs.CreateUUIDClassEntities2(type_triples,ns_class_ids, sparql_ep_uri)
        logging.info("END uuid creation process")
    else:
        logging.error("Shape file path not provided")
