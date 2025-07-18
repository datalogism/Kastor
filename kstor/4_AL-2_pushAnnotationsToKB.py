#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 10:35:40 2024

"""

from rdflib import Graph
import pandas as pd

############## USEFULL FUCNTIONS

import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct
import src.class_signatures as cs

import src.NLI_TripletCritic as llm_eval

from argparse import ArgumentParser
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-annot", "--annotation_file", default=1200)
    parser.add_argument("-samp", "--sample_name", default=None)
    args = parser.parse_args()
    if args.shape_file_path and args.annotation_file and args.sample_name:
        shape = Graph()
        shape.parse(args.shape_file_path)
        sparql_ep = 'http://localhost:8080/sparql'
        print(">>>>>>>>>>>>>>>>>>>>>>>>>> START HERE")
        annotation_ng_base = "http://ns.inria.fr/kstor/annotated_samples/"
        samples_ng_base = "http://ns.inria.fr/kstor/samples/"
        sample_name =  args.sample_name
        sample_ng= samples_ng_base+sample_name
        annotation_ng= annotation_ng_base+sample_name
        annotation_file = args.annotation_file

        # "uniform" / "inverse freq sampl"
        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real = {}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)] = p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)

        ## CLEAR SAMPLE
        query="SELECT * FROM <"+annotation_ng+"> {?s ?p ?o} LIMIT 10"
        res=ct.get_sparql_dataframe(sparql_ep,query)
        print(res)
        query="PREFIX ks: <http://ns.inria.fr/kstor/#> DROP GRAPH <"+annotation_ng+">"
        res=ct.sparql_service_update(sparql_ep,query)

        query="SELECT * FROM <"+annotation_ng+"> {?s ?p ?o} LIMIT 10"
        res=ct.get_sparql_dataframe(sparql_ep,query)
        print(res)

        SAMPLE_orig={}
        list_uri=cs.get_SampleEntUris(sample_ng,sparql_ep)
        for uri in list_uri:

            uri_clean=rs.cleanEntURL(uri)
            triples=cs.get_SampleEntData(sample_ng,uri_clean,sparql_ep)
            if(len(triples)>0):
                SAMPLE_orig[uri_clean]={}
                for index, row in triples.iterrows():
                    p=row["p"]
                    if(p not in SAMPLE_orig[uri_clean].keys()):
                        SAMPLE_orig[uri_clean][p]=[]
                    val2=str(row["o"])


                    if("Year" in p):
                        val2=val2[0:4]

                    SAMPLE_orig[uri_clean][p].append(val2)
            else:
                print("PB WITH ",uri_clean)

        #print(list_uri)
        file_new_art = pd.read_csv(annotation_file)
        corrections={}
        for index, row in file_new_art.iterrows():
            uri=row["ent_uri"]

            uri_clean=rs.cleanEntURL(uri)
            if(uri_clean in SAMPLE_orig.keys()):
                print("find")
                if(uri_clean not in corrections.keys()):

                    corrections[uri_clean]={"to_add":{},"to_delete":{}}

                real_p=dict_simply_real[row["pred"]]

                type_annot=row["type"]

                if("FP" in type_annot and str(row["verif"]).strip().upper()=="TRUE" and str(row["found"]).strip().upper()=="TRUE"):
                    if(real_p not in corrections[uri_clean]["to_add"].keys()):
                        corrections[uri_clean]["to_add"][real_p]=[]
                    corrections[uri_clean]["to_add"][real_p].append(row["val_pred"])
                if("FN" in type_annot and str(row["verif"]).strip().upper()=="FALSE"):
                    print("'HEY",uri_clean)
                    if(real_p not in corrections[uri_clean]["to_delete"].keys()):
                        corrections[uri_clean]["to_delete"][real_p]=[]
                    corrections[uri_clean]["to_delete"][real_p].append(row["val_gold"])
            else:
                print("PB with", uri_clean)

        for k in SAMPLE_orig.keys():
           # k="http://dbpedia.org/resource/Abel_Buell"
            orig=SAMPLE_orig[k].copy()
            to_delete={}
            to_add={}
            if(k in corrections.keys()):
                print("CORRECTIONS")
                to_delete=corrections[k]["to_delete"]
                #print(to_delete)
                to_add=corrections[k]["to_add"]


                #print(">>>>>>>>>>>>>> ORIG>",len(orig))
                #print(">>>>>>>>>>>>>> TEMPO SCORED>",len(tempo_scored))

            else:
                print("NO CORRECTIONS")

            corrected=[]
            for p in orig.keys():
                values=orig[p]
                for val in values:
                    val2=str(val)


                    if("Year" in p):
                        val2=val2[0:4]
                    if(p not in to_delete.keys()):
                        corrected.append({"prop":p,"val":val2})
                    elif(val not in to_delete[p]):
                        corrected.append({"prop":p,"val":val2})
                    else:
                        print("TODELETE")

            tempo_scored=[]
            for tempo in corrected:
                type_prop_c=type_prop[tempo["prop"]]
                val=tempo["val"]
                if('"' in val or "'" in val):
                        val = val.translate(str.maketrans({"'":  r"\'",
                                  '"': r'\"'}))
                results=cs.get_SampleEntScores(sample_ng,k,tempo["prop"],type_prop_c,val,sparql_ep)
                if(len(results)>0):
                    print("HEY")
                    tempo2=tempo
                    tempo2["tc"]=float(results["tc"])
                    tempo2["xnli"]=float(results["xnli"])
                    tempo_scored.append(tempo2)

                else:
                    print("PB with scores of ",k)
                    print(tempo["prop"],">",val)
                    abstract=cs.get_abstract(k,sparql_ep)
                    abstract=str(abstract["abstract"][0])
                    temp_data={"ent_uri": k,"prop":tempo["prop"],"value":val,"abstract":abstract}
                    triplet_critic=llm_eval.getTripletCritic_proba(temp_data)
                    xnli=llm_eval.get_XNLI_proba(temp_data)
                    tempo2={"prop":tempo["prop"],"val":val,"xnli":xnli,"tc":triplet_critic}
                    tempo_scored.append(tempo2)

            for p in to_add.keys():

                abstract=cs.get_abstract(k,sparql_ep)
                abstract=str(abstract["abstract"][0])
                for val in to_add[p]:
                    temp_data={"ent_uri": k,"prop":p,"value":val,"abstract":abstract}
                    triplet_critic=llm_eval.getTripletCritic_proba(temp_data)
                    xnli=llm_eval.get_XNLI_proba(temp_data)
                    tempo2={"prop":p,"val":val,"xnli":xnli,"tc":triplet_critic}
                    tempo_scored.append(tempo2)
            idx=0
            for triple in tempo_scored:
                val=triple["val"]
                if('"' in val or "'" in val):
                        val = val.translate(str.maketrans({"'":  r"\'",
                                  '"': r'\"'}))
                query="PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <"+annotation_ng+"> { <"+k+"> <"+triple["prop"]+"> _:n"+str(idx)+". _:n"+str(idx)+" rdf:value '"+val+"'^^"+type_prop[triple["prop"]]+". _:n"+str(idx)+" ks:triplet_critic '"+str(triple["tc"])+"'^^xsd:float  . _:n"+str(idx)+" ks:xnli '"+str(triple["xnli"])+"'^^xsd:float  }}"
                idx += 1
                #print(query)
                res=ct.sparql_service_update(sparql_ep,query)

        query="SELECT  (COUNT(DISTINCT ?s) as ?nb) FROM <"+annotation_ng+"> {?s ?p ?n. ?n rdf:value ?o.}"
        res=ct.get_sparql_dataframe(sparql_ep,query)
        print(res)


