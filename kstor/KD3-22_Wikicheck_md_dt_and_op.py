#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KD3-22_Wikicheck_md_dt_and_op.py

This module provides functions to analyze and process RDF named graphs, specifically focusing on
entities that need processing based on their presence in different named graphs and their properties.

Key functionalities:
- Count entities that need processing
- Retrieve subjects for processing
- Get statistics about named graphs
- Process person entities with specific properties
"""

from rdflib import Graph
from argparse import ArgumentParser

# Import local modules
import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct
import src.class_signatures as cs
import sys
from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper

#### NEED TO BE MORE GENERAL HERE LIMITED TO INFERENCES
def getNbEntToDO(sparql_ep, target_ng, found_ng, abstract_ng):
    """
    Counts the number of entities in the target named graph that need to be processed.
    An entity needs processing if:
    1. It exists in the target named graph but not in the 'found' named graph
    2. It has a non-empty abstract in the abstract named graph
    
    Args:
        sparql_ep (str): SPARQL endpoint URL
        target_ng (str): Target named graph URI
        found_ng (str): Named graph URI where already processed entities are stored
        abstract_ng (str): Named graph URI containing entity abstracts
        
    Returns:
        int: Number of entities that need to be processed
    """
    sparql = SPARQLWrapper(sparql_ep)
    # Query to find entities in target graph that aren't in found graph but have abstracts
    query = """
    SELECT (COUNT(DISTINCT ?s) as ?nb) 
    FROM <{target_ng}> 
    WHERE {  
        ?s ?p ?o .
        FILTER NOT EXISTS { 
            GRAPH <{found_ng}> { ?s ?p ?o } 
        } . 
        FILTER EXISTS { 
            GRAPH <{abstract_ng}> { 
                ?s ?p2 ?o2. 
                FILTER(?o2 != '') 
            } 
        }
    }""".format(target_ng=target_ng, found_ng=found_ng, abstract_ng=abstract_ng)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)
def getNbEntToDO2(sparql_ep,found_ng,abstract_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = '''select  (COUNT(DISTINCT ?s) as ?nb)  FROM <'''+abstract_ng+'''> WHERE  {
        ?s ?p2 ?o. FILTER(?o != '' ).
       FILTER NOT EXISTS { 
       GRAPH  <'''+found_ng+'''> { ?s ?p ?o } 
        }
          }'''

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)

#### NEED TO BE MORE GENERAL HERE LIMITED TO INFERENCES
def get_SubjectsToRetrieve(sparql_ep,target_ng,found_ng,abstract_ng,limit,offset):
    sparql = SPARQLWrapper(sparql_ep)
    query = "select DISTINCT ?s FROM <"+target_ng+"> WHERE  { ?s ?p ?o. FILTER NOT EXISTS { GRAPH  <"+found_ng+"> { ?s ?p ?o }  } . FILTER EXISTS { GRAPH  <"+abstract_ng+"> { ?s ?p2 ?o2. FILTER(?o2 != '' ). } }. } ORDER BY DESC(?s) LIMIT " + str( limit) +" OFFSET "+str(offset)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects

def get_SubjectsToRetrieve2(sparql_ep,target_ng,found_ng,abstract_ng,limit,offset):
    sparql = SPARQLWrapper(sparql_ep)
    query = '''select  DISTINCT ?s  FROM <''' + abstract_ng + '''> WHERE  {
          ?s ?p2 ?o. FILTER(?o != '' ).
         FILTER NOT EXISTS { 
         GRAPH  <''' + found_ng + '''> { ?s ?p ?o } 
          }
            } ORDER BY DESC(?s) LIMIT ''' + str( limit) +''' OFFSET '''+str(offset)
    #query = "select DISTINCT ?s FROM <"+target_ng+"> WHERE  { ?s ?p ?o. FILTER NOT EXISTS { GRAPH  <"+found_ng+"> { ?s ?p ?o }  } . FILTER EXISTS { GRAPH  <"+abstract_ng+"> { ?s ?p2 ?o2. FILTER(?o2 != '' ). } }. } ORDER BY DESC(?s) LIMIT " + str( limit) +" OFFSET "+str(offset)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects

def get_SubjectsToRetrieve3(sparql_ep,target_ng,found_ng,abstract_ng,limit,offset):
    sparql = SPARQLWrapper(sparql_ep)
    query = '''select  DISTINCT ?s  FROM <''' + abstract_ng + '''> WHERE  {
          ?s ?p2 ?o. FILTER(?o != '' ).
            } ORDER BY DESC(?s) LIMIT ''' + str( limit) +''' OFFSET '''+str(offset)
    #query = "select DISTINCT ?s FROM <"+target_ng+"> WHERE  { ?s ?p ?o. FILTER NOT EXISTS { GRAPH  <"+found_ng+"> { ?s ?p ?o }  } . FILTER EXISTS { GRAPH  <"+abstract_ng+"> { ?s ?p2 ?o2. FILTER(?o2 != '' ). } }. } ORDER BY DESC(?s) LIMIT " + str( limit) +" OFFSET "+str(offset)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects
def get_NBentInNG(sparql_ep,new_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = "select  (COUNT(DISTINCT ?s) as ?nb)  FROM <"+new_ng+"> WHERE  {   ?s ?p ?o }"

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)

def get_NBPersoInNG(sparql_ep,new_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select  (COUNT(DISTINCT ?s) as ?nb)  FROM <"+new_ng+"> WHERE  {   ?s ?p ?o. ?s a dbo:Person. }"

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)

def get_NBPersoInNG2(sparql_ep, new_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#>  select  (COUNT(DISTINCT ?s) as ?nb)  FROM <" + new_ng + "> WHERE  {   ?s dcat:resource_identifier  ?uid.  ?s a dbo:Person. }"

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)


import sys
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default="/user/cringwal/home/PycharmProjects/Kastor/shapes/PersonShape_op.ttl")
    parser.add_argument("-ng", "--searchspace_namedgraph", default="http://ns.inria.fr/kstor/#inferences")
    args = parser.parse_args()

    # to_do=getNbEntToDO(sparql_ep,search_ng,current_ng)
    if args.shape_file_path and args.searchspace_namedgraph:
        shape = Graph()
        shape.parse(args.shape_file_path)
        sparql_ep = 'http://localhost:8080/sparql'
        search_ng=args.searchspace_namedgraph
        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        default_graph="urn:x-arq:DefaultGraph"
        inf_graph="http://ns.inria.fr/kstor/inferences/" + shape_name
        #search_space=[default_graph ]
        search_space = [inf_graph,default_graph]
        #search_space = [default_graph]
        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        found_ng = "http://ns.inria.fr/kstor/wikichecked/" + shape_name + "/abtract_md"
        #print("DELETE")
        #query_delete = "DROP GRAPH <" + found_ng+">"
        #res = ct.sparql_service_update(sparql_ep, query_delete)

        type_triples = ts.getShapeType(shape)
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        ns_class_ids = "http://ns.inria.fr/kstor/class_randoms_id/" + type_triples_name
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name
        #abstract_ng = "http://ns.inria.fr/kstor/wiki_md/Person"

        # found_ng_0= "http://ns.inria.fr/kstor/#found_in_abtract"
        # abstract_ng="http://ns.inria.fr/kstor/#wiki_md_corrected"
        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real = {}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)] = p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)
        clean = False
        nb_in_found_ng = get_NBentInNG(sparql_ep, found_ng)
        print(">>>>>>>>>>nb_in_found_ng:", nb_in_found_ng)
        nb_in_abstract_ng = get_NBentInNG(sparql_ep, abstract_ng)
        print(">>>>>>>>>>nb_in_abstract_ng:", nb_in_abstract_ng)
        print("INSERT IN >",found_ng)
        for search_ng in search_space:

            print("===============================CURRENT SEARCH NG>",search_ng)
            nb_entities=getNbEntToDO2(sparql_ep,found_ng,abstract_ng)
            size_sample=nb_entities

            nb_loop=0
            count_ent_checked=0
            offset=0
            limit=10000
            done=[]
            to_do=nb_entities
            sample = [0]


            while len(sample)!=0:
                print(">>>>>>>>>>>>>>>>>>>>>LOOP :" ,nb_loop,">",count_ent_checked,"/",nb_entities)

                sample= get_SubjectsToRetrieve3(sparql_ep,search_ng,found_ng,abstract_ng,limit,offset)
                print(sample)

                for uri in sample:

                    uri = rs.uncodeurl(uri)
                    print(uri)
                    done.append(uri)
                    count_ent_checked+=1
                    data_sbj=None
################################ A DECOMM
                  #  if("inference" in search_ng):
                   #     print("ICI")
                        #cs.get_NamedGraphData(row["s"], search_ng, type_triples, prop_focus, sparql_ep)
                    #    data_sbj=cs.get_NamedGraphData(uri,search_ng,prop_focus,sparql_ep).to_dict('dict')
                    #else:
                    #if (search_ng == default_graph):
                     #   print(uri)
                      #  print("HEY")
                    data_sbj = cs.get_NamedGraphDataRangeOk(uri, search_ng, type_prop, sparql_ep).to_dict('dict')
                    print(data_sbj)
                    if(data_sbj):
                        abs_=cs.get_abstract_ng(uri,abstract_ng,sparql_ep)
                        if (len(abs_) > 0):
                            #print(uri)
                            abstract = abs_["abstract"][0]
                            nb_found=0
                            for prop in data_sbj.keys():
                                values=list(set(data_sbj[prop].values()))
                                #print(values)
                                for val in values:
                                    current_prop=dict_simply_real[prop]
                                    #print(current_prop)
                                    #if("Year" in prop):
                                     #   val=str(val).split("-")[0]
                                    if ("Year" in prop and "-" in str(val)):
                                        print("DATE")
                                        val = str(val).split("-")[0][0:4]
                                    if str(val) != "nan" and str(val) != "NaN" and str(val) != "":

                                        val = rs.cleanTxt(str(val))
                                        found = ts.find_in_abstractWithObj(abstract, current_prop, val, type_prop[current_prop])

                                        if(found):

                                            print(">>>>>>>>>>>>>>>>>>>>>>>>>FOUND")
                                            nb_found+=1
                                            #print("====")
                                            #print(abstract)
                                            #print("====")
                                            #print("-------------")
                                            #print("val>", val)
                                            #print(found)
                                            temp_new = {"ent_uri": uri, "type": type_prop[current_prop], "prop": current_prop,
                                                        "value": [val]}
                                            if ('"' in val or "'" in val):
                                                val = val.translate(str.maketrans({"'": r"\'", '"': r'\"'}))
                                            query=""
                                            if("dbo:" not in type_prop[current_prop]):
                                                query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + found_ng + "> { <" + uri + "> <" + current_prop + ">  '" + val + "'^^" + \
                                                        type_prop[current_prop] + " }}"
                                            else:
                                                query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + found_ng + "> { <" + uri + "> <" + current_prop + ">  <" + val + ">  }}"
                                            print(query)
                                            res = ct.sparql_service_update(sparql_ep, query)
                                            print(res)
                            if nb_found>0:
                                print("-",uri,">",nb_found)
                                #print(data_sbj)
                    else:
                        print("PRB WITH SUBJ")
                #to_do = getNbEntToDO(sparql_ep, search_ng, found_ng, abstract_ng)
                nb_new=get_NBentInNG(sparql_ep,abstract_ng)
                #print(">>>>>>>>>>>>>>> TODO ?",to_do)
                print(">>>>>>>>>>>>>>> nb_new ?",nb_new)
                offset+=limit
                nb_loop+=1
