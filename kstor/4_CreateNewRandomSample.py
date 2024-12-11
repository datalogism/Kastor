#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 10:35:40 2024

@author: cringwal
"""

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

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-ng", "--searchspace_namedgraph", default="http://ns.inria.fr/kstor/#dates_inferenced")
    parser.add_argument("-sz", "--size_sample", default=1200)
    # LATTER
    # "uniform" / "inverse freq sampl"
    args = parser.parse_args()

    if args.shape_file_path and args.searchspace_namedgraph and args.size_sample:
        shape = Graph()
        shape.parse(args.shape_file_path)

        sparql_ep = 'http://localhost:8080/sparql'
        search_ng = args.searchspace_namedgraph
        found_ng = "http://ns.inria.fr/kstor/#found_in_abtract"


        print(">> get usefull data")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real={}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)]=p
        type_prop = ts.getShapePropWithType(shape)
        type_triples = ts.getShapeType(shape)

        size_sample=int(args.size_sample)
        existing_sample=None
        #"http://ns.inria.fr/kstor/samples/sample_0"
        ####################### REVOIR INTEGRATION NAMED GRAPH PRECEDANT
        other_samples=[]
        if(existing_sample==None):
            ########## SAMPLE NAME
            query='SELECT DISTINCT ?g  {  GRAPH ?g {}}'
            results=ct.get_sparql_dataframe(sparql_ep, query)
            existing_ng=list(results['g'])
            sample_ng="http://ns.inria.fr/kstor/samples/"
            for ng_ in existing_ng:
                if(sample_ng in ng_):
                    other_samples.append(ng_)
            idx=len(other_samples)
            while("http://ns.inria.fr/kstor/samples/sample_"+str(idx) in other_samples):
                idx+=1
            sample_ng="http://ns.inria.fr/kstor/samples/sample_"+str(idx)
        else:
            sample_ng=existing_sample

        print("================================ CURRENT SAMPLE :",sample_ng)
        print("other samples:",other_samples)
        done_list=cs.get_Exlude_Ent_NG(other_samples,sparql_ep)
        #
        ## CLEAR SAMPLE
        #sample_ng="http://ns.inria.fr/kstor/samples/sample_1"
       # sample_ng="http://ns.inria.fr/kstor/samples/"
       # query="SELECT * FROM <"+sample_ng+"> {?s ?p ?o} LIMIT 10"
        #res=ct.get_sparql_dataframe(sparql_ep,query)
        #query="PREFIX ks: <http://ns.inria.fr/kstor/#> DROP GRAPH <"+sample_ng+">"
        #res=ct.sparql_service_update(sparql_ep,query)

        limit=size_sample
        offset=0

        query="SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+sample_ng+"> WHERE {?s ?p ?n. ?n rdf:value ?o. }"
        SAMPLE_len=ct.sparql_service_to_int(sparql_ep, query)
        SAMPLE_len=int(SAMPLE_len["nb"])
        while(size_sample!=SAMPLE_len):
            print("============+>",SAMPLE_len,"/",size_sample)
            results=cs.get_RandomSample_NG_EntAbs(sparql_ep, limit, offset)
            list_current_uri=[]
            for idx, row in results.iterrows():
                print(idx)
                abstract=row["abstract"]
                uri=rs.cleanEntURL(row["s"])
                print(uri)
                if(uri not in done_list and SAMPLE_len<size_sample):
                    print(row["s"], "> NOT IN DONE")
                    query="PREFIX dbo: <http://dbpedia.org/ontology/>  select ?p ?o FROM <"+found_ng+"> { <"+uri+"> ?p ?o. }"
                    res=ct.get_sparql_dataframe(sparql_ep,query)

                    for index, row2 in res.iterrows():
                        real_prop=row2["p"]
                        val=str(row2["o"])
                        val=rs.cleanTxt(val)
                        if('"' in val or "'" in val):
                            val = val.translate(str.maketrans({"'":  r"\'",
                                      '"': r'\"'}))

                        if("Year" in real_prop):
                            val=val[0:4]
                        if(row["s"] not in list_current_uri):
                            SAMPLE_len+=1
                            list_current_uri.append(row["s"])
                        simply=ts.getSimplifiedProp(p)
                        uri_base=uri.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")
                        temp={"ent_uri": uri_base,"prop":simply,"value":val,"abstract":abstract}
                        triplet_critic=llm_eval.getTripletCritic_proba(temp)
                        xnli=llm_eval.get_XNLI_proba(temp)

                        query="PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <"+sample_ng+"> { <"+uri+"> <"+real_prop+"> _:n"+str(index)+". _:n"+str(index)+" rdf:value '"+val+"'^^"+type_prop[real_prop]+". _:n"+str(index)+" ks:triplet_critic '"+str(triplet_critic)+"'^^xsd:float  . _:n"+str(index)+" ks:xnli '"+str(xnli)+"'^^xsd:float  }}"
                        res=ct.sparql_service_update(sparql_ep,query)
                else:
                    print(uri,"in DONE")
            offset+=limit
            query="SELECT (COUNT(DISTINCT ?s) as ?nb) FROM <"+sample_ng+"> WHERE {?s ?p ?n. ?n rdf:value ?o}"
            SAMPLE_len=ct.sparql_service_to_int(sparql_ep, query)
            SAMPLE_len=int(SAMPLE_len["nb"])

        print("TOTAL PERSONB NG>",)
        print(results)

        query="PREFIX dbo: <http://dbpedia.org/ontology/>  PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT ?p (COUNT(DISTINCT ?s) as ?nb_ent) (AVG(?tc) as ?tc_avg) (AVG(?xnli) as ?xnli_avg) FROM <"+sample_ng+"> WHERE { ?s ?p ?n. ?n rdf:value ?o. ?n ks:triplet_critic ?tc. ?n ks:xnli ?xnli } GROUP BY ?p "
        results=ct.get_sparql_dataframe(sparql_ep, query)
        print("TOTAL PERSONB NG>",)
        print(results)
