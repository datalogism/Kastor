
from rdflib import Graph
import json
from os.path import isfile, join
from argparse import ArgumentParser
import pandas as pd

from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/kstor/')
#import  abstractExtended as ae
import src.triple_shapes as ts
import src.class_signatures as cs



shape_file_path="/user/cringwal/home/PycharmProjects/Kastor/shapes/FilmShapeFromOnto.ttl"
shape = Graph()
shape.parse(shape_file_path)
sparql_ep = 'http://localhost:8080/sparql'


print(">> get usefull data")
namespaces = shape.namespaces()
prop_focus = ts.getShapeProp(shape)
dict_simply_real={}
for p in prop_focus:
    dict_simply_real[ts.getSimplifiedProp(p)]=p
type_prop = ts.getShapePropWithType(shape)
type_triples = ts.getShapeType(shape)
print(len(type_prop.keys()))
nb_combin={}
for i in range(100):
    print(">>>>",i)
    seq=range(i)
    class_sign_all=cs.get_All_ClassSignatures(shape,seq)

    nb_combin[str(i)]=len(class_sign_all)
    print(nb_combin[str(i)])
