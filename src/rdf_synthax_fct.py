#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 10:37:45 2023

@author: cringwal
"""
import re 
import json
from rdflib import Graph
import urllib.parse

def cleanEntURL(entity):
    if("%" not in entity):
        txt=urllib.parse.quote(entity.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")).replace(".","%2E")
    else:
        txt = entity.replace("http://dbpedia.org/resource/", "").replace("https://dbpedia.org/resource/", "")
    return "http://dbpedia.org/resource/"+txt

def cleanTurtle(triples_init):
    g1 = Graph()
    g1.parse(data=triples_init, format="turtle")
    
    #print(">>>>>>>>>>>>>>>>> BEFORE")
    # knows_query = '''
    # SELECT * 
    # WHERE {
    #     ?s ?p ?o
    # }'''
    
    # qres = g1.query(knows_query)
    # for row in qres:
    #     print(row.s, row.p, row.o)
        
    DELETE_query = '''
    DELETE{ ?s ?p ?o }
    WHERE {
        ?s ?p ?o.    
        FILTER (?o=""^^xsd:string)
    }'''
    
    g1.update(DELETE_query)

    # print(">>>>>>>>>>>>>>>>>AFTER")
    
    # knows_query = '''
    # SELECT * 
    # WHERE {
    #     ?s ?p ?o
    # }'''
    
    # qres = g1.query(knows_query)
    # for row in qres:
    #     print(row.s, row.p, row.o)
    
    return g1.serialize(format="turtle")
    

def reOrderNtriples(t):
    list_orig = t.split(".\n")
    type_t = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    label_t = "http://www.w3.org/2000/01/rdf-schema#label"
    new_list = []
    for elem in list_orig:
        if(type_t in elem):
            new_list.append(elem)
            break
    for elem in list_orig:
         if(label_t in elem):
             new_list.append(elem)
             break
    
    for elem in list_orig:
         if(elem not in new_list):
             new_list.append(elem)
    new_triples=".\n".join(new_list)
    return new_triples

def cleanTxt(txt):
    try:
        if(txt[0]==" "):
            txt=txt[1:]
    except:
        print(txt)
    if(txt[-1]==" "):
        txt=txt[:-1]
    return txt.strip()

def cleanTxtAndPrefixes(txt,prefixes):
    txt=cleanTxt(txt)
    for p in prefixes:
        txt=txt.replace(p+":","")
    return txt

def cleanEnt(txt):
    txt=txt.replace("<","").replace(">","").replace("https://dbpedia.org/resource/","").replace("http://dbpedia.org/resource/","")
    return cleanTxt(txt)     

def simplifyTutle(t,datatype=False, inLine=False, facto=True):
    g1 = Graph()
    g1.parse(data=t, format="turtle")
    if(facto==False):
        t=g1.serialize(format="ntriples") 
        t=reOrderNtriples(t)
        for ns_prefix, namespace in g1.namespaces():
           t=t.replace(namespace,"")
        t=t.replace("<",":")
        
    for ns_prefix, namespace in g1.namespaces():
       t=t.replace(namespace,"")
      
    test=t 
    test=test.replace("https://dbpedia.org/resource/","dbr:").replace("http://dbpedia.org/resource/","dbr:")
    test=test.replace("\n\n","\n").replace(",\n"," ,\n")
    splitted=test.split("\n")
    new_=""
    for split in splitted:
        if("prefix" not in split and len(split.strip())>2):

                if("^^" in split and datatype==False):
                    first=split.split("^^")
                    new_=new_+"\n"+first[0]+" "+first[1].split(" ")[1]
                else:
                    new_=new_+"\n"+split
    #test=re.sub("@prefix .{2,4}: <(?:\"[^\"]*\"['\"]*|'[^']* '['\"]*|[^'\">])+> .\\n","",test)
    
    new2=re.sub(" .{2,4}:"," :",new_).replace("    ","   ").replace("dbr","")
    new2=new2.replace("<","").replace(">","").replace("  .:",".:").replace(" .:",". :")
    if(new2[0:1]=="\n"):
        new2=new2[1:len(new2)]
    
    if(inLine):
        new2= new2.replace("\n:",":").replace("\n<","").replace(".\n",".")
        new2=re.sub(r"[\n\t]*", "",new2).replace("   "," ").replace(" ;",";").strip()
    return new2.strip()

def TurtleToList(t, facto=True):
    # t=triples
    # facto=True
    g1 = Graph()
    g1.parse(data=t, format="turtle")
    prefixes=[]
    for ns_prefix, namespace in g1.namespaces():
        prefixes.append(ns_prefix)
    
    splitted = t.split("\n")
    new_=[]
    for split in splitted:
        if("prefix" not in split and len(split.strip())>2):
                if("^^" in split):
                    first=split.split("^^")
                    txt=first[0]
                    if(split[-1] in [".",";",","]):
                        txt+=" "+split[-1]
                    new_.append(txt)
                else:
                    new_.append(split)
    
    resp= "\n".join(new_).replace(" a "," type ")+"\n".strip()
    
    list_container=[]
    triples_list=resp.split(".\n")
    
    for triples in triples_list:
        if(";\n" in triples):
            prop_list=triples.split(";\n")
            subj=prop_list[0].split(" ")[0]
            
            
            temp1=[]
            for prop in prop_list :
                
                sublist=False
                
                prop2=prop.replace(subj,"")
                subj2=cleanTxtAndPrefixes(cleanEnt(subj),prefixes)
                if(",\n" in prop2):
                    
                    object_list=prop2.strip().split(",\n")
                    
                    if(len(object_list)>0):
                        sublist=True
                        prop_name=object_list[0].split(" ")[0]
                        temp2=[]
                        for obj in object_list :
                            prop_val=obj.replace(prop_name,"").replace('"',"").replace('.',"").strip()
                            if(facto==True):
                                temp2.append(cleanTxtAndPrefixes(prop_val,prefixes))
                            else:
                                list_container.append([subj2,cleanTxtAndPrefixes(prop_name,prefixes),cleanTxtAndPrefixes(prop_val,prefixes)])
                        if(facto==True):
                             temp1.append([cleanTxtAndPrefixes(prop_name,prefixes),temp2])
                    else:
                        sublist=False
                        
                if(sublist==False):
                    object_list=[token for token in prop2.split(" ") if token not in [""," ",",",".",";"]]
                    prop_name=object_list[0]
                    prop_val=prop2.replace(prop_name,"").replace('"',"").replace('.',"").replace('\n',"").strip()
                    
                    if(facto==True):
                        temp1.append([cleanTxtAndPrefixes(prop_name,prefixes),cleanTxtAndPrefixes(prop_val,prefixes)])
                    else:
                        list_container.append([subj2,cleanTxtAndPrefixes(prop_name,prefixes),cleanTxtAndPrefixes(prop_val,prefixes)])
            
            if(facto==True):
                
                subj2=cleanTxtAndPrefixes(cleanEnt(subj),prefixes)
                list_container.append([subj2,temp1])

            
    return list_container

def FactorisedListTOList(list_):
    flat_list=[]
    for t in list_:
        if(type(t[1])==list):
            subj=t[0]
            
            for pred_list in t[1]:
                rel=pred_list[0]
                if(type(pred_list[1])==list):
                    for t3 in pred_list[1]:
                        flat_list.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(t3)])
                else:
                    flat_list.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(pred_list[1])])
        else:
            flat_list.append([cleanEnt(t[0]),cleanTxt(t[1]),cleanTxt(t[2])])
    return flat_list

def FactorisedTagTOTag(tags): 
    flat_list=""
    list_triples=[token for token in tags.split("<et>") if token !=""]
    for triples in list_triples:
        #triples=list_triples[0]
        subj_list=[token for token in triples.split("<subj>") if token !=""]
        for subj_comp in subj_list:
            #subj_comp=subj_list[0]
            rel_list=[token for token in subj_comp.split("<rel>") if token !=""]
            subj=rel_list[0]
             #flat_list+="<subj>"+subj
            for rel_comp in rel_list[1:]:
                #rel_comp= rel_list[1]
                rel_list2=[token for token in rel_comp.split("<obj>") if token !=""]
                relation=rel_list2[0]
               # flat_list+="<rel>"+relation
                if(len(rel_list2)==2):
                    obj=rel_list2[1]
                    flat_list+="<subj>"+cleanEnt(subj)+"<rel>"+cleanTxt(relation)+"<obj>"+cleanTxt(obj)+"<et>"
                else:
                    for obj in rel_list2[1:]:
                        flat_list+="<subj>"+cleanEnt(subj)+"<rel>"+cleanTxt(relation)+"<obj>"+cleanTxt(obj)+"<et>"
    return flat_list

    
def TurtleToTag(t, facto=True):
    to_list=TurtleToList(t, facto)
    list_=""
    if(facto==False):
        for t in to_list:
            list_=list_+"<subj>"+cleanEnt(t[0])+"<rel>"+cleanTxt(t[1])+"<obj>"+cleanTxt(t[2])+"<et>"
    else:
        for t in to_list:
            if(type(t[1])==list):
                list_=list_+"<subj>"+cleanEnt(t[0])
                
                for pred_list in t[1]:
                    list_ += "<rel>"+cleanTxt(pred_list[0])
                    if(type(pred_list[1])==list):
                        for t3 in pred_list[1]:
                            list_=list_+"<obj>"+cleanTxt(t3)
                    else:
                        list_=list_+"<obj>"+cleanTxt(pred_list[1])
            else:
                list_=list_+"<subj>"+cleanEnt(t[0])+"<rel>"+cleanTxt(t[1])
                        
                        
            list_=list_+"<et>"
    return list_
        
# from rdflib import Graph, URIRef, Literal
# from rdflib.namespace import RDFS, XSD
# g1 = Graph()
# test='''@prefix dbo: <http://dbpedia.org/ontology/>.
# @prefix dbr: <http://dbpedia.org/resource/>.
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.

# dbr:Homer_Simpson a dbo:Person ;
#     rdfs:label "Homer Simpson"^^<xsd:string> ;
#     dbo:birthDate "1987-04-19"^^<xsd:date> ;
#     dbo:birthYear "1987"^^<xsd:gYear>.'''
# g1.parse(data=test, format="turtle")

# # g1.add((
# #     URIRef("http://dbpedia.org/resource/Monja_Danischewsky"),
# #     RDFS.label,
# #     Literal("Nick", datatype=XSD.string)
# # ))
# g1.serialize(format="ntriples")
# with open("/user/cringwal/home/Desktop/THESE/experiences/exp2out/RAW_SAMPLE_data/DS_turtle.json",encoding="utf-8") as json_file:
#         data = json.load(json_file) 

# data2=[]
# for row in data:
#     temp={}
#     temp["entity"]=row["entity"]
#     if("http" in row["triples"]):
#         print("turtle3")
#         break
#     data2.append(temp) 
    
       
# def TurtleSToList(txt,facto=True):
#     list_rel=[]
#     if facto == True:
#         temp=txt.split(";")
#         subj=re.findall("(?<=:).*?(?=\s)",temp[0])[0]
#         type_ = None
#         for t in ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',"rdfs:type","type","a"]:
#             if(" "+t+" " in  temp[0]):
#                 splitted=temp[0].split(" "+t+" ")
#                 type_=splitted[1].replace(":","")
#                 break
    
#         if(type_):
#             list_rel.append([subj,"type",type_])
#         for i in range(1,len(temp)): 
#             rel=re.findall("(?<=:).*?(?=\s)",temp[i])[0]
#             obj=re.findall("(?<=\")(.*)(?=\")",temp[i])[0]
#             list_rel.append([subj,rel,obj])
#     else:
#         temp=[t for t in txt.split(".") if len(t)>1]
#         subj=re.findall("(?<=:).*?(?=\s)",temp[0])[0]
#         type_ = None
#         for t in ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',"rdfs:type",":type","type","a"]:
#             if(t in  temp[0]):
#                 splitted=temp[0].split(" "+t+" ")
#                 type_=splitted[1].replace(":","").strip()
#                 break
#         if(type_):
#             list_rel.append([subj,"type",type_])
#         for i in range(1,len(temp)): 
#             temp_replaced= temp[i].replace(":"+subj,"").replace(subj,"")
#             rel=re.findall("(?<=:).*?(?=\s)",temp_replaced)[0].strip()
#             obj=re.findall("(?<=\")(.*)(?=\")",temp_replaced)[0].strip()
#             list_rel.append([subj,rel,obj])
            
#     return list_rel




# print("S1")
# S1=simplifyTutle(data[10]["triples"],datatype=True,inLine=True,facto=True)
# print(TurtleSToList(S1,True)) #OK
# print("S8")
# S8=simplifyTutle(data[10]["triples"],datatype=True,inLine=False,facto=True)
# print(TurtleSToList(S8,True)) ##  OK
# print("S3")
# S3=simplifyTutle(data[10]["triples"],datatype=False,inLine=False,facto=True)
# print(TurtleSToList(S3,True)) ## OK
# print("S6")
# S6=simplifyTutle(data[10]["triples"],datatype=False,inLine=True,facto=True)
# print(TurtleSToList(S6,True))

# S2=simplifyTutle(data[10]["triples"],datatype=False,inLine=False,facto=False)
# print(TurtleSToList(S2,False))
# S4=simplifyTutle(data[10]["triples"],datatype=False,inLine=True,facto=False)
# print(TurtleSToList(S4,False))
# S5=simplifyTutle(data[10]["triples"],datatype=True,inLine=False,facto=False)
# print(TurtleSToList(S5,False))
# S7=simplifyTutle(data[10]["triples"],datatype=True,inLine=True,facto=False)
# print(TurtleSToList(S7,False))
 