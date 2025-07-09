#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 23:19:49 2025

@author: cringwal
"""

print("ICI")
from rdflib import Graph
import os
#os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
print("LA")
from transformers import pipeline
import json

print("LA")
import datefinder
import pandas as pd
import sys
sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/slm/src/')

print("ICI")
import score_fct as scr_fct
import score as scr
import urllib.parse
import os

def uncodeurl(URL):
    if("%" in URL):
        print("HEY")
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

print("START")

datafiles = [ "/user/cringwal/home/Desktop/RES_XP_last/NEW_CONFIG/CORRECTED/PLAIN/op_and_dt_old/DS_turtleS_0datatype_1inLine_1facto_test.json"]
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
    "nationality": 'country of citizenship',
    "date of birth": "birthDate",
    "date of death": "deathDate"

}
print("ICI")
# [, 'participant',  'sport', 'member of sports team', 'country', 'league', 'point in time', 'member of political party',, 'located in the administrative territorial entity', 'location', 'place of death', 'member of', 'applies to jurisdiction', 'office held by head of government', 'participant in', 'capital', 'contains administrative territorial entity', 'genre', 'drafted by', 'capital of', 'subclass of', 'educated at', 'award received', 'winner', 'father', 'mother', 'child', 'spouse', 'conflict', 'headquarters location', 'instance of', 'position held', 'owned by', 'part of', 'owner of', 'sibling', 'operator', 'position played on team / speciality', 'has part', 'diplomatic relation', 'shares border with', 'inception', 'author', 'publication date', 'notable work', 'occupation', 'field of this occupation']
triplet_extractor = pipeline('text2text-generation', model='Babelscape/rebel-large', tokenizer='Babelscape/rebel-large')
prop_list = {}
for dataf in datafiles:
    with open(dataf) as user_file:
        data = json.load(user_file)
        abs_dict={}
        gold_triples=[]
        pred_triples=[]
        for row in data:
            print(row["ent"])
            # We need to use the tokenizer manually since we need special tokens.
            input_txt = row["abstract"]
            try:
                extracted_text = triplet_extractor.tokenizer.batch_decode(
                    [triplet_extractor(input_txt, return_tensors=True, return_text=False)[0]["generated_token_ids"]])
                # Function to parse the generated text and extract the triplets

                extracted_triplets = extract_triplets(extracted_text[0])
                gold_triples_temp,parsed=scr_fct.toListRel(row["triples"],"turtle",facto=False,grammar=None)
                subj_gold=gold_triples_temp[0][0]
                abs_dict[subj_gold]=row["abstract"]
                pred_triples_temp=[]
                obj_found={}

                for triple in extracted_triplets:

                    subj = uncodeurl(triple["head"].replace(" ", "_"))
                    obj = uncodeurl(triple["tail"])
                    if (triple["type"] in prop_map.keys()):

                        pred = prop_map[triple["type"]]

                        pred_triples_temp.append([subj, pred, obj])

                        if ("date" in pred.lower()):
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
                                pred_triples_temp.append([subj, pred, dates[0]])
                        else:
                            obj = uncodeurl(triple["tail"].replace(" ", "_"))
                        obj_found[obj] = (subj, pred)
                    for triple in extracted_triplets:
                        subj = uncodeurl(triple["head"].replace(" ", "_"))
                        if (subj in obj_found.keys()):
                            if (triple["type"] == 'country'):
                                subj2 = uncodeurl(obj_found[subj][0]).replace(" ", "_")
                                rel2 = obj_found[subj][1]
                                obj = uncodeurl(triple["tail"].replace(" ", "_"))
                                if ([subj2, rel2, obj] not in pred_triples_temp):
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
            except:
                print("PBlentght")

        scores, part_parsed, part_subj_ok, part_valid_s, part_valid_r, callbacks = scr.re_score_withShapeWithObjREBEL(pred_triples, gold_triples, shape,  abs_dict)
        type_abs="new"
        if("old" in dataf):
            type_abs="old"
        with open("/user/cringwal/home/Desktop/RESULTS_DATA/REBEL_results/NEW_Plain_scores_" + type_abs + "_test.json",'w', encoding='utf-8') as f:
            json.dump(scores, f)
        e = pd.DataFrame.from_dict(callbacks["to_inspect"])
        e.to_csv("/user/cringwal/home/Desktop/RESULTS_DATA/REBEL_results/NEW_Plain_inspect_" + type_abs + "_test.csv", encoding='utf-8',
                 index=True)
        e = pd.DataFrame.from_dict(callbacks["notvalid_examples"])
        e.to_csv("/user/cringwal/home/Desktop/RESULTS_DATA/REBEL_results/NEW_MD_not_valid_" + type_abs + "_test.csv",
                 encoding='utf-8',
                 index=True)

