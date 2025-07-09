#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 11:50:12 2024

"""
import random
from argparse import ArgumentParser
from rdflib import Graph
import json
import src.corese_tools as ct
import sys


############## USEFULL FUCNTIONS

import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.class_signatures as cs
from sklearn.model_selection import StratifiedShuffleSplit
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

        sample_S=12000
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

        sample_ng=args.named_graph_sample
            #"http://ns.inria.fr/kstor/samples/sample_3"

        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real={}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)]=p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)

        list_obj_prop = [k for k in type_prop.keys() if "dbo:" in type_prop[k]]

        list_dt_prop = [k for k in type_prop.keys() if "dbo:" not in type_prop[k]]
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name

        SAMPLE=[]
        prop_stats={}
        patt_set_stat={}
        existing_uri= []
        #['United_States', 'Arem-arem', 'Bacon_Explosion', 'BLT', 'Indonesia', 'Tomato', 'Amatriciana_sauce', 'Italy', 'Bacon_sandwich', 'Dessert', 'Arrabbiata_sauce', 'Baked_Alaska', 'Bionico', 'Mexico', 'Celery']
        list_uri=cs.get_SampleEntUris(sample_ng,sparql_ep)
        print("xxxxxxxxxxxxxxxx",len(list_uri))
        for uri in list_uri:
            print(">>>>>",uri)

            uri_clean=rs.cleanEntURL(uri)
            if(uri_clean.replace("http://dbpedia.org/resource/","") in existing_uri):
                print(">>>>>>>>>>>>>>>>>>>> FOUND")
            elif(uri_clean not in existing_uri):
                #abs_data=cs.get_abstract(uri, sparql_ep)
                if(args.abstract_type=="MD"):
                    abs_data=cs.get_abstractMD(uri,abstract_ng, sparql_ep)
                else:
                    abs_data=cs.get_abstract(uri, sparql_ep)
                abstract=str(abs_data["abstract"][0])

                #fng_data=cs.get_FoundNgData(uri,found_ng, sparql_ep)

                fng_data=cs.get_SampleData(uri,sample_ng, sparql_ep)
                ent_dict2=[]
                for index, row2 in fng_data.iterrows():

                    real_prop=row2["p"]
                    if real_prop in type_prop.keys():
                        val=str(row2["o"])
                        val=rs.cleanTxt(val)
                        if ("dbo:" in type_prop[real_prop]):
                            val = rs.cleanEntURL(val)
                        else:
                                if('"' in val or "'" in val):
                                    val = val.translate(str.maketrans({"'":  r"\'",
                                              '"': r'\"'}))

                                if ("Year" in real_prop and "-" in str(val)):
                                    val = str(val).split("-")[0][0:4]
                        if("Year" in real_prop and "-" in str(val)):
                            val=str(val).split("-")[0][0:4]

                        temp_new={"type":type_prop[real_prop],"prop":real_prop,"value":[val]}
                        ent_dict2.append(temp_new)

                print(uri_clean)
                triples=ts.triplesWithShape(uri_clean,ent_dict2,shape)
                patt_set=[]
                for row in ent_dict2:
                    if(row["prop"] not in patt_set):
                        patt_set.append(row["prop"])
                    if(row["prop"] not in prop_stats.keys()):
                        prop_stats[row["prop"]]=0
                    else:
                        prop_stats[row["prop"]]+=1
                patt_set.sort()
                if(str(patt_set) not in patt_set_stat.keys()):
                    patt_set_stat[str(patt_set)]=0
                else:
                    patt_set_stat[str(patt_set)]+=1



                ent3=uri_clean.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")
                if(sample_size<sample_S):
                    sample_size+=1
                    SAMPLE.append({"triples":triples.serialize(format="turtle"),"abstract":abstract,"ent":ent3,"pattern":str(patt_set),"class":0})
        print("HEYYY")
        print(prop_stats)
        print("-----------")
        print(sample_size)
        equiv_distrib=sample_size/len(prop_stats.keys())
        avg=sum([ prop_stats[k] for k in prop_stats.keys() ])/len(list(prop_stats.keys()))
        list_under_repres=[ k for k in prop_stats.keys() if prop_stats[k]<avg]
        #list_under_repres = [k for k in prop_stats.keys()]

        print(list_under_repres)
        class_count={"NONE":0}
        class_idx={"NONE":0}
        for row in SAMPLE:
            Found=[]
            for idx in range(len(list_under_repres)):
                under_rep=list_under_repres[idx]
                if under_rep in row["pattern"]:
                    Found.append(under_rep)
            if(len(Found)==1):
                    if(Found[0] not in class_count.keys()):
                        class_count[Found[0]]=1
                        idx=len(class_idx.keys())+1
                        class_idx[Found[0]]=idx
                    else:
                        idx = class_idx[Found[0]]
                        class_count[Found[0]]+=1
                    row["class"]=idx
            elif(len(Found)>1):
                added=False
                for f in Found:
                    if(f not in class_count.keys()):
                        class_count[f] = 1
                        idx=len(class_idx.keys())+1
                        class_idx[f]=idx
                        row["class"]=idx
                        added=True
                    break
                if added==False:
                    sortedDictclass = sorted(class_count)
                    for valprop in sortedDictclass:
                        if valprop in Found:
                            if (valprop not in class_count.keys()):
                                class_count[valprop] = 1
                                idx = len(class_idx.keys()) + 1
                                class_idx[valprop] = idx
                                added = True
                            else:
                                idx = class_idx[valprop]
                                class_count[valprop] += 1
                            row["class"] = idx
                            break
            else:
                class_count["NONE"]+=1

        print("###############")
        print(class_count)
        print(class_idx)
        SAMPLE=SAMPLE[0:sample_S]
        SAMPLE_rd = SAMPLE.copy()
        dataset_turtleLight = []
        for row in SAMPLE_rd:
            triples = row["triples"]
            #print(triples)
            new = row.copy()
            triples_list1 = rs.simplifyTutle(triples, False, True, True)

           # if(len(triples_list1)<0):
            #    print(triples_list1)
            new["triples"] = uncodeurl(triples_list1)
           # print(new["triples"] )

            dataset_turtleLight.append(new)
       # print(len(dataset_turtleLight))
        test_size=(sample_S-(sample_S/1.2))/sample_S
        sss = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=0)
        y=[row["class"] for row in SAMPLE_rd]
        dataset_turtleLight_eval=[]
        dataset_turtleLight_train=[]
        dataset_turtle_eval=[]
        dataset_turtle_train=[]
        for i, (train_index, test_index) in enumerate(sss.split(SAMPLE_rd, y)):
            for idx in train_index:
                dataset_turtleLight_train.append(dataset_turtleLight[idx])
                dataset_turtle_train.append(SAMPLE_rd[idx])

            for idx in test_index:
                dataset_turtleLight_eval.append(dataset_turtleLight[idx])
                dataset_turtle_eval.append(SAMPLE_rd[idx])
        ########### HERE VAL=TEST BECAUSE WE NEED A TEST FILE BUT AS WE USE CROSS VALIDATION THIS SET IS
        ### PICKEN FROM TRAIN SET
        # TO DO : DEFINE IN ANOTHER PLACE SAMPLE SIZE
        class_count_2={}
        for k in class_idx.keys():
            class_count_2[class_idx[k]]=class_count[k]
        with open(dir_out + "class_idx.json", 'w', encoding='utf-8') as f1:
            json.dump(class_idx, f1)
        with open(dir_out + "class_count.json", 'w', encoding='utf-8') as f1:
            json.dump(class_count_2, f1)
        with open(dir_out + "DS_turtle_train.json", 'w', encoding='utf-8') as f1:
            json.dump(dataset_turtle_train, f1)
        with open(dir_out + "DS_turtle_val.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtle_eval, fl)

        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_train.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight_train, fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_val.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight_eval, fl)
