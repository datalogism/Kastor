from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/kstor/src/')
import  abstractExtended as ae

def get_SubjectsToRetrieveWithID(sparql_ep,search_ng,current_ng,limit):

    sparql = SPARQLWrapper(sparql_ep)
    query = "PREFIX dcat: <http://www.w3.org/ns/dcat#> select  ?s ?id FROM <" + search_ng + "> WHERE  {   ?s dcat:resource_identifier  ?uid. ?s <http://dbpedia.org/ontology/wikiPageRevisionID> ?id. FILTER NOT EXISTS { GRAPH  <" + current_ng + "> { ?s ?p ?o }  } } ORDER BY ASC(?uid) LIMIT " + str(limit)
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [{"subj":row["s"]["value"],"id":row["id"]["value"]} for row in qres["results"]["bindings"]]
    return subjects

wikipedia_agent = "(https://datalogism.github.io/; celian.ringwald@inria.fr) Inria"
sparql_ep = 'http://localhost:8080/sparql'
search_ng = "urn:x-arq:DefaultGraph"
current_ng = "http://ns.inria.fr/kstor/#wiki_md_init"
limit = 5
test_list=get_SubjectsToRetrieveWithID(sparql_ep,search_ng,current_ng,limit)
for ent in test_list:
    entity_splm=ent["subj"].replace('http://dbpedia.org/resource/','').replace('https://dbpedia.org/resource/','')
    print("before")
    md_entity=ae.getAbstractMD2(entity_splm,ent["id"], wikipedia_agent)
    print(md_entity)