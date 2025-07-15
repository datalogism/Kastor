#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 15:07:35 2024

@author: cringwal
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 30 16:33:40 2024

@author: cringwal
"""
import pandas as pd
from rdflib import Graph

from pyshacl import validate
from rdflib import Graph

import json

import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/kstor/')
import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct

import itertools
import datefinder
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF
from unidecode import unidecode
import random
import urllib
import urllib.parse

import urllib.parse


def uncodeurl(URL):
    if ("%" in URL):
        print("HEY")
        return urllib.parse.unquote(URL)
    else:
        return URL


def cleanURL(entity):
    if ("%" not in entity):
        txt = urllib.parse.quote(
            entity.replace("http://dbpedia.org/resource/", "").replace("https://dbpedia.org/resource/", "")).replace(
            ".", "%2E")
    else:
        txt = entity.replace("http://dbpedia.org/resource/", "").replace("https://dbpedia.org/resource/", "")
    return txt

def checkIfExistInKG(sparql_ep,ent,ent_type):
    query = "SELECT (COUNT(DISTINCT ?p) as ?nb_p) { <"+ent+"> a <"+ent_type+">; ?p ?o. } "
    print(query)
    results = ct.sparql_service_to_dataframe(sparql_ep, query)
    return int(results["nb_p"].iloc[0])

def triplesWithShape(ent_k, list_relations, shacl_g):
    type_triple = ts.getShapeType(shacl_g)
    names_spaces = shacl_g.namespaces()

    g = Graph()
    dbr = Namespace("http://dbpedia.org/resource/")
    g.bind("dbr", dbr)
    for ns_prefix, namespace in names_spaces:
        current_ns = Namespace(str(namespace))
        g.bind(ns_prefix, current_ns)

    type_triple_uri = URIRef(type_triple)
    current_entity = URIRef(ent_k)

    g.add((current_entity, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), type_triple_uri))
    for rel in list_relations:
        prop_uri = URIRef(rel["prop"])
       # for v in rel["value"]:
        v=rel["value"]
        if ("dbo:" in rel["type"]):

            v2 = rs.cleanEntURL(v)

            obj_val = URIRef(v2)
        else:

            obj_val = Literal(v, datatype=rel["type"].replace("xsd:", "http://www.w3.org/2001/XMLSchema#"))
        g.add((current_entity, prop_uri, obj_val))

    return g


shape_file = "/user/cringwal/home/PycharmProjects/Kastor/shapes/PersonShape_op_and_dp.ttl"

shacl_g = Graph()
shacl_g.parse(shape_file)

namespaces = shacl_g.namespaces()
prop_focus = ts.getShapeProp(shacl_g)
type_prop = ts.getShapePropWithType(shacl_g)
type_triples = ts.getShapeType(shacl_g)

SAMPLE = {}
metadata_path = "/user/cringwal/home/Desktop/synthBio/SynthBio.json"
with open(metadata_path, encoding="utf-8") as json_file:
    data = json.load(json_file)

for row in data:
    attr = row["attrs"]

    ent_uri = urllib.parse.quote(row["attrs"]["name"].replace(" ", "_"))
    ent_uri = rs.cleanEntURL(ent_uri)
    ent_2 = rs.cleanEnt(ent_uri)
    print(ent_uri)
    list_relation = []
    found_uri=True
    for k in attr.keys():
        #print(k)
        val = attr[k]
        # if(k == "name"):
        #   p='http://www.w3.org/2000/01/rdf-schema#label'
        #  list_relation.append({"prop":p,"value":str(val),"type":type_prop[p]})

        if (k == "label"):
            p = 'http://www.w3.org/2000/01/rdf-schema#label'
            list_relation.append({"prop": p, "value": str(val), "type": type_prop[p]})
        if (k == "birth_date"):
            vals = [x for x in datefinder.find_dates(val)]
            if (len(vals) == 1):
                date = vals[0].strftime('%Y-%m-%d')
                print(date)
                p = 'http://dbpedia.org/ontology/birthDate'
                list_relation.append({"prop": p, "value": date, "type": type_prop[p]})
        if (k == "death_date"):
            vals = [x for x in datefinder.find_dates(val)]
            if (len(vals) == 1):
                date = vals[0].strftime('%Y-%m-%d')
                print(date)
                p = 'http://dbpedia.org/ontology/deathDate'
                list_relation.append({"prop": p, "value": date, "type": type_prop[p]})
        if (k == "birth_place"):
            p='http://dbpedia.org/ontology/birthPlace'
            type_p=type_prop[p].replace("dbo:","http://dbpedia.org/ontology/")
            val2=val.split(',')[0]
            obj_uri = urllib.parse.quote(val2.replace(" ", "_"))
            obj_uri = rs.cleanEntURL(obj_uri)
            exist=checkIfExistInKG("http://localhost:8080/sparql",obj_uri,type_p)

            if (exist > 0):
                list_relation.append({"prop": p, "value": obj_uri, "type": type_prop[p]})
        if (k == "death_place"):
            p = 'http://dbpedia.org/ontology/deathPlace'
            type_p = type_prop[p].replace("dbo:", "http://dbpedia.org/ontology/")
            val2 = val.split(',')[0]
            obj_uri = urllib.parse.quote(val2.replace(" ", "_"))
            obj_uri = rs.cleanEntURL(obj_uri)
            exist = checkIfExistInKG("http://localhost:8080/sparql", obj_uri, type_p)
            #print(obj_uri,">",exist)


            if (exist > 0):
                list_relation.append({"prop": p, "value": obj_uri, "type": type_prop[p]})

        if (k == "nationality"):

            p = 'http://dbpedia.org/ontology/nationality'
            type_p = "http://www.w3.org/2002/07/owl#Thing"
            val2 = val.split(',')[0]
            obj_uri = urllib.parse.quote(val2.replace(" ", "_"))
            obj_uri = rs.cleanEntURL(obj_uri)
            exist = checkIfExistInKG("http://localhost:8080/sparql", obj_uri, type_p)


            if (exist > 0):
                list_relation.append({"prop": p, "value": obj_uri, "type": type_prop[p]})
    if found_uri:
        print("========================")
        print(list_relation)
        triples = triplesWithShape(ent_uri, list_relation, shacl_g)
        print("========================")
        print(triples.serialize(format="turtle"))
        print("========================")
        triples2 = ts.DatesInferences(triples, "http://dbpedia.org/ontology/birthDate",
                                      "http://dbpedia.org/ontology/birthYear")
        triples3 = ts.DatesInferences(triples2, "http://dbpedia.org/ontology/deathDate",
                                      "http://dbpedia.org/ontology/deathYear")
        SAMPLE[ent_uri] = {"triples": triples3.serialize(format="turtle"), "abstract": row["biographies"][0],
                           "ent": ent_2}
####### TURTLE
dataset_turtle = []
for ent in SAMPLE.keys():
    row = SAMPLE[ent]
    dataset_turtle.append(row)

with open("/user/cringwal/home/Desktop/RES_XP_last/TEST/DS_turtle_synthbio.json", 'w', encoding='utf-8') as f:
    json.dump(dataset_turtle, f)

sample_limit = 2000
dataset_turtle = sorted(dataset_turtle, key=lambda x: random.random())
dataset_turtleLight = []
for row in dataset_turtle[0:(sample_limit - 1)]:
    triples = row["triples"]
    new = row.copy()
    triples_list1 = rs.simplifyTutle(triples, False, True, True)
    new["triples"] = triples_list1
    dataset_turtleLight.append(new)

with open(
        "/user/cringwal/home/Desktop/RES_XP_last/TEST/DS_turtleS_0datatype_1inLine_1facto_synthbio_test.json",
        'w', encoding='utf-8') as f:
    json.dump(dataset_turtleLight, f)
