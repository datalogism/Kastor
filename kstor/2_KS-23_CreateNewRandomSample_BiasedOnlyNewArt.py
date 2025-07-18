#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 10:35:40 2024

"""

from rdflib import Graph
from argparse import ArgumentParser

import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct
import src.class_signatures as cs
import src.NLI_TripletCritic as llm_eval
import sys
from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
from SPARQLWrapper import get_sparql_dataframe


def get_RandomSample_NG_EntAbsMDNew(sparql_ep, abstract_ng, wikichecked_ng,class_id_ng, limit=10, offset=0):
    query = '''PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX dcat: <http://www.w3.org/ns/dcat#>
     select ?s ?abstract FROM  <'''+abstract_ng+'''>  where {
           ?s <http://www.w3.org/2000/01/rdf-schema#comment> ?abstract.
          { GRAPH  <'''+class_id_ng+'''> { ?s dcat:resource_identifier  ?uid} }.
          
          FILTER  EXISTS { GRAPH  <''' + wikichecked_ng + '''> { ?s ?p ?o } }.
          FILTER  EXISTS { GRAPH  <http://ns.inria.fr/kstor/wikinew_202004/> { ?s ?p ?o } }
     } ORDER BY ASC(?uid) LIMIT ''' + str(
        limit) + " OFFSET " + str(offset)

    results = get_sparql_dataframe(sparql_ep, query)

    return results
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-sz", "--size_sample", default=1200)
    parser.add_argument("-es", "--existing_sample", default=None)
    ## EXISTING SAMPLE MUST LOOK LIKE
    # "http://ns.inria.fr/kstor/samples/sample_0"
    # TO DO CHOICE OF THE DISTRIBUTION
    # "uniform" / "inverse freq sampl"
    args = parser.parse_args()

    print("HEY")
    if args.shape_file_path and args.size_sample:
        shape = Graph()
        shape.parse(args.shape_file_path)

        sparql_ep = 'http://localhost:8080/sparql'
        #search_ng = args.searchspace_namedgraph


        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real={}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)]=p

        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)

        list_obj_prop=[ k for k in type_prop.keys() if "dbo:" in type_prop[k]]
        list_dt_prop=[ k for k in type_prop.keys() if "dbo:" not in type_prop[k]]

        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")

        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        class_id_ng =  "http://ns.inria.fr/kstor/class_randoms_id/" + type_triples_name
        found_ng = "http://ns.inria.fr/kstor/wikichecked/" + shape_name + "/abtract_md"
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name

        size_sample=int(args.size_sample)
        existing_sample=None
        #existing_sample="http://ns.inria.fr/kstor/samples/PersonShape_dp/abtract_md/only_new_sample_0"
        ####################### REVOIR INTEGRATION NAMED GRAPH PRECEDANT
        other_samples=[]
        if(existing_sample==None):
            ########## SAMPLE NAME
            query='SELECT DISTINCT ?g  {  GRAPH ?g {}}'
            results=ct.get_sparql_dataframe(sparql_ep, query)
            existing_ng=list(results['g'])
            sample_ng="http://ns.inria.fr/kstor/samples/" + shape_name + "/abtract_md"
           # new = "http://ns.inria.fr/kstor/samples/" + shape_name + "/abtract_md/sample_"

            for ng_ in existing_ng:
                if(sample_ng in ng_):
                    other_samples.append(ng_)

            idx=len(other_samples)

            while("http://ns.inria.fr/kstor/samples/" + shape_name + "/abtract_md/only_new_sample_"+str(idx) in other_samples):
                idx+=1
            sample_ng="http://ns.inria.fr/kstor/samples/" + shape_name + "/abtract_md/only_new_sample_"+str(idx)
        else:
            sample_ng=existing_sample
        print("================================ CURRENT SAMPLE :",sample_ng)
        print("other samples:",other_samples)

        done_list=cs.get_Exlude_Ent_NG(other_samples,sparql_ep)

        #
        ## CLEAR SAMPLE
       # sample_ng="http://ns.inria.fr/kstor/samples/"
       # query="SELECT * FROM <"+sample_ng+"> {?s ?p ?o} LIMIT 10"
        #res=ct.get_sparql_dataframe(sparql_ep,query)
        #sample_ng="http://ns.inria.fr/kstor/samples/sample_0"
        #query="PREFIX ks: <http://ns.inria.fr/kstor/#> DROP GRAPH <"+sample_ng+">"
        #res=ct.sparql_service_update(sparql_ep,query)
        #sample_ng="http://ns.inria.fr/kstor/samples/sample_1"
        #query = "PREFIX ks: <http://ns.inria.fr/kstor/#> DROP GRAPH <" + sample_ng + ">"
        #res = ct.sparql_service_update(sparql_ep, query)
        #sys.exit()
        limit=size_sample
        offset=0

        query="SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+sample_ng+"> WHERE {?s ?p ?n. ?n rdf:value ?o. }"
        SAMPLE_len=ct.sparql_service_to_int(sparql_ep, query)

        while(size_sample!=SAMPLE_len):
            print("============+>",SAMPLE_len,"/",size_sample)
            results=get_RandomSample_NG_EntAbsMDNew(sparql_ep, abstract_ng, found_ng, class_id_ng, limit, offset)
            list_current_uri=[]
            for idx, row in results.iterrows():
                uri = rs.cleanEntURL(row["s"])
                abstractMD = row["abstract"].strip()
                abs_data = cs.get_abstract(uri, sparql_ep)
                abstract = str(abs_data["abstract"][0]).strip()
                if (uri not in done_list
                        and SAMPLE_len < size_sample
                        and len(abstract) > 10
                        and len(abstractMD) > 10):
                    query="PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <"+found_ng+"> { <"+uri+"> ?p ?o. }"
                    res=ct.get_sparql_dataframe(sparql_ep,query)
                    #print(res)
                    if (len(list_dt_prop) > 0 and len(list_obj_prop) > 0):
                        res2 = res.copy()
                        local_prop = []
                        for index, row2 in res2.iterrows():
                            local_prop.append(row2["p"])
                        found_op = [a for a in local_prop if a in list_obj_prop]
                    else:
                        found_op = [None]
                    if (len(found_op) > 0):
                        for index, row2 in res.iterrows():
                            #print(row2)
                            real_prop=row2["p"]

                            if(real_prop in type_prop.keys()):
                                val=str(row2["o"])
                                if (row["s"] not in list_current_uri):
                                    SAMPLE_len += 1
                                    list_current_uri.append(row["s"])

                                val=rs.cleanTxt(val)

                                if ('"' in val or "'" in val or "\\" in val):
                                    val = val.translate(str.maketrans({"'": r"\'", '"': r'\"', "\\": "\\\\"}))

                                if("Year" in real_prop and "-" in str(val)):
                                    val=str(val).split("-")[0][0:4]


                                simply=ts.getSimplifiedProp(p)
                                uri_base=uri.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")
                                val_look=val.replace("_"," ")
                                temp={"ent_uri": uri_base,"prop":simply,"value":val_look,"abstract":abstract}
                                triplet_critic=llm_eval.getTripletCritic_proba(temp)
                                xnli=llm_eval.get_XNLI_proba(temp)
                                if ("dbo:" not in type_prop[real_prop] and "dbpedia.org" not in type_prop[real_prop]):
                                    query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + sample_ng + "> { <" + uri + "> <" + real_prop + "> _:n" + str(
                                        index) + ". _:n" + str(index) + " rdf:value '" + val + "'^^" + type_prop[
                                                real_prop] + ". _:n" + str(index) + " ks:triplet_critic '" + str(
                                        triplet_critic) + "'^^xsd:float  . _:n" + str(index) + " ks:xnli '" + str(
                                        xnli) + "'^^xsd:float  }}"

                                else:
                                    query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + sample_ng + "> { <" + uri + "> <" + real_prop + "> _:n" + str(
                                        index) + ". _:n" + str(index) + " rdf:value <" + val + "> . _:n" + str(
                                        index) + " ks:triplet_critic '" + str(
                                        triplet_critic) + "'^^xsd:float  . _:n" + str(index) + " ks:xnli '" + str(
                                        xnli) + "'^^xsd:float  }}"

                                res = ct.sparql_service_update(sparql_ep, query)
                else:
                    print(uri,"in DONE")
            offset+=limit
            query="SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+sample_ng+"> WHERE {?s ?p ?n. ?n rdf:value ?o}"
            SAMPLE_len=ct.sparql_service_to_int(sparql_ep, query)
            print("======================>",SAMPLE_len)
            #SAMPLE_len=int(SAMPLE_len["nb"])

        print("TOTAL PERSONB NG>",)
        print(results)

        query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT ?p (COUNT(DISTINCT ?s) as ?nb_ent) (AVG(?tc) as ?tc_avg) (AVG(?xnli) as ?xnli_avg) FROM <"+sample_ng+"> WHERE { ?s ?p ?n. ?n rdf:value ?o. ?n ks:triplet_critic ?tc. ?n ks:xnli ?xnli } GROUP BY ?p "
        results=ct.get_sparql_dataframe(sparql_ep, query)
        print("TOTAL PERSONB NG>",)
        print(results)
