#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 09:28:16 2024

"""
import sys

from rdflib import Graph
import json
from os.path import isfile, join
from argparse import ArgumentParser
import pandas as pd


import src.triple_shapes as ts
import src.class_signatures as cs
import src.corese_tools as ct
import sys

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-output", "--output_dir", default=1200)
    parser.add_argument("-ng", "--named_graph_sample", default=None)
    args = parser.parse_args()
    if args.shape_file_path and args.output_dir:
        dir_out=args.output_dir
        shape = Graph()
        shape.parse(args.shape_file_path)
        sparql_ep = 'http://localhost:8080/sparql'

        found_ng=args.named_graph_sample

        default_ng="<urn:x-arq:DefaultGraph>"

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
        prop_stats={}
        for prop in prop_focus:
            nb=cs.get_PropertiesRealised(prop,found_ng,sparql_ep)
            if(int(nb)>0):
                prop_focus2.append(prop)
                prop_stats[prop]=nb/res["nb"][0]
            print(">>>>NB: ",prop," - ",nb)
        print("PROP FOCUS>",prop_focus2)
        stats_file = join(dir_out, shape_name + "PropStats_foundNG.json")
        exist_stats = isfile(stats_file)

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(prop_stats, f)

        class_sign_all=cs.get_All_ClassSignatures(shape,prop_focus2)
        stats_file=join(dir_out,shape_name+"ClassSignatureStats_foundx10.json")
        exist_stats=isfile(stats_file)
        exist_stats=False
        class_sign_freq={}
        if (exist_stats==True):
            print("STATS FILE EXISTS")
            with open(stats_file) as current_file:
                    class_sign_freq = json.load(current_file)
        else:

            found_abs=found_ng
            print("STATS FILE CREATION")
            nb_ent=cs.get_NbEntitiesNG(found_abs,sparql_ep)

            print("ALL entities : ",nb_ent)
            for class_sign in class_sign_all:
                print(class_sign)
                nb_entities=cs.get_ClassSignatureNb_NG(type_triples,list(class_sign),prop_focus2,found_abs,sparql_ep)
                print(nb_entities)
                tempo={"nb_prop":len(class_sign),"nb_real":nb_entities,"freq":nb_entities/nb_ent}
                c=list(class_sign)
                c.sort()
                c_tuple=tuple(c)
                class_sign_freq[str(c_tuple)]=tempo
            with open(stats_file, 'w', encoding='utf-8')  as f:
                 json.dump(class_sign_freq, f)
    
            class_sign_freq_dt=[]
            list_prop=list(dict_simply_real.keys())
            n=0
            for pattern in class_sign_freq.keys():
                tempo=["pattern"+str(n)]
                for prop in list_prop:
                    if(dict_simply_real[prop] in pattern):
                            tempo.append(1)
                    else:
                        tempo.append(0)
                tempo.append(class_sign_freq[pattern]["nb_real"])
                class_sign_freq_dt.append(tempo)
                n+=1
            colnames_=["pattern"]+list_prop+["nb_real"]
            df=pd.DataFrame(class_sign_freq_dt, columns=colnames_)

            df.to_csv(dir_out+'RDF_stats_sample_'+shape_name+'_sample1x10.csv', encoding='utf-8', index=True)

            print(dir_out+'RDF_stats_sample_')


