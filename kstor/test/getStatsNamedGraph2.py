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
    if("MeanOfTransportationShapeTXT2KG_clean" in ng):
        print(ng)

ng="http://ns.inria.fr/kstor/samples/MeanOfTransportationShapeTXT2KG_clean/abtract_md/mix_sample_1"

query="Select (COUNT(DISTINCT ?s) as ?nb) FROM <"+ng+"> {  ?s ?p ?n. ?n rdf:value ?o. } "
results=ct.get_sparql_dataframe(sparql_ep, query)
print(results)
