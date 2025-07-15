#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 17:49:15 2024

"""

from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
from SPARQLWrapper import get_sparql_dataframe
import itertools
import sys
from urllib.parse import unquote


#sys.path.append('/user/cringwal/home/Desktop/THESE/CORESE_DATASET_build/')
import src.corese_tools as ct
import src.triple_shapes as ts
import src.rdf_synthax_fct as rs

    
def get_NbEntitiesNGToDo(ng,found_ng,sparql_ep):
    ########## QUERIES STATS
    sparql = SPARQLWrapper(sparql_ep) 
    
    sparql.setQuery("SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+ng+"> where {  ?s ?p ?o.    FILTER NOT EXISTS { GRAPH  <"+found_ng+"> { ?s ?p ?o }  }  }")
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    
    nb_ent=int(qres["results"]["bindings"][0]["nb"]["value"])
    print("ALL entities : ",nb_ent)
    return nb_ent

def get_NbEntitiesNG(ng,sparql_ep):
    ########## QUERIES STATS
    sparql = SPARQLWrapper(sparql_ep) 
    
    sparql.setQuery(" SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+ng+"> where {  ?s ?p ?o.  }")
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    
    nb_ent=int(qres["results"]["bindings"][0]["nb"]["value"])
    print("ALL entities : ",nb_ent)
    return nb_ent

def get_NbEntitiesType(target_class,sparql_ep):
    ########## QUERIES STATS
    sparql = SPARQLWrapper(sparql_ep) 
    
    sparql.setQuery("PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#>  SELECT (COUNT(DISTINCT ?s) as ?nb) from <urn:x-arq:DefaultGraph>  where {  ?s a <"+target_class+">.  ?s dcat:resource_identifier  ?uid.  }")
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    
    nb_ent=int(qres["results"]["bindings"][0]["nb"]["value"])
    print("ALL entities : ",nb_ent)
    return nb_ent

def get_NbEntitiesNG(ng,sparql_ep):
    ########## QUERIES STATS
    sparql = SPARQLWrapper(sparql_ep) 
    
    sparql.setQuery("PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#>  SELECT (COUNT(DISTINCT ?s) as ?nb) from <"+ng+">  where {  ?s ?p ?o.  }")
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    
    nb_ent=int(qres["results"]["bindings"][0]["nb"]["value"])
    print("ALL entities : ",nb_ent)
    return nb_ent

def get_ClassSignatureNb_K(target_class, type_prop_focus, all_type_prop, sparql_ep):
   
    set_all=set(all_type_prop)
    set_current=set(type_prop_focus)
    set_diff=set_all.difference(set_current)
    
    sparql = SPARQLWrapper(sparql_ep) 
    idx=0
    set_1_txt=""
    set_2_txt=""
    for prop in set_current:
        set_1_txt+="?s <"+prop+"> ?o"+str(idx)+". "
        idx+=1
    if(len(list(set_current))!=len(set_all)):
        for prop in set_diff:
            set_2_txt+="filter not exists {?s <"+prop+"> ?o"+str(idx)+". }. "
            idx+=1
        
    if(len(list(set_current))!=len(set_all)):
        
        for prop in set_diff:
            set_2_txt+="filter not exists {?s <"+prop+"> ?o"+str(idx)+". }. "
            idx+=1
            
    query1 = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#> SELECT (COUNT(DISTINCT ?s) as ?nb) WHERE {  ?s a <"+target_class+">.  ?s dcat:resource_identifier  ?uid. "+set_1_txt+" "+set_2_txt+" } "
    sparql.setQuery(query1)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb=int(qres["results"]["bindings"][0]["nb"]["value"])
    return nb

def get_PropertiesRealised(prop,found_ng,sparql_ep):
    query1 = "PREFIX dbo: <http://dbpedia.org/ontology/>  select (COUNT(DISTINCT ?s) as ?nb) from <" + found_ng + "> where {  ?s <"+prop+"> ?o } "
    print(query1)

    sparql = SPARQLWrapper(sparql_ep)
    sparql.setQuery(query1)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb = int(qres["results"]["bindings"][0]["nb"]["value"])
    return nb

def get_PropertyRandomSample_NG(target_class, type_prop_focus, all_type_prop, ng, sparql_ep,size_sample):
    set_all = set(all_type_prop)
    set_current = set(type_prop_focus)
    set_diff = set_all.difference(set_current)

    sparql = SPARQLWrapper(sparql_ep)
    idx = 0
    set_1_txt = ""
    set_2_txt = ""
    for prop in set_current:
        set_1_txt += "?s <" + prop + "> ?o" + str(idx) + ". "
        idx += 1
   # if (len(list(set_current)) != len(set_all)):
    #    for prop in set_diff:
     #       set_2_txt += "OPTIONAL {?s <" + prop + "> ?o" + str(idx) + ". }. "
      #      idx += 1


    query1 = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#> SELECT DISTINCT ?s FROM <" + ng + "> WHERE { " + set_1_txt + " " + set_2_txt + " } ORDER BY RAND() LIMIT "+str(size_sample)
    sparql.method = 'POST'
    sparql.setQuery(query1)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    # print(qres)
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects

def get_ClassSignatureRandomSample_NG(target_class, type_prop_focus, all_type_prop, ng, sparql_ep,size_sample):
    set_all = set(all_type_prop)
    set_current = set(type_prop_focus)
    set_diff = set_all.difference(set_current)

    sparql = SPARQLWrapper(sparql_ep)
    idx = 0
    set_1_txt = ""
    set_2_txt = ""
    for prop in set_current:
        set_1_txt += "?s <" + prop + "> ?o" + str(idx) + ". "
        idx += 1
    if (len(list(set_current)) != len(set_all)):
        for prop in set_diff:
            set_2_txt += "filter not exists {?s <" + prop + "> ?o" + str(idx) + ". }. "
            idx += 1

    if (len(list(set_current)) != len(set_all)):

        for prop in set_diff:
            set_2_txt += "filter not exists {?s <" + prop + "> ?o" + str(idx) + ". }. "
            idx += 1

    query1 = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#> SELECT DISTINCT ?s FROM <" + ng + "> WHERE { " + set_1_txt + " " + set_2_txt + " } ORDER BY RAND() LIMIT "+str(size_sample)
    print(query1)
    sparql.method = 'POST'
    sparql.setQuery(query1)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    # print(qres)
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects
def get_ClassSignatureNb_NG(target_class, type_prop_focus, all_type_prop, ng, sparql_ep):
   
    set_all=set(all_type_prop)
    set_current=set(type_prop_focus)
    set_diff=set_all.difference(set_current)
    
    sparql = SPARQLWrapper(sparql_ep) 
    idx=0
    set_1_txt=""
    set_2_txt=""
    for prop in set_current:
        set_1_txt+="?s <"+prop+"> ?o"+str(idx)+". "
        idx+=1
    if(len(list(set_current))!=len(set_all)):
        for prop in set_diff:
            set_2_txt+="filter not exists {?s <"+prop+"> ?o"+str(idx)+". }. "
            idx+=1
        
    if(len(list(set_current))!=len(set_all)):
        
        for prop in set_diff:
            set_2_txt+="filter not exists {?s <"+prop+"> ?o"+str(idx)+". }. "
            idx+=1
            
    query1 = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#> SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+ng+"> WHERE { "+set_1_txt+" "+set_2_txt+" } "
    print(query1)
    sparql.method = 'POST'
    sparql.setQuery(query1)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    #print(qres)
    nb=int(qres["results"]["bindings"][0]["nb"]["value"])
    return nb

def get_All_ClassSignatures(shape,type_prop):
    # Generate all possible two-element combinations
    # Convert the resulting iterator to a list
    all_combinations=set()
    for i in range(len(type_prop)):
        combinations = set(itertools.combinations(type_prop, i))
        all_combinations= combinations  | all_combinations
    return list(all_combinations)

def get_Exlude_Ent_NG(ng_out_list,sparql_ep, limit=10, offset=0):
    entity_list=[]
    for ng_out in ng_out_list:
        for ng_out in ng_out_list:
            query="Select DISTINCT ?s FROM <"+ng_out+"> {  ?s ?p ?n. ?n rdf:value ?o. } "
                  
            results=get_sparql_dataframe(sparql_ep, query)
            entity_list+=list(results["s"])
    return list(set(entity_list))
        
def get_RandomSample_NG_in_out(ng_in,ng_out_list,sparql_ep, limit=10, offset=0):

    out_txt=""
    for ng_out in ng_out_list:
        out_txt+=".  FILTER NOT EXISTS { GRAPH  <"+ng_out+"> { ?s ?p ?o } }"
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract FROM <urn:x-arq:DefaultGraph> where {  ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract.  ?s dcat:resource_identifier  ?uid.  FILTER  EXISTS { GRAPH  <"+ng_in+"> { ?s ?p ?o } } "+out_txt+" } ORDER BY ASC(?uid) LIMIT """+str(limit)+" OFFSET "+str(offset)
      
    results=get_sparql_dataframe(sparql_ep, query)

    return results

        
def get_RandomSample_NG_EntAbs(sparql_ep, limit=10, offset=0):

    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract FROM <urn:x-arq:DefaultGraph> where {    ?s dcat:resource_identifier  ?uid.  ?s a dbo:Person.  ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract.  } ORDER BY ASC(?uid) LIMIT "+str(limit)+" OFFSET "+str(offset)
      
    results=get_sparql_dataframe(sparql_ep, query)

    return results




def get_ClassSignatureSample_K(target_class, type_prop_focus, all_type_prop,sparql_ep, limit=10, offset=0):
    
    set_all=set(all_type_prop)
    set_current=set(type_prop_focus)
    set_diff=set_all.difference(set_current)
    idx=0
    set_1_txt=""
    var_1_txt=""
    set_2_txt=""
    for prop in set_current:
        simply=ts.getSimplifiedProp(prop)
        set_1_txt+="?s <"+prop+"> ?"+simply+". "
        var_1_txt+=" ?"+simply
       
    if(len(list(set_current))!=len(set_all)):
        for prop in set_diff:
            set_2_txt+="filter not exists {?s <"+prop+"> ?o"+str(idx)+". }. "
            idx+=1
    # #  BIND(RAND() AS ?sortKey)     } ORDER BY ?sortKey ...       
    # #query="PREFIX dbo: <http://dbpedia.org/ontology/> select ?s "+var_1_txt+" ?abstract where { ?s a <"+target_class+">. ?s dbo:abstract ?abstract. "+set_1_txt+" "+set_2_txt+" FILTER (lang(?abstract) = 'en') } ORDER BY DESC(?s) LIMIT """+str(limit)+" OFFSET "+str(offset)
    # #query="PREFIX dbo: <http://dbpedia.org/ontology/> select ?s "+var_1_txt+" where { ?s a <"+target_class+">. "+set_1_txt+" "+set_2_txt+"} ORDER BY RAND() LIMIT """+str(limit)+" OFFSET "+str(offset)
    # query="PREFIX dbo: <http://dbpedia.org/ontology/> select ?s "+var_1_txt+" where { ?s a <"+target_class+">. ?s dcat:resource_identifier  ?uid. "+set_1_txt+" "+set_2_txt+"} ORDER BY ASC(?uid) LIMIT """+str(limit)+" OFFSET "+str(offset)
    # query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract "+var_1_txt+" where { ?s a <"+target_class+">.  ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. ?s dcat:resource_identifier  ?uid. "+set_1_txt+" FILTER (lang(?abstract) = 'en') } ORDER BY ASC(?uid) LIMIT """+str(limit)+" OFFSET "+str(offset)
    # query1 = "PREFIX dbo: <http://dbpedia.org/ontology/> SELECT (COUNT(DISTINCT ?s) as ?nb) WHERE {  ?s a <"+target_class+">. "+set_1_txt+" "+set_2_txt+" } "
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract "+var_1_txt+" where { ?s a <"+target_class+">.   ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract.  ?s dcat:resource_identifier  ?uid. "+set_1_txt+" "+set_2_txt+" "+" FILTER (lang(?abstract) = 'en') } ORDER BY ASC(?uid) LIMIT "+str(limit)+" OFFSET "+str(offset)
   # print(query)
    #query="PREFIX dbo: <http://dbpedia.org/ontology/> select ?s ?a "+var_1_txt+" where { ?s a <"+target_class+">.  "+set_1_txt+" "+set_2_txt+"} LIMIT """+str(limit)
    #print(query)
    results=get_sparql_dataframe(sparql_ep, query)
    return results

def cleanUUUIDClassEntities(targetClass, sparql_ep):
    query='''
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        DELETE {
            ?s dcat:resource_identifier ?u1
        }
        WHERE { 
            ?s a <'''+targetClass+'''>. ?s dcat:resource_identifier ?u1 
        }
        '''
    
    results=ct.sparql_service_update(sparql_ep, query) 
    
    return "OK"


def get_sample_to_update(target_class, prop_all,sparql_ep, limit=10, offset=0):
    #target_class=type_triples
    #prop_all=prop_focus
    set_all=set(prop_all)
    
    idx=0
    set_1_txt=""
    var_1_txt=""
    for prop in set_all:
        simply=ts.getSimplifiedProp(prop)
        set_1_txt+=" OPTIONAL {?s <"+prop+"> ?"+simply+". }."
        var_1_txt+=" ?"+simply
        idx+=1
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract "+var_1_txt+" from <urn:x-arq:DefaultGraph>  where { ?s a <"+target_class+">.  ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. ?s dcat:resource_identifier  ?uid. "+set_1_txt+" FILTER (lang(?abstract) = 'en') } ORDER BY ASC(?uid) LIMIT """+str(limit)+" OFFSET "+str(offset)
    
    results=get_sparql_dataframe(sparql_ep, query)
    return results


def get_sampleNG_to_updateOnlyNew(ng, found_ng, sparql_ep, limit=10, offset=0):
    # target_class=type_triples
    # prop_all=prop_focus

    #  sample=  cs.get_sampleNG_to_update(infered_data_ng,sparql_ep,limit, offset)
    query = "PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?p ?o  FROM <" + ng + "> {  ?s ?p ?o. FILTER  EXISTS { GRAPH  <http://ns.inria.fr/kstor/wikinew_202004/> { ?s ?pi ?oi } }.     FILTER NOT EXISTS { GRAPH  <" + found_ng + "> { ?s ?p ?o }  } } ORDER BY ASC(?s) LIMIT """ + str(
        limit) + " OFFSET " + str(offset)

    results = get_sparql_dataframe(sparql_ep, query)
    return results


def get_sampleNG_to_update(ng,found_ng, sparql_ep, limit=10, offset=0):
    #target_class=type_triples
    #prop_all=prop_focus
    
  #  sample=  cs.get_sampleNG_to_update(infered_data_ng,sparql_ep,limit, offset)
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?p ?o  FROM <"+ng+"> {  ?s ?p ?o.     FILTER NOT EXISTS { GRAPH  <"+found_ng+"> { ?s ?p ?o }  } } ORDER BY ASC(?s) LIMIT """+str(limit)+" OFFSET "+str(offset)

    results=get_sparql_dataframe(sparql_ep, query)
    return results

def get_SampleEntUris(ng_sample,sparql_ep):

    query="Select DISTINCT ?s FROM <"+ng_sample+"> {  ?s ?p ?n. ?n rdf:value ?o. } "

    print(ng_sample)
    results=get_sparql_dataframe(sparql_ep, query)
    print(results)
    return list(results["s"])

def get_SampleEntUrisProp(ng_sample,prop,sparql_ep):

    query="Select DISTINCT ?s FROM <"+ng_sample+"> {  ?s <"+prop+"> ?o. } "

    print(ng_sample)
    results=get_sparql_dataframe(sparql_ep, query)
    print(results)
    return list(results["s"])

def get_SampleALLUriSynth(ng_sample,sparql_ep):

    query="PREFIX prov: <http://www.w3.org/ns/prov#>  Select DISTINCT ?u0 ?u1 ?abs FROM <"+ng_sample+"> {  ?u0 prov:wasDerivedFrom  ?u1. ?u0 <http://www.w3.org/2000/01/rdf-schema#comment> ?abs.  } "

    results=get_sparql_dataframe(sparql_ep, query)

    return results

def get_SampleENtUriSynth(ng_sample,sparql_ep):

    query="PREFIX prov: <http://www.w3.org/ns/prov#>  Select DISTINCT ?u0 ?u1 FROM <"+ng_sample+"> {  ?u0 prov:wasDerivedFrom  ?u1 } "

    results=get_sparql_dataframe(sparql_ep, query)

    return results

def get_SampleData(ent_uri,ng_sample,sparql_ep):

    query="Select ?s ?p ?o  FROM <"+ng_sample+"> {  <"+ent_uri+"> ?p ?n. ?n rdf:value ?o. } "

    results=get_sparql_dataframe(sparql_ep, query)

    return results

def get_SampleDataWC(ent_uri,ng_sample,sparql_ep):

    query="Select ?s ?p ?o  FROM <"+ng_sample+"> {  <"+ent_uri+"> ?p  ?o. } "

    results=get_sparql_dataframe(sparql_ep, query)

    return results

def get_SampleEntScores(ng_sample, ent_uri, p,type_prop, val,sparql_ep):
    if "dbo:" in type_prop:
        query=" PREFIX ks: <http://ns.inria.fr/kstor/#>  Select ?tc ?xnli FROM <"+ng_sample+"> {  <"+ent_uri+"> <"+p+"> ?n. ?n rdf:value <"+val+"'>. ?n ks:xnli ?xnli. ?n ks:triplet_critic ?tc. } "
    else:
        query=" PREFIX ks: <http://ns.inria.fr/kstor/#>  Select ?tc ?xnli FROM <"+ng_sample+"> {  <"+ent_uri+"> <"+p+"> ?n. ?n rdf:value '"+val+"'^^"+type_prop+". ?n ks:xnli ?xnli. ?n ks:triplet_critic ?tc. } "
    print(query)
    results=get_sparql_dataframe(sparql_ep, query)
    return results

def get_SampleEntData(ng_sample, ent_uri,sparql_ep):

    query="Select ?p ?o FROM <"+ng_sample+"> {  <"+ent_uri+"> ?p ?n. ?n rdf:value ?o. } "
          
    results=get_sparql_dataframe(sparql_ep, query)
    return results
            
def get_abstract(ent_uri,sparql_ep):
    #target_class=type_triples
    #prop_all=prop_focus
    
  #  sample=  cs.get_sampleNG_to_update(infered_data_ng,sparql_ep,limit, offset)
   

    url = unquote(ent_uri)

    query="SELECT   ?abstract FROM  <urn:x-arq:DefaultGraph>  WHERE {  <"+url+"> <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. } "
    #query="SELECT   ?p ?o FROM  <urn:x-arq:DefaultGraph>  WHERE {  <"+ent_uri+"> ?p ?o } "

    results=get_sparql_dataframe(sparql_ep, query)
    return results


def get_abstractMD(ent_uri, wiki_md_ng,sparql_ep):
    # target_class=type_triples
    # prop_all=prop_focus

    #  sample=  cs.get_sampleNG_to_update(infered_data_ng,sparql_ep,limit, offset)

    url = unquote(ent_uri)

    query = "SELECT   ?abstract FROM  <"+wiki_md_ng+">  WHERE {  <" + url + "> <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. } "
    # query="SELECT   ?p ?o FROM  <urn:x-arq:DefaultGraph>  WHERE {  <"+ent_uri+"> ?p ?o } "

    results = get_sparql_dataframe(sparql_ep, query)
    return results

def get_abstract_ngSynth(ent_uri, uri_orig,ng, sparql_ep):
    # target_class=type_triples
    # prop_all=prop_focus

    #  sample=  cs.get_sampleNG_to_update(infered_data_ng,sparql_ep,limit, offset)

    url = unquote(ent_uri)
    query ="PREFIX prov: <http://www.w3.org/ns/prov#>  Select  ?abstract  FROM <"+ng+"> {  <" + ent_uri + "> prov:wasDerivedFrom  <" + uri_orig + "> . <" + ent_uri + "> <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. } "

    # query="SELECT   ?p ?o FROM  <urn:x-arq:DefaultGraph>  WHERE {  <"+ent_uri+"> ?p ?o } "

    results = get_sparql_dataframe(sparql_ep, query)
    return results

def get_abstract_ng(ent_uri,ng, sparql_ep):
    # target_class=type_triples
    # prop_all=prop_focus

    #  sample=  cs.get_sampleNG_to_update(infered_data_ng,sparql_ep,limit, offset)

    url = unquote(ent_uri)

    query = "SELECT   ?abstract FROM  <"+ng+">  WHERE {  <" + url + "> <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. } "
    # query="SELECT   ?p ?o FROM  <urn:x-arq:DefaultGraph>  WHERE {  <"+ent_uri+"> ?p ?o } "

    results = get_sparql_dataframe(sparql_ep, query)
    return results


def get_FoundNgData(ent_uri,found_ng,sparql_ep):
      query="SELECT ?s ?p ?o FROM <"+found_ng+"> {    <"+ent_uri+">  ?p ?o. } "

      results=get_sparql_dataframe(sparql_ep, query)
      return results

def getCorrectedNgData(ent_uri,annotation_ng,sparql_ep):
      query="SELECT ?s ?p ?o FROM <"+annotation_ng+"> {    <"+ent_uri+">  ?p ?n. ?n rdf:value ?o. }"

      results=get_sparql_dataframe(sparql_ep, query)
      return results
    
def get_NamedGraphData(ent_uri,named_graph, prop_all,sparql_ep, limit=10, offset=0):
    #target_class=type_triples
    #prop_all=prop_focus
    set_all=set(prop_all)
    
    idx=0
    set_1_txt=""
    var_1_txt=""
    for prop in set_all:
        simply=ts.getSimplifiedProp(prop)
        set_1_txt+=" OPTIONAL {?s <"+prop+"> ?"+simply+". }."
        var_1_txt+=" ?"+simply
        idx+=1
     
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  select "+var_1_txt+" from <"+named_graph+"> where { OPTIONAL {?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract.}. "+set_1_txt+"} "
    query=query.replace("?s","<"+ent_uri+">")
    #print("__________________________")
    #print(query)
    results=get_sparql_dataframe(sparql_ep, query)
    return results


def get_NamedGraphDataRangeOk(ent_uri, named_graph, prop_all_typed, sparql_ep):
    # target_class=type_triples
    # prop_all=prop_focus
    #set_all = set(prop_all)

    idx = 0
    set_1_txt = ""
    var_1_txt = ""

    for prop in prop_all_typed.keys():
        simply = ts.getSimplifiedProp(prop)
        if("dbo:" in prop_all_typed[prop]):
            #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            set_1_txt += " OPTIONAL {$?s$ <" + prop + "> ?" + simply + ". ?" + simply + " a "+prop_all_typed[prop]+". }."
            var_1_txt += " ?" + simply
            idx += 1
        else:
            set_1_txt += " OPTIONAL {$?s$ <" + prop + "> ?" + simply + ". }."
            var_1_txt += " ?" + simply
            idx += 1
    #print("========")
    #print(var_1_txt)
    #print(set_1_txt)
    query = "PREFIX dbo: <http://dbpedia.org/ontology/>  select " + var_1_txt + " from <" + named_graph + "> where {  " + set_1_txt + " } "

    query = query.replace("$?s$", "<" + ent_uri + ">")
    #print(query)
    results = get_sparql_dataframe(sparql_ep, query)

    return results

def get_RandomSample_K(target_class, prop_all,sparql_ep, limit=10, offset=0):
    #target_class=type_triples
    #prop_all=prop_focus
    set_all=set(prop_all)
    
    idx=0
    set_1_txt=""
    var_1_txt=""
    for prop in set_all:
        simply=ts.getSimplifiedProp(prop)
        set_1_txt+=" OPTIONAL {?s <"+prop+"> ?"+simply+". }."
        var_1_txt+=" ?"+simply
        idx+=1
       
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract "+var_1_txt+" where { ?s a <"+target_class+">.  ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. ?s dcat:resource_identifier  ?uid. "+set_1_txt+" FILTER (lang(?abstract) = 'en') } ORDER BY ASC(?uid) LIMIT """+str(limit)+" OFFSET "+str(offset)
  
    results=get_sparql_dataframe(sparql_ep, query)
    return results


def get_RandomSample_NG(target_class, prop_all,sparql_ep, limit=10, offset=0):
    #target_class=type_triples
    #prop_all=prop_focus
    set_all=set(prop_all)
    
    idx=0
    set_1_txt=""
    var_1_txt=""
    for prop in set_all:
        simply=ts.getSimplifiedProp(prop)
        set_1_txt+=" OPTIONAL {?s <"+prop+"> ?"+simply+". }."
        var_1_txt+=" ?"+simply
        idx+=1
       
    query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#> select ?s ?abstract "+var_1_txt+" where { ?s a <"+target_class+">.  ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. ?s dcat:resource_identifier  ?uid. "+set_1_txt+" FILTER (lang(?abstract) = 'en') } ORDER BY ASC(?uid) LIMIT """+str(limit)+" OFFSET "+str(offset)
  
    results=get_sparql_dataframe(sparql_ep, query)
    return results

def CreateUUIDClassEntities(target_class, sparql_ep):
    
    sparql = SPARQLWrapper(sparql_ep)   
    q1="PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#> select  (COUNT(DISTINCT ?s) as ?nb)  where { ?s a <"+target_class+">;  <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. filter not exists {?s dcat:resource_identifier ?u1 . }. FILTER (lang(?abstract) = 'en') } "

    sparql.setQuery(q1)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_to_annotate=int(qres["results"]["bindings"][0]["nb"]["value"])
    
    print("=============== WILL ANNOTATE :" ,nb_to_annotate)
    offset=0
    limit=10000
    if( nb_to_annotate>0):
        nb_loop=0
        
        while offset<nb_to_annotate :
            
            print(">>>>>>>>>>>>>>>>>>>>>LOOP :" ,nb_loop)
          
            query = '''
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX dcat: <http://www.w3.org/ns/dcat#>
                INSERT
                { 
                        ?s  dcat:resource_identifier ?random. 
                        }
                WHERE{
                    
                        select DISTINCT ?s ?random
                        WHERE { 
                            ?s a <'''+target_class+'''>;  <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. filter not exists {?s dcat:resource_identifier ?u2 . }. 
                            BIND(RAND() AS ?random). FILTER (lang(?abstract) = 'en') 
                               } 
                         GROUP BY ?s ORDER BY ?random LIMIT '''+str(limit)+''' OFFSET '''+str(offset)+'''
                  
                    
                }
                '''
            results=ct.sparql_service_update(sparql_ep, query)    
            offset=offset+limit
            nb_loop+=1
        return "Done"
    else:
        return "Already Done"


def CreateUUIDClassEntities2(target_class,class_ns, sparql_ep,from_scratch=False):
    sparql = SPARQLWrapper(sparql_ep)
    if(from_scratch==True):
        query_drop="DROP GRAPH  <" + class_ns + ">"
        sparql.setMethod(POST)
        sparql.setRequestMethod(POSTDIRECTLY)
        sparql.setQuery(query_drop)
        sparql.query()
    q1 = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX dcat: <http://www.w3.org/ns/dcat#> select  (COUNT(DISTINCT ?s) as ?nb)  FROM  <urn:x-arq:DefaultGraph> where { ?s a <" + target_class + ">; <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. FILTER (lang(?abstract) = 'en'). FILTER NOT EXISTS {GRAPH <"+class_ns+"> { ?s dcat:resource_identifier ?u1. } } }"
    print(q1)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(q1)

    qres = sparql.query().convert()

    print(qres)
    print("HEY")
    nb_to_annotate = int(qres["results"]["bindings"][0]["nb"]["value"])

    print("=============== WILL ANNOTATE :", nb_to_annotate)
    #sys.exit()
    offset = 0
    limit = 10000
    if (nb_to_annotate > 0):
        nb_loop = 0

        while offset < nb_to_annotate:
            print(">>>>>>>>>>>>>>>>>>>>>LOOP :", nb_loop)

            query = '''
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX dcat: <http://www.w3.org/ns/dcat#>
                INSERT
                { GRAPH <'''+class_ns+'''> {
                            ?s  dcat:resource_identifier ?random. 
                    }
                }
                WHERE{

                        select DISTINCT ?s ?random
                        WHERE { 
                            ?s a <''' + target_class + '''>;  <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract. 
                            filter not exists {GRAPH <'''+class_ns+'''> {?s dcat:resource_identifier ?u2.}  }.
                            BIND(RAND() AS ?random). FILTER (lang(?abstract) = 'en') 
                               } 
                         GROUP BY ?s ORDER BY ?random LIMIT ''' + str(limit) + ''' OFFSET ''' + str(offset) + '''


                }
                '''
            results = ct.sparql_service_update(sparql_ep, query)
            offset = offset + limit
            nb_loop += 1
        return "Done"
    else:
        return "Already Done"

