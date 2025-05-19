#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 10:35:40 2024

"""

from rdflib import Graph
from argparse import ArgumentParser

import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct
import src.class_signatures as cs
import src.abstractExtended as ae
from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
from SPARQLWrapper import get_sparql_dataframe
import sys

def getNbEntToDO2(sparql_ep,search_ng,current_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = "PREFIX dcat: <http://www.w3.org/ns/dcat#> select  (COUNT(DISTINCT ?s) as ?nb)  FROM <" + search_ng + "> WHERE  {   ?s dcat:resource_identifier  ?uid. FILTER  EXISTS { GRAPH  <http://ns.inria.fr/kstor/wikinew_202004/> { ?s ?pi ?oi } }. FILTER NOT EXISTS { GRAPH  <" + current_ng + "> { ?s ?p ?o }  } } "
    print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)

def get_SubjectsToRetrieve(sparql_ep,search_ng,current_ng,limit):

    sparql = SPARQLWrapper(sparql_ep)
    query = "PREFIX dcat: <http://www.w3.org/ns/dcat#> select  ?s FROM <" + search_ng + "> WHERE  {   ?s dcat:resource_identifier  ?uid. FILTER NOT EXISTS { GRAPH  <" + current_ng + "> { ?s ?p ?o }  } } ORDER BY ASC(?uid) LIMIT " + str(limit)
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects

def get_SubjectsToRetrieveWithID2(sparql_ep,search_ng,current_ng,limit):

    sparql = SPARQLWrapper(sparql_ep)
    query = "PREFIX dcat: <http://www.w3.org/ns/dcat#> select  ?s ?id FROM <" + search_ng + "> WHERE  {   ?s dcat:resource_identifier  ?uid. ?s <http://dbpedia.org/ontology/wikiPageRevisionID> ?id. FILTER  EXISTS { GRAPH  <http://ns.inria.fr/kstor/wikinew_202004/> { ?s ?pi ?oi } }. FILTER NOT EXISTS { GRAPH  <" + current_ng + "> { ?s ?p ?o }  } } ORDER BY ASC(?uid) LIMIT " + str(limit)
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [{"subj":row["s"]["value"],"id":row["id"]["value"]} for row in qres["results"]["bindings"]]
    return subjects


def get_SubjectsToRetrieveWithIDAndIdNS2(sparql_ep, search_ng, id_ng, current_ng, limit):
    sparql = SPARQLWrapper(sparql_ep)

    query = '''PREFIX dcat: <http://www.w3.org/ns/dcat#> select  ?s ?id 
    FROM <''' + search_ng + '''> WHERE  { 
        GRAPH <''' + id_ng + '''> { ?s dcat:resource_identifier  ?uid }.
       ?s <http://dbpedia.org/ontology/wikiPageRevisionID> ?id.
          FILTER  EXISTS { GRAPH  <http://ns.inria.fr/kstor/wikinew_202004/> { ?s ?pi ?oi } }. FILTER NOT EXISTS { GRAPH  <''' + current_ng + '''> { ?s ?p ?o }  }

       } ORDER BY ASC(?uid) LIMIT ''' + str(limit)

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [{"subj": row["s"]["value"], "id": row["id"]["value"]} for row in qres["results"]["bindings"]]
    return subjects


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    args = parser.parse_args()

    wikipedia_agent="(https://datalogism.github.io/; celian.ringwald@inria.fr) Inria"
    sparql_ep = 'http://localhost:8080/sparql'
    search_ng="urn:x-arq:DefaultGraph"

    if args.shape_file_path:
        print("shape load")
        shape = Graph()
        shape.parse(args.shape_file_path)
        type_triples = ts.getShapeType(shape)
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        ns_class_ids = "http://ns.inria.fr/kstor/class_randoms_id/" + type_triples_name
        current_ng="http://ns.inria.fr/kstor/wiki_md/"+type_triples_name


        nb_loop=0
        count_ent_checked=0
        offset=0
        limit=10000
        done=[]
        to_do=getNbEntToDO2(sparql_ep,ns_class_ids,current_ng)
        print(">>>>>>>>>>>>>>>>>>>>> NB ENT TO GET ABSTRACT",to_do)
        while to_do>0:
           print(">>>>>>>>>>>>>>>>>>>>>LOOP :" ,nb_loop,">",count_ent_checked,"/",to_do)
           sample=  get_SubjectsToRetrieveWithIDAndIdNS2(sparql_ep,search_ng,ns_class_ids,current_ng,limit)

           for node in sample:
                uri=node["subj"]
                wiki_id= node["id"]
                entity_splm=uri.replace('http://dbpedia.org/resource/','').replace('https://dbpedia.org/resource/','')
                print("before")

                md_entity = ae.getAbstractMD2(entity_splm,wiki_id, wikipedia_agent)
                print(md_entity)
                #md_entity=ae.getAbstractMD(entity_splm,wikipedia_agent)
                print(uri)
                if ('"' in md_entity or "'" in md_entity or "\\" in md_entity):
                    md_entity = md_entity.translate(str.maketrans({"'": r"\'", '"': r'\"',"\\" : "\\\\"}))

                query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + current_ng + "> { <" + uri + "> <http://www.w3.org/2000/01/rdf-schema#comment>  '" + md_entity + "' }}"
                try:
                    res = ct.sparql_service_update(sparql_ep, query)
                    count_ent_checked+=1
                except:
                    print("============== PB WITH: ")
                    print(query)
                    print("==============")
                print("after")
           to_do=getNbEntToDO2(sparql_ep,search_ng,current_ng)
           offset+=limit
           nb_loop+=1
