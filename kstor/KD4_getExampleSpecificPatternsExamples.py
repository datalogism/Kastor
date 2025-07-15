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
from transformers.safetensors_conversion import previous_pr

import src.triple_shapes as ts
import src.class_signatures as cs
import src.corese_tools as ct
from bs4 import BeautifulSoup # pip install beautifulsoup4

from markdown import markdown

def md_to_text(md):
    html = markdown(md)
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-output", "--output_dir", default=1200)
    parser.add_argument("-ng", "--named_graph_sample", default=None)
    args = parser.parse_args()
    if args.shape_file_path and args.output_dir:
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
        class_sign_to_explore=[]
        for class_k in class_sign_all:
            if(ref_prop in class_k):
                c = list(class_k)
                c.sort()
                c_tuple = tuple(c)
                class_sign_to_explore.append(c_tuple)
        class_sign_to_explore=list(set(class_sign_to_explore))

        class_sign_freq={}
        print(class_sign_to_explore)
        for class_sign in class_sign_to_explore:
            print(class_sign)
            nb_entities = cs.get_ClassSignatureNb_NG(type_triples, list(class_sign), prop_focus2, found_ng, sparql_ep)
            print(nb_entities)
            tempo =  nb_entities
            c = list(class_sign)
            c.sort()
            c_tuple = tuple(c)
            class_sign_freq[str(c_tuple)] = tempo
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(class_sign_freq)
        class_sign_freq_dt = []
        list_prop = list(dict_simply_real.keys())
        n = 0
        for pattern in class_sign_freq.keys():
            tempo = ["pattern" + str(n)]
            for prop in list_prop:
                if (prop in pattern):
                    tempo.append(1)
                else:
                    tempo.append(0)
            tempo.append(class_sign_freq[pattern])
            class_sign_freq_dt.append(tempo)
            n += 1
        colnames_ = ["pattern"] + list_prop + ["nb_real"]
        df = pd.DataFrame(class_sign_freq_dt, columns=colnames_)

        df.to_csv(dir_out + 'RDF_stats_alias_based_' + shape_name + '_sample1X10.csv', encoding='utf-8', index=True)

        sys.exit()

        class_sign=('http://www.w3.org/2000/01/rdf-schema#label', 'http://dbpedia.org/ontology/birthDate',
         'http://dbpedia.org/ontology/birthYear', 'http://dbpedia.org/ontology/alias',
         'http://dbpedia.org/ontology/birthName')

        found_abs = found_ng
        entities = cs.get_ClassSignatureRandomSample_NG(type_triples, list(class_sign), prop_focus2, found_abs, sparql_ep,size_sample=10)

        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name

        previous_abs=None
        for uri in entities:
            print(uri)
            abs_data = cs.get_abstractMD(uri, abstract_ng, sparql_ep)
            query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <" + found_ng + "> { <" + uri + "> ?p ?o. }"
            res = ct.get_sparql_dataframe(sparql_ep, query)

            print(res)
            res['length'] = res['o'].str.len()
            res.sort_values('length', ascending=False, inplace=True)
            print("~~~~~~~~~~~~~~")
            print(res)
            abstract = abs_data["abstract"][0]
            print("ORIG:")
            print(md_to_text(abstract))
            for index, row2 in res.iterrows():
                # print(row2)
                real_prop = row2["p"]

                if (real_prop in type_prop.keys()):
                    val = str(row2["o"])
                    #print(real_prop,">",val)
                    abstract=ts.find_in_abstractAndPropTag(abstract, real_prop, val, type_prop[real_prop])

                    #abstract=ts.find_in_abstractAndMASK(abstract, real_prop, val, type_prop[real_prop])

            print(abstract)
            abstract=md_to_text(abstract)
            print("xxxxxxxxxxxxx")
            print(abstract)
            if previous_abs:
                for index, row2 in res.iterrows():
                    # print(row2)
                    real_prop = row2["p"]

                    if (real_prop in type_prop.keys()):
                        val = str(row2["o"])

                        if("$"+real_prop+"$" in previous_abs):
                            previous_abs=previous_abs.replace("$"+real_prop+"$",val)
            print(">>>>>>>>>>>>>")
            print(previous_abs)
            print("xxxxxxxxxxxxx")
            previous_abs=abstract