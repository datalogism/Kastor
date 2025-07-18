#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 11:50:12 2024

"""
import random
from argparse import ArgumentParser
from rdflib import Graph
import json

from sympy.codegen.ast import continue_

import src.corese_tools as ct
import sys


############## USEFULL FUCNTIONS

import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.class_signatures as cs
        
import urllib.parse
def uncodeurl(URL):
    if("%" in URL):
        print("HEY")
        return urllib.parse.unquote(URL)
    else:
        return URL


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-output", "--output_dir", default=None)
    parser.add_argument("-ng", "--named_graph_sample", default=None)
    parser.add_argument("-abs", "--abstract_type", default="MD")
    #parser.add_argument("-abs", "--abstract_type", default=None)
    args = parser.parse_args()
    sample_size=0
    print(">>>>>>>>>>>>>>>>>>>>>>>>>> START HERE")
    if args.shape_file_path and args.output_dir and args.named_graph_sample and args.abstract_type:
        shape = Graph()
        shape.parse(args.shape_file_path)
        dir_out=args.output_dir
        sparql_ep = 'http://localhost:8080/sparql'
        #found_ng="http://ns.inria.fr/kstor/#found_in_abtract"
        #found_ng = "http://ns.inria.fr/kstor/#found_in_abtract_md"
        query = 'SELECT distinct ?g {  GRAPH ?g {} }'
        results = ct.get_sparql_dataframe(sparql_ep, query)
        existing_ng = list(results['g'])
        print(results)
        for ng in existing_ng:
            if "http://ns.inria.fr/kstor/samples/" in ng:
                query = 'SELECT ( COUNT(distinct ?s) as ?nb) {  GRAPH <'+ng+'> {?s ?p ?o.} }'
                results = ct.get_sparql_dataframe(sparql_ep, query)
                print(">>>>>>>>>",ng)
                print(results)
            #if "http://ns.inria.fr/kstor/samples/PersonShape_op/abtract_md/" in ng:
                #query = 'DROP GRAPH <' + ng + '>'
                #print("TO DROP")
                #results = ct.get_sparql_dataframe(sparql_ep, query)
                #print(">>>>>>>>>", ng)

               # res = ct.sparql_service_update(sparql_ep, query)
                #print(results)
        #sys.exit()

        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")

        found_ng = "http://ns.inria.fr/kstor/wikichecked/" + shape_name + "/abtract_md"
        sample_ng = args.named_graph_sample
        #sample_ng=args.named_graph_sample
            #"http://ns.inria.fr/kstor/samples/sample_3"

        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real={}
        nb_by_prop={}
        for p in prop_focus:
            nb_by_prop[p]=0
            dict_simply_real[ts.getSimplifiedProp(p)]=p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)

        list_obj_prop = [k for k in type_prop.keys() if "dbo:" in type_prop[k]]

        list_dt_prop = [k for k in type_prop.keys() if "dbo:" not in type_prop[k]]
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name

        SAMPLE=[]
        existing_uri= []

        prop_stats = {}
        for prop in prop_focus:
            nb = cs.get_PropertiesRealised(prop, found_ng, sparql_ep)
            if (int(nb) > 0):
                prop_stats[prop] = nb
            print(">>>>NB: ", prop, " - ", nb)

        sorted_prop = sorted(prop_stats, key=prop_stats.get, reverse=False)
        continue_loop= True
        if (continue_loop):
            for ref_prop in sorted_prop:

                #continue_loop = True
                uri_prop_list=cs.get_SampleEntUrisProp(found_ng,ref_prop,sparql_ep)
                ng_wkcheck="http://ns.inria.fr/kstor/#found_in_abtract"

                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> NEW')
                nb_found=0
                for uri in uri_prop_list:
                    if(continue_loop and nb_found < 100):
                        #print(">>>>>", uri)
                        current_prop_list=set()

                        uri_clean = rs.cleanEntURL(uri)
                        if (uri_clean in existing_uri):
                            print(">>>>>>>>>>>>>>>>>>>> FOUND",ref_prop)
                            nb_found+=1
                        elif (uri_clean not in existing_uri):
                            existing_uri.append(uri_clean)
                            # abs_data=cs.get_abstract(uri, sparql_ep)
                            if (args.abstract_type == "MD"):
                                abs_data = cs.get_abstractMD(uri, abstract_ng, sparql_ep)
                            else:
                                abs_data = cs.get_abstract(uri, sparql_ep)
                            abstract = str(abs_data["abstract"][0])

                            # fng_data=cs.get_FoundNgData(uri,found_ng, sparql_ep)

                            fng_data = cs.get_SampleDataWC(uri, found_ng, sparql_ep)
                            ent_dict2 = []
                            for index, row2 in fng_data.iterrows():

                                real_prop = row2["p"]
                                current_prop_list.add(real_prop)
                                if real_prop in type_prop.keys():
                                    val = str(row2["o"])
                                    val = rs.cleanTxt(val)
                                    if ("dbo:" in type_prop[real_prop]):
                                        val = rs.cleanEntURL(val)
                                    else:
                                        if ('"' in val or "'" in val):
                                            val = val.translate(str.maketrans({"'": r"\'",
                                                                               '"': r'\"'}))

                                        if ("Year" in real_prop and "-" in str(val)):
                                            val = str(val).split("-")[0][0:4]
                                    if ("Year" in real_prop and "-" in str(val)):
                                        val = str(val).split("-")[0][0:4]

                                    temp_new = {"type": type_prop[real_prop], "prop": real_prop, "value": [val]}
                                    ent_dict2.append(temp_new)

                            triples = ts.triplesWithShape(uri_clean, ent_dict2, shape)
                            ent3 = uri_clean.replace("http://dbpedia.org/resource/", "").replace("https://dbpedia.org/resource/",
                                                                                                 "")
                            #if (sample_size < 1000):
                            # not_ok=0
                            # for p in current_prop_list:
                            #     if(nb_by_prop[p]>=1000):
                            #         not_ok+=1

                            continue_current_prop= nb_by_prop[ref_prop] > 1000

                            all_sup_1000=True
                            for ex in nb_by_prop.keys():
                                if(nb_by_prop[ex]<1000):
                                    all_sup_1000=False

                            if( continue_current_prop == False and  len(SAMPLE)<4800 ):
                                print(len(SAMPLE),"-",ref_prop)
                                ("------------------")
                                print(nb_by_prop)
                                for p in current_prop_list:
                                    nb_by_prop[p]+=1
                                sample_size += 1
                                SAMPLE.append({"triples": triples.serialize(format="turtle"), "abstract": abstract, "ent": ent3})
                            if(all_sup_1000 and len(SAMPLE)>4800):
                                continue_loop = False

        ("------------------")
        print(nb_by_prop)
        print("------------------")

        #SAMPLE=SAMPLE[0:12000]
        SAMPLE_rd = SAMPLE.copy()
        random.shuffle(SAMPLE_rd)
        dataset_turtleLight = []
        for row in SAMPLE_rd:
            triples = row["triples"]
            print(triples)
            new = row.copy()
            triples_list1 = rs.simplifyTutle(triples, False, True, True)

            if(len(triples_list1)<0):
                print(triples_list1)
            new["triples"] = uncodeurl(triples_list1)
            print(new["triples"] )

            dataset_turtleLight.append(new)
        ########### HERE VAL=TEST BECAUSE WE NEED A TEST FILE BUT AS WE USE CROSS VALIDATION THIS SET IS
        ### PICKEN FROM TRAIN SET
        # TO DO : DEFINE IN ANOTHER PLACE SAMPLE SIZE
        with open(dir_out + "DS_turtle_train.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd[0:3000], fl)
        with open(dir_out + "DS_turtle_train_sample.json", 'w', encoding='utf-8') as f1:
            json.dump(SAMPLE_rd[0:20], f1)
        with open( dir_out+ "DS_turtle_all_test.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd, fl)
        with open( dir_out+ "DS_turtle_test.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd[3000:3200], fl)
        with open(dir_out + "DS_turtle_val.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd[3200:3400], fl)

        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_all_test.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight, fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_train.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight[0:3000], fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_train_sample.json", 'w', encoding='utf-8') as f1:
            json.dump(dataset_turtleLight[0:20], f1)
        with open( dir_out+ "DS_turtleS_0datatype_1inLine_1facto_test.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight[3000:3200], fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_val.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight[3200:3400], fl)
        print("------------------")
        print(nb_by_prop)
        print("------------------")
