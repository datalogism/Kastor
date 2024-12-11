#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 09:28:16 2024

"""

from rdflib import Graph
import json
from os.path import isfile, join
from argparse import ArgumentParser
import pandas as pd


import src.triple_shapes as ts
import src.class_signatures as cs


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-output", "--output_dir", default=1200)
    parser.add_argument("-ng", "--named_graph_sample", default=None)
    args = parser.parse_args()
    if args.shape_file_path and args.output_dir and args.named_graph_sample:
        shape = Graph()
        shape.parse(args.shape_file_path)
        sparql_ep = 'http://localhost:8080/sparql'

        dir_out=args.output_dir
        found_ng=args.named_graph_sample
        #dir_root="/user/home/Desktop/"
        #found_ng="http://ns.inria.fr/kstor/#found_in_abtract"
        default_ng="<urn:x-arq:DefaultGraph>"
        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real={}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)]=p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)


        class_sign_all=cs.get_All_ClassSignatures(shape,prop_focus)
        stats_file=join(dir_out,"ClassSignatureStats_foundNG.json")
        exist_stats=isfile(stats_file)
    
        class_sign_freq={}
        if (exist_stats):
            print("STATS FILE EXISTS")
            with open(stats_file) as current_file:
                    class_sign_freq = json.load(current_file)
        else:

            found_abs="<"+found_ng+">"
            print("STATS FILE CREATION")
            nb_ent=cs.get_NbEntitiesNG(found_abs,sparql_ep)

            print("ALL entities : ",nb_ent)
            for class_sign in class_sign_all:
                print(class_sign)
                nb_entities=cs.get_ClassSignatureNb_NG(type_triples,list(class_sign),prop_focus,found_abs,sparql_ep)
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
            df.to_csv(dir_out+'RDF_stats_foundInAbs.csv', encoding='utf-8', index=True)


            class_real=[k for k in class_sign_freq.keys() if class_sign_freq[k]["nb_real"]>0]

            #if(sampling_technic=="uniform"):
            proba_classes=[1/len(class_real) for k in class_real if class_sign_freq[k]["nb_real"]>0]

