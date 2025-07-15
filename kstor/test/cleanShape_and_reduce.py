import sys
from rdflib import Graph
sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/kstor/')
import  src.abstractExtended as ae
import src.corese_tools as ct
import src.corese_tools as ct
import src.triple_shapes as ts

sparql_ep = 'http://localhost:8080/sparql'
shape_file="/user/cringwal/home/PycharmProjects/Kastor/shapes/txt2kg/WrittenWorkShapeTXT2KG_clean.ttl"
shape = Graph()
shape.parse(shape_file)

print(">>>>>>>>>>>>>>>>>>> SHAPE BEFORE CLEANING")
print(shape.serialize( format="ttl"))
type_triples = ts.getShapeType(shape)


type_prop = ts.getShapePropWithType(shape)


notfound_prop=[]
for k in type_prop.keys():
    query = """ SELECT (COUNT(?s) as ?nb_g) FROM <urn:x-arq:DefaultGraph>
                        WHERE {
                            ?s a <"""+type_triples+""">.
                            ?s <"""+k+"""> ?o.
                        }"""
    results = ct.get_sparql_dataframe(sparql_ep, query)
    nb=int(results["nb_g"])
    print(k,">",nb)
    if(nb<100):
        print("NOT FOUND")
        notfound_prop.append(k)

for prop_notf in notfound_prop:
        shape.update("""   Prefix sh: <http://www.w3.org/ns/shacl#> 
                           DELETE {
                                ?s sh:property ?bn.
                               ?bn sh:path <"""+prop_notf+""">.
                               ?bn ?p ?j.
                               } 
                           WHERE {
                               ?s sh:property ?bn.
                               ?bn sh:path <"""+prop_notf+""">.
                               ?bn ?p ?j.
                           }""")

print(">>>>>>>>>>>>>>>>>>> SHAPE AFTER CLEANING")

path_w = shape_file.replace(".ttl","_reduced.ttl")
with open(path_w, mode='w') as f:
    f.write(shape.serialize( format="ttl"))