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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-ng", "--searchspace_namedgraph", default="http://ns.inria.fr/kstor/#dates_inferenced")
    args = parser.parse_args()

    if args.shape_file_path and args.searchspace_namedgraph:
        shape = Graph()
        shape.parse(args.shape_file_path)

        sparql_ep = 'http://localhost:8080/sparql'
        search_ng=args.searchspace_namedgraph
        found_ng="http://ns.inria.fr/kstor/#found_in_abtract"

        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real={}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)]=p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)
        clean = False

        if clean:
            query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT  (COUNT(DISTINCT ?s) as ?nb) FROM <" + found_ng + "> WHERE { ?s ?p ?o }"
            res = ct.get_sparql_dataframe(sparql_ep, query)
            print("BEFORE>", res)
            query = "PREFIX ks: <http://ns.inria.fr/kstor/#> DROP GRAPH " + found_ng
            res = ct.sparql_service_update(sparql_ep, query)
            query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT  (COUNT(DISTINCT ?s) as ?nb) FROM <" + found_ng + "> WHERE { ?s ?p ?o }"
            res = ct.get_sparql_dataframe(sparql_ep, query)
            print("AFTER>", res)

        nb_entities=cs.get_NbEntitiesNG(search_ng,sparql_ep)
        size_sample=nb_entities
        nb_loop=0
        count_ent_checked=0
        offset=0
        limit=100
        done=[]
        to_do=cs.get_NbEntitiesNGToDo(search_ng,found_ng,sparql_ep)

        while count_ent_checked!=to_do:
            print(">>>>>>>>>>>>>>>>>>>>>LOOP :" ,nb_loop,">",count_ent_checked,"/",to_do)
            sample=  cs.get_sampleNG_to_update(search_ng,found_ng,sparql_ep,limit, offset)

            for index, row in sample.iterrows():
               # dates=cs.get_NamedGraphData(row["s"],search_ng,type_triples, prop_focus,sparql_ep)
                #print(dates)
                #print(row)
                uri=rs.cleanEntURL(row["s"])
                if uri not in done :
                    count_ent_checked+=1
                    done.append(uri)
                #print(row)
                abs_=cs.get_abstract(row["s"],sparql_ep)
                if(len(abs_)>0):
                    abstract=abs_["abstract"][0]
                    current_prop=row["p"]
                    val=str(row["o"])

                    if val != "nan" and val!= "NaN" and val!="":
                        val=rs.cleanTxt(val)
                    if  val!="":
                        val=rs.cleanTxt(val)


                    found=ts.find_in_abstract(abstract,current_prop,val,type_prop[current_prop])
                    if(found):
                        #print(found)
                        temp_new={"ent_uri":uri,"type":type_prop[current_prop],"prop":current_prop,"value":[val]}

                        #CAN ALSO EVAL TRIPLET CRITIC AND NLI HERE
                        #to_eval={"ent_uri":uri_base,"type":type_prop[real_prop],"prop":real_prop,"value":val,"abstract":abstract}
                        #test=nli.getTripletCritic_proba(to_eval)
                        if('"' in val or "'" in val):
                            val = val.translate(str.maketrans({"'":  r"\'",'"': r'\"'}))
                        query="PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <"+found_ng+"> { <"+uri+"> <"+current_prop+">  '"+val+"'^^"+type_prop[current_prop]+" }}"

                        res=ct.sparql_service_update(sparql_ep,query)

            to_do=cs.get_NbEntitiesNGToDo(search_ng,found_ng,sparql_ep)
            offset+=limit
            nb_loop+=1
