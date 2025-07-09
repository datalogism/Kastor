#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 09:28:16 2024

"""
import sys

from rdflib import Graph
import json
from datetime import datetime
from os.path import isfile, join
from argparse import ArgumentParser
import src.rdf_synthax_fct as rs
import pandas as pd
from transformers.safetensors_conversion import previous_pr

import src.triple_shapes as ts
import src.class_signatures as cs
import src.corese_tools as ct
from bs4 import BeautifulSoup # pip install beautifulsoup4

from markdown import markdown
import random
def md_to_text(md):
    html = markdown(md)
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-output", "--output_dir", default=1200)
    parser.add_argument("-ng", "--named_graph_sample", default=None)
    parser.add_argument("-gs", "--generation_strategy", default="KR_same_level")
    args = parser.parse_args()
    if args.shape_file_path and args.output_dir:
        shape = Graph()
        shape.parse(args.shape_file_path)
        sparql_ep = 'http://localhost:8080/sparql'
        size_sample_togen=1000
        dir_out=args.output_dir
        gen_strat=args.generation_strategy
        found_ng=args.named_graph_sample
        new_ng=found_ng+"/synthetic/"+gen_strat


        print("================================ CURRENT SAMPLE :", new_ng)


        #dir_root="/user/home/Desktop/"
        #found_ng="http://ns.inria.fr/kstor/#found_in_abtract"
        default_ng="<urn:x-arq:DefaultGraph>"
        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        prop_focus2=[]
        dict_simply_real={}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)]=p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)


        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT  (COUNT(DISTINCT ?s) as ?nb) FROM <" + found_ng + "> WHERE { ?s ?p ?o }"
        res = ct.get_sparql_dataframe(sparql_ep, query)
        print("BEFORE>", res)
        prop_stats = {}
        for prop in prop_focus:
            nb = cs.get_PropertiesRealised(prop, found_ng, sparql_ep)
            if (int(nb) > 0):
                prop_focus2.append(prop)
                prop_stats[prop] = nb / res["nb"][0]

        class_sign_all = cs.get_All_ClassSignatures(shape, prop_focus2)
        ref_prop='http://dbpedia.org/ontology/alias'
        entities = cs.get_PropertyRandomSample_NG(type_triples, [ref_prop], prop_focus2, found_ng, sparql_ep,
                                                  size_sample=size_sample_togen)

        pattern_count={}
        for uri in entities:
            pattern=[]
            query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <" + found_ng + "> { <" + uri + "> ?p ?o. }"
            res = ct.get_sparql_dataframe(sparql_ep, query)

            for index, row2 in res.iterrows():
                real_prop = row2["p"]
                pattern.append(real_prop)
            c = list(set(pattern))
            c.sort()
            c_tuple = tuple(c)
            if(c_tuple not in pattern_count.keys()):
                pattern_count[c_tuple]=1
            else:
                pattern_count[c_tuple]+=1
        class_sign_freq_dt = []
        list_prop = list(dict_simply_real.keys())
        n = 0
        for pattern in pattern_count.keys():
            print(pattern)
            tempo = ["pattern" + str(n)]
            for prop in list_prop:
                if (prop in str(pattern)):
                    tempo.append(1)
                else:
                    tempo.append(0)
            tempo.append(pattern_count[pattern])
            class_sign_freq_dt.append(tempo)
            n += 1
        colnames_ = ["pattern"] + list_prop + ["nb_real"]
        df = pd.DataFrame(class_sign_freq_dt, columns=colnames_)

        df.to_csv(dir_out + 'RDF_stats_alias_based_' + shape_name + '_sample1X10.csv', encoding='utf-8', index=True)
        print(pattern_count)

        #### RETRIEVE ALREADY CREATED DATA
        selected_couples = []
        query = "PREFIX prov: <http://www.w3.org/ns/prov#>. PREFIX dbo: <http://dbpedia.org/ontology/>  select ?uri_0 ?uri_1 FROM <" + new_ng + "> { ?uri_0 prov:wasDerivedFrom ?uri_1. }"
        res = ct.get_sparql_dataframe(sparql_ep, query)
        for index, row in res.iterrows():
            key = str(row["uri_0"]) + "|" + str(row["uri_1"])
            if(key not in selected_couples):
                selected_couples.append(key)


        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name


        while len(selected_couples) < size_sample_togen:
            ### LOW LEVEL REPLACE

            new_couples=[]
            print("====================>", len(selected_couples))
            if(gen_strat=="KR_low_level"):
                    random_patt = random.choice(list(pattern_count.keys()))
                    smaller_patt=[ k for k in pattern_count.keys() if len(k)< len(random_patt)]
                    accepted_patt=[]
                    for sp in smaller_patt:
                        set_rp=set(random_patt)
                        set_sp=set(sp)
                        if(len(set_sp-set_rp)==0):
                            accepted_patt.append(list(set_sp))
                    if(len(accepted_patt)>0):
                        randomlow_patt = random.choice(accepted_patt)
                        entity_0 = cs.get_ClassSignatureRandomSample_NG(type_triples, list(random_patt), prop_focus2, found_ng,
                                                                        sparql_ep, size_sample=1)
                        entity_1 = cs.get_ClassSignatureRandomSample_NG(type_triples, list(randomlow_patt), prop_focus2, found_ng,
                                                                         sparql_ep, size_sample=1)
                        key = str(entity_1[0]) + "|" + str(entity_0[0])

                        if (key not in selected_couples):
                            selected_couples.append(key)
                            new_couples.append(key)

            elif(gen_strat=="KR_same_level"):

                    class_sign_freq_with_duo = [k for k in pattern_count.keys() if pattern_count[k] > 1]
                    try:
                        random_patt =random.choice(class_sign_freq_with_duo)
                    except:
                        random_patt = None
                    if(random_patt != None):
                        entities = cs.get_ClassSignatureRandomSample_NG(type_triples, list(random_patt), prop_focus2, found_ng,
                                                                        sparql_ep, size_sample=2)
                        key=str(entities[0])+"|"+str(entities[1])

                        if(key not in selected_couples):
                            selected_couples.append(key)
                            new_couples.append(key)

                        key=str(entities[1])+"|"+str(entities[0])

                        if (key not in selected_couples):
                            selected_couples.append(key)
                            new_couples.append(key)



            print("====================>", len(selected_couples))

            for couples_raw in new_couples:
                print(couples_raw)
                couples=couples_raw.split('|')
                print(couples)
                uri_template_0=rs.uncodeurl(couples[0])
                uri_template=rs.cleanEntURL(couples[0])
                uri_new_0=rs.uncodeurl(couples[1])
                uri_new=rs.cleanEntURL(couples[1])

                template_abs = cs.get_abstractMD(uri_template, abstract_ng, sparql_ep)

                query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <" + found_ng + "> { <" + uri_template + "> ?p ?n. ?n rdf:value ?o. }"
                print(query)
                template_graph = ct.get_sparql_dataframe(sparql_ep, query)
                print(template_graph)
                template_graph['length'] = template_graph['o'].str.len()
                template_graph.sort_values('length', ascending=False, inplace=True)
                print("~~~~~~~~~~~~~~")
                template_abs = template_abs["abstract"][0]
                print("ORIG:")
                print(md_to_text(template_abs))

                for index, row2 in template_graph.iterrows():
                    # print(row2)
                    real_prop = row2["p"]

                    if (real_prop in type_prop.keys()):
                        val = str(row2["o"])
                        #print(real_prop,">",val)
                        template_abs=ts.find_in_abstractAndPropTag(template_abs, real_prop, val, type_prop[real_prop])

                        #abstract=ts.find_in_abstractAndMASK(abstract, real_prop, val, type_prop[real_prop])
                print("PATTERN ABS")
                print(template_abs)

                template_abs=md_to_text(template_abs)

                print("uri new >",uri_new)
                query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <" + found_ng + "> { <" + uri_new + "> ?p ?n. ?n rdf:value ?o. }"
                new_graph0 = ct.get_sparql_dataframe(sparql_ep, query)
                new_graph = new_graph0.copy()
                new_graph['length'] = new_graph['o'].str.len()
                new_graph.sort_values('length', ascending=False, inplace=True)
                print("~~~~~~~~~~~~~~")
                print(new_graph)
                new_abs=template_abs
                for index, row2 in new_graph.iterrows():
                    real_prop = row2["p"]
                    if (real_prop in type_prop.keys()):
                        if("dbo:" in type_prop[real_prop]):
                            uri= str(row2["o"])
                            query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?label FROM "+default_ng+" { <" + uri + "> <http://www.w3.org/2000/01/rdf-schema#label>  ?label. }"
                            res_label = ct.get_sparql_dataframe(sparql_ep, query)
                            val=res_label["label"][0]
                        elif("Date"  in real_prop):
                            val = str(row2["o"])
                            val=  datetime.strptime(val,"%Y-%m-%d").strftime('%d %B %Y')
                        else:
                            val = str(row2["o"])
                        if("http://dbpedia.org/resource/" in val or "https://dbpedia.org/resource/" in val):
                            val=val.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","").replace("_"," ")

                        if("$"+real_prop+"$" in new_abs):
                            new_abs=new_abs.replace("$"+real_prop+"$",val)

                print(">>>>>>>>>>>>>")
                print(new_abs)
                print("derived from ",uri_template)
                print("using >",new_graph0 )
                print("xxxxxxxxxxxxx")

                if ('"' in new_abs or "'" in new_abs or "\\" in new_abs):
                    new_abs = new_abs.translate(str.maketrans({"'": r"\'", '"': r'\"', "\\": "\\\\"}))

                ##################################### ABSTRACT AND META INFO
                query = "PREFIX prov: <http://www.w3.org/ns/prov#> PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + new_ng + "> { <" + uri_new + "> prov:wasDerivedFrom <" + uri_template_0 + ">. <" + uri_new_0 + "> <http://www.w3.org/2000/01/rdf-schema#comment>  '" + new_abs + "'.  }}"
                print(query)
                res = ct.sparql_service_update(sparql_ep, query)
                print(res)

