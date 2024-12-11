#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 11:50:12 2024

"""
import random
from argparse import ArgumentParser
from rdflib import Graph
import json
import sys


############## USEFULL FUCNTIONS

import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.class_signatures as cs
        



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-output", "--output_dir", default=1200)
    parser.add_argument("-ng", "--named_graph_sample", default=None)
    args = parser.parse_args()

    print(">>>>>>>>>>>>>>>>>>>>>>>>>> START HERE")
    if args.shape_file_path and args.output_dir and args.named_graph_sample:
        shape = Graph()
        shape.parse(args.shape_file_path)
        dir_out=args.output_dir
        sparql_ep = 'http://localhost:8080/sparql'
        found_ng="http://ns.inria.fr/kstor/#found_in_abtract"
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
        SAMPLE=[]
        list_uri=cs.get_SampleEntUris(sample_ng,sparql_ep)
        for uri in list_uri:
            print(">>>>>",uri)

            uri_clean=rs.cleanEntURL(uri)
            abs_data=cs.get_abstract(uri, sparql_ep)
            abstract=str(abs_data["abstract"][0])

            fng_data=cs.get_FoundNgData(uri,found_ng, sparql_ep)
            ent_dict2=[]
            for index, row2 in fng_data.iterrows():

                real_prop=row2["p"]
                val=str(row2["o"])
                val=rs.cleanTxt(val)
                if('"' in val or "'" in val):
                    val = val.translate(str.maketrans({"'":  r"\'",
                              '"': r'\"'}))

                if("Year" in real_prop):
                    val=val[0:4]

                temp_new={"type":type_prop[real_prop],"prop":real_prop,"value":[val]}
                ent_dict2.append(temp_new)


            triples=ts.triplesWithShape(uri_clean,ent_dict2,shape)
            ent3=uri_clean.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")

            SAMPLE.append({"triples":triples.serialize(format="turtle"),"abstract":abstract,"ent":ent3})

        SAMPLE_rd = SAMPLE.copy()
        random.shuffle(SAMPLE_rd)
        dataset_turtleLight = []
        for row in SAMPLE_rd:
            triples = row["triples"]
            new = row.copy()
            triples_list1 = rs.simplifyTutle(triples, False, True, True)
            new["triples"] = triples_list1
            dataset_turtleLight.append(new)
        ########### HERE VAL=TEST BECAUSE WE NEED A TEST FILE BUT AS WE USE CROSS VALIDATION THIS SET IS
        ### PICKEN FROM TRAIN SET
        # TO DO : DEFINE IN ANOTHER PLACE SAMPLE SIZE
        with open(dir_out + "DS_turtle_train.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd[0:1000], fl)
        with open(dir_out + "DS_turtle_train_sample.json", 'w', encoding='utf-8') as f1:
            json.dump(SAMPLE_rd[0:20], f1)
        with open( dir_out+ "DS_turtle_all_test.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd, fl)
        with open( dir_out+ "DS_turtle_test.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd[1000:1200], fl)
        with open(dir_out + "DS_turtle_val.json", 'w', encoding='utf-8') as fl:
            json.dump(SAMPLE_rd[1000:1200], fl)

        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_all_test.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight, fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_train.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight[0:1000], fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_train_sample.json", 'w', encoding='utf-8') as f1:
            json.dump(dataset_turtleLight[0:20], f1)
        with open( dir_out+ "DS_turtleS_0datatype_1inLine_1facto_test.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight[1000:1200], fl)
        with open(dir_out + "DS_turtleS_0datatype_1inLine_1facto_val.json", 'w', encoding='utf-8') as fl:
            json.dump(dataset_turtleLight[1000:1200], fl)