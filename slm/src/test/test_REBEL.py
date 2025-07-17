#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 13:27:07 2025

@author: cringwal
"""

import json

from sklearn.model_selection import KFold, StratifiedKFold

from rdflib import Graph
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from transformers import pipeline
import json
import datefinder
import pandas as pd
import sys
sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/slm/src/')

import score_fct as scr_fct
import score as scr
import urllib.parse
import os

def uncodeurl(URL):
    if("%" in URL):
        return urllib.parse.unquote(URL)
    else:
        return URL
def getShapeType(shacl_g):
    get_types = """
        SELECT DISTINCT ?target_class
        WHERE {
            ?a sh:targetClass ?target_class
        }"""
    qres = shacl_g.query(get_types)
    return [str(row[0]) for row in qres][0]


def getShapeProp(shacl_g):
    get_prop = """
    SELECT DISTINCT ?target_prop
    WHERE {
        ?a sh:path ?target_prop
    }"""
    qres = shacl_g.query(get_prop)
    return [str(row[0]) for row in qres]


def getShapePropWithType(shacl_g):
    get_prop = """
    SELECT DISTINCT ?target_prop ?datatype
    WHERE {
        ?a sh:path ?target_prop;
           sh:datatype|sh:class ?datatype.
    }"""
    qres = shacl_g.query(get_prop)
    return {str(row[0]): str(row[1]).replace("http://www.w3.org/2001/XMLSchema#", "xsd:").replace(
        "http://dbpedia.org/ontology/", "dbo:") for row in qres}


def getSimplifiedProp(prop):
    if ("#" in prop):
        splitted = prop.split("#")
    else:
        splitted = prop.split("/")
    return splitted[-1]


def extract_triplets(text):
    triplets = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
    return triplets


datafiles = [ "/user/cringwal/home/Desktop/RES_XP_last/NEW_CONFIG/FILTERED/PLAIN/op_and_dt_old/DS_turtle_test.json"]
shape = Graph()
shape_file = "/user/cringwal/home/PycharmProjects/Kastor/shapes/PersonShape_op_and_dp.ttl"

shape.parse(shape_file)
namespaces = shape.namespaces()
prop_focus = getShapeProp(shape)
dict_simply_real = {}
for p in prop_focus:
    dict_simply_real[getSimplifiedProp(p)] = p
type_prop = getShapePropWithType(shape)
type_triples = getShapeType(shape)

prop_map = {
    'place of birth': "birthPlace",
    'place of death': "deathPlace",
    'country of citizenship': "nationality",
    "date of birth": "birthDate",
    "date of death": "deathDate"

}
triplet_extractor = pipeline('text2text-generation', model='Babelscape/rebel-large', tokenizer='Babelscape/rebel-large')
tokenizer_kwargs = {'truncation':True,'max_length':512}

prop_list = {}
nb_pred_triples=0
nb_onto_ok_triples=0

datafile = "/user/cringwal/home/Desktop/RES_XP_last/NEW_CONFIG/CORRECTED/PLAIN/op_and_dt_old/DS_turtle_train.json"

#datafiles = [ "/user/cringwal/home/Desktop/RES_XP_last/NEW_CONFIG/CORRECTED/PLAIN/op_and_dt_old/DS_turtle_test.json"]

splitter = KFold(10, shuffle=False)
with open(datafile) as user_file:
    data = json.load(user_file)
    data_train=data[0:1000]
    abs_dict={}
    gold_triples=[]
    pred_triples=[]
    for fold, (train_index, test_index) in enumerate(splitter.split(data_train)):
      
        
        for idx in test_index:
            row=data_train[idx]
            print(row["ent"])
            # We need to use the tokenizer manually since we need special tokens.
            input_txt = row["abstract"]
            extracted_text = triplet_extractor.tokenizer.batch_decode(
                [triplet_extractor(input_txt, return_tensors=True, return_text=False,**tokenizer_kwargs)[0]["generated_token_ids"]])
            # Function to parse the generated text and extract the triplets

            extracted_triplets = extract_triplets(extracted_text[0])
            nb_pred_triples+=len(extracted_triplets)
            gold_triples_temp,parsed=scr_fct.toListRel(row["triples"],"turtle",facto=False,grammar=None)
            subj_gold=gold_triples_temp[0][0]
            subj_clean_gold = scr_fct.uncodeurl(subj_gold.replace("dbr:", "").replace(":", "").strip())

            abs_dict[subj_clean_gold]=row["abstract"]
            pred_triples_temp=[]
            obj_found={}
            added=[]
            for triple in extracted_triplets:
                
                subj = uncodeurl(triple["head"].replace(" ", "_"))
                pred_triples_temp.append([subj,"type","dbo:Person"])
                obj = uncodeurl(triple["tail"].replace(" ", "_"))
                if (triple["type"] in prop_map.keys()):

                    pred = prop_map[triple["type"]]

                    if ("date" in pred.lower()):
                        obj = uncodeurl(triple["tail"].replace("_", " "))
                        matches = datefinder.find_dates(obj)
                        dates = []
                        try:
                            for match in matches:
                                if (match != ''):
                                    dates.append(match.strftime('%Y-%m-%d'))
                        except Exception as error:
                            print(error)
                            pass
                        if (len(dates) > 0):
                            pred2 = pred.replace("Date", "Year")
                            if(pred+"$"+ dates[0] not in added):
                                pred_triples_temp.append([subj, pred,  dates[0]])
                                added.append(pred+"$"+ dates[0])
    
                            if(pred2+"$"+ dates[0][0:4] not in added):
                                added.append(pred2+"$"+ dates[0][0:4])
                                pred_triples_temp.append([subj, pred2, dates[0][0:4]])
    
                    else:
                        
                        if(pred+"$"+obj not in added):
                            added.append(pred+"$"+obj)
                            pred_triples_temp.append([subj, pred, obj])

                    obj_found[obj] = (subj, pred)
                for triple in extracted_triplets:
                    subj = uncodeurl(triple["head"].replace(" ", "_"))
                    if (subj in obj_found.keys()):
                        if (triple["type"] == 'country'):
                            subj2 = uncodeurl(obj_found[subj][0]).replace(" ", "_")
                            rel2 = obj_found[subj][1]
                            obj = uncodeurl(triple["tail"].replace(" ", "_"))
                            if (rel2+"$"+obj not in added):
                                added.append(rel2+"$"+obj)
                                pred_triples_temp.append([subj2, rel2, obj])
                    else:
                        if (triple["type"] not in prop_list.keys()):
                            prop_list[triple["type"]] = 0
                        prop_list[triple["type"]] += 1

            print(">>>>>>>>>>> GOLD")
            print(gold_triples_temp)
            print(">>>>>>>>>>> PRED")
            print(pred_triples_temp)
            gold_triples.append(gold_triples_temp)
            pred_triples.append(pred_triples_temp)
            
            nb_onto_ok_triples+=len(pred_triples_temp)
           
    
        scores, part_parsed, part_subj_ok, part_valid_s, part_valid_r, callbacks = scr.re_score_withShapeWithObjREBEL(pred_triples, gold_triples, shape,  abs_dict)
        scores["OntoConf"]=nb_onto_ok_triples/nb_pred_triples
        scores["part_valid_r"]=part_valid_r
        scores["part_valid_s"]=part_valid_s
        scores["part_parsed"]=part_parsed
        scores["part_subj_ok"]=part_subj_ok
       # type_abs="new"
        if("old" in datafile):
            type_abs="old"
        with open("/user/cringwal/home/Desktop/RESULTS_DATA/REBEL_results/PLAIN_scores_" + type_abs + "_"+str(fold)+"_test.json",'w', encoding='utf-8') as f:
            json.dump(scores, f)
        e = pd.DataFrame.from_dict(callbacks["to_inspect"])
        e.to_csv("/user/cringwal/home/Desktop/RESULTS_DATA/REBEL_results/PLAIN_inspect_" + type_abs  + "_"+str(fold)+ "_test.csv", encoding='utf-8',
                 index=True)
        e = pd.DataFrame.from_dict(callbacks["notvalid_examples"])
        e.to_csv("/user/cringwal/home/Desktop/RESULTS_DATA/REBEL_results/PLAIN_not_valid_" + type_abs  + "_"+str(fold)+ "_test.csv",
                 encoding='utf-8',
                 index=True)

