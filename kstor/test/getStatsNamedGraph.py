import sys
sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/kstor/')
import  src.abstractExtended as ae
import src.corese_tools as ct

sparql_ep = 'http://localhost:8080/sparql'
query='SELECT DISTINCT ?g  {  GRAPH ?g {}}'
results=ct.get_sparql_dataframe(sparql_ep, query)
existing_ng=list(results['g'])
print(existing_ng)

for ng in existing_ng:
    if("CityShapeTXT2KG_clean" in ng):
        print(ng)

ng="http://ns.inria.fr/kstor/samples/CityShapeTXT2KG_clean/abtract_md/mix_sample_0"
query=""" SELECT (COUNT(?s) as ?nb_g)  (COUNT(DISTINCT ?s) as ?nb_e)  (COUNT(?p) as ?nb_p) FROM <"""+ng+""">
                    WHERE {
                        ?s ?p ?o.
                    }"""
results=ct.get_sparql_dataframe(sparql_ep, query)
print(results)
query=""" SELECT  (COUNT(DISTINCT ?s) as ?nb_e)   FROM <"""+ng+""">
                    WHERE {
                        ?s ?p ?o.
                    } """
results=ct.get_sparql_dataframe(sparql_ep, query)
print(results)
query=""" SELECT ?p  (COUNT(DISTINCT ?s) as ?nb_e)   FROM <"""+ng+""">
                    WHERE {
                        ?s ?p ?o.
                    } GROUP BY ?p"""
results=ct.get_sparql_dataframe(sparql_ep, query)
print(results)