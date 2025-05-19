from argparse import ArgumentParser
import logging
import json
from rdflib import Graph
import src.class_signatures as cs
import src.triple_shapes as ts

import src.corese_tools as ct
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-wd", "--wikidiff_file_path", default="/user/cringwal/home/Desktop/WikiDiff/newArticles.json")
    args = parser.parse_args()

    sparql_ep = 'http://localhost:8080/sparql'
    current_ng= "http://ns.inria.fr/kstor/wikinew_202004/"
   # if args.wikidiff_file_path:
    with open(args.wikidiff_file_path, 'r', encoding='utf-8') as f:
        list_new_art = json.load(f)
        N=len(list_new_art)
        for i in range(len(list_new_art)):
            print(i,"/",N)
            ent=list_new_art[i]
            uri="http://dbpedia.org/resource/"+ent
            query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + current_ng + "> { <" + uri + "> a dbo:Thing }}"
            #print(query)

            res = ct.sparql_service_update(sparql_ep, query)

