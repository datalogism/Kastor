"""
1_KD-322_Wikicheck_md_dt_and_op.py

This script processes RDF shape files and checks for property values in Markdown abstracts of entities.
It compares property values from a knowledge graph with values found in entity abstracts,
and stores the results in a named graph for further analysis.

Key functionalities:
- Count entities that need processing
- Retrieve subjects for processing
- Get statistics about named graphs
- Wikicheck the data related to a given SHACL shape based on the MARKDOWN abstracts

Usage Example:
    python 1_KD-322_Wikicheck_md_dt_and_op.py \
        --shape_file "/path/to/shape_file.ttl" \
        --searchspace_namedgraph "http://example.org/target-graph"

Arguments:
    -s, --shape_file:     Path to the SHACL shape file (.ttl) defining the data structure
    -ng, --searchspace_namedgraph:      Named graph URI containing graph data to be processed

"""

from rdflib import Graph
from argparse import ArgumentParser

# Import local modules
import src.triple_shapes as ts
import src.rdf_synthax_fct as rs
import src.corese_tools as ct
import src.class_signatures as cs
from SPARQLWrapper import JSON, SPARQLWrapper



def getNbEntToDO(sparql_ep, found_ng, abstract_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = '''select  (COUNT(DISTINCT ?s) as ?nb)  FROM <''' + abstract_ng + '''> WHERE  {
        ?s ?p2 ?o. FILTER(?o != '' ).
       FILTER NOT EXISTS { 
       GRAPH  <''' + found_ng + '''> { ?s ?p ?o } 
        }
          }'''

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)


def get_SubjectsToRetrieve(sparql_ep, target_ng, found_ng, abstract_ng, limit, offset):
    sparql = SPARQLWrapper(sparql_ep)
    query = '''select  DISTINCT ?s  FROM <''' + abstract_ng + '''> WHERE  {
          ?s ?p2 ?o. FILTER(?o != '' ).
            } ORDER BY DESC(?s) LIMIT ''' + str(limit) + ''' OFFSET ''' + str(offset)
    # query = "select DISTINCT ?s FROM <"+target_ng+"> WHERE  { ?s ?p ?o. FILTER NOT EXISTS { GRAPH  <"+found_ng+"> { ?s ?p ?o }  } . FILTER EXISTS { GRAPH  <"+abstract_ng+"> { ?s ?p2 ?o2. FILTER(?o2 != '' ). } }. } ORDER BY DESC(?s) LIMIT " + str( limit) +" OFFSET "+str(offset)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    subjects = [row["s"]["value"] for row in qres["results"]["bindings"]]
    return subjects


def get_NBentInNG(sparql_ep, new_ng):
    sparql = SPARQLWrapper(sparql_ep)
    query = "select  (COUNT(DISTINCT ?s) as ?nb)  FROM <" + new_ng + "> WHERE  {   ?s ?p ?o }"

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    qres = sparql.query().convert()
    nb_todo = qres["results"]["bindings"][0]["nb"]["value"]
    return int(nb_todo)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path",
                        default="/user/cringwal/home/PycharmProjects/Kastor/shapes/PersonShape_op.ttl")
    parser.add_argument("-ng", "--searchspace_namedgraph", default="http://ns.inria.fr/kstor/#inferences")
    args = parser.parse_args()

    if args.shape_file_path and args.searchspace_namedgraph:
        ## Get shape data
        shape = Graph()
        shape.parse(args.shape_file_path)

        # Initialize SPARQL endpoint connection
        sparql_ep = 'http://localhost:8080/sparql'

        search_ng = args.searchspace_namedgraph
        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
        type_triples = ts.getShapeType(shape)
        type_triples_name = type_triples.replace("http://dbpedia.org/ontology/", "")
        namespaces = shape.namespaces()
        prop_focus = ts.getShapeProp(shape)
        dict_simply_real = {}
        for p in prop_focus:
            dict_simply_real[ts.getSimplifiedProp(p)] = p
        type_prop = ts.getShapePropWithType(shape)

        #### Named graph definition
        default_graph = "urn:x-arq:DefaultGraph"
        inf_graph = "http://ns.inria.fr/kstor/inferences/" + shape_name
        found_ng = "http://ns.inria.fr/kstor/wikichecked/" + shape_name + "/abtract_md"
        ns_class_ids = "http://ns.inria.fr/kstor/class_randoms_id/" + type_triples_name
        abstract_ng = "http://ns.inria.fr/kstor/wiki_md/" + type_triples_name

        search_space = [inf_graph, default_graph]

        clean = False
        nb_in_found_ng = get_NBentInNG(sparql_ep, found_ng)
        print(">>>>>>>>>>nb_in_found_ng:", nb_in_found_ng)
        nb_in_abstract_ng = get_NBentInNG(sparql_ep, abstract_ng)
        print(">>>>>>>>>>nb_in_abstract_ng:", nb_in_abstract_ng)
        print("INSERT IN >", found_ng)

        for search_ng in search_space:

            print("===============================CURRENT SEARCH NG>", search_ng)
            nb_entities = getNbEntToDO(sparql_ep, found_ng, abstract_ng)
            size_sample = nb_entities

            nb_loop = 0
            count_ent_checked = 0
            offset = 0
            limit = 10000
            done = []
            to_do = nb_entities
            sample = [0]

            while len(sample) != 0:
                print(">>>>>>>>>>>>>>>>>>>>>LOOP :", nb_loop, ">", count_ent_checked, "/", nb_entities)

                sample = get_SubjectsToRetrieve(sparql_ep, search_ng, found_ng, abstract_ng, limit, offset)
                print(sample)

                for uri in sample:

                    uri = rs.uncodeurl(uri)
                    print(uri)
                    done.append(uri)
                    count_ent_checked += 1
                    data_sbj = None
                    data_sbj = cs.get_NamedGraphDataRangeOk(uri, search_ng, type_prop, sparql_ep).to_dict('dict')
                    print(data_sbj)
                    if (data_sbj):
                        abs_ = cs.get_abstract_ng(uri, abstract_ng, sparql_ep)
                        if (len(abs_) > 0):
                            abstract = abs_["abstract"][0]
                            nb_found = 0
                            for prop in data_sbj.keys():
                                values = list(set(data_sbj[prop].values()))
                                for val in values:
                                    current_prop = dict_simply_real[prop]
                                    if ("Year" in prop and "-" in str(val)):
                                        print("DATE")
                                        val = str(val).split("-")[0][0:4]
                                    if str(val) != "nan" and str(val) != "NaN" and str(val) != "":

                                        val = rs.cleanTxt(str(val))
                                        found = ts.find_in_abstractWithObj(abstract, current_prop, val,
                                                                           type_prop[current_prop])

                                        if (found):

                                            print(">>>>>>>>>>>>>>>>>>>>>>>>>FOUND")
                                            nb_found += 1
                                            temp_new = {"ent_uri": uri, "type": type_prop[current_prop],
                                                        "prop": current_prop,
                                                        "value": [val]}
                                            if ('"' in val or "'" in val):
                                                val = val.translate(str.maketrans({"'": r"\'", '"': r'\"'}))
                                            query = ""
                                            if ("dbo:" not in type_prop[current_prop]):
                                                query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + found_ng + "> { <" + uri + "> <" + current_prop + ">  '" + val + "'^^" + \
                                                        type_prop[current_prop] + " }}"
                                            else:
                                                query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> INSERT DATA { GRAPH <" + found_ng + "> { <" + uri + "> <" + current_prop + ">  <" + val + ">  }}"
                                            print(query)
                                            res = ct.sparql_service_update(sparql_ep, query)
                                            print(res)
                            if nb_found > 0:
                                print("-", uri, ">", nb_found)
                    else:
                        print("PRB WITH SUBJ")
                nb_new = get_NBentInNG(sparql_ep, abstract_ng)
                print(">>>>>>>>>>>>>>> nb_new ?", nb_new)
                offset += limit
                nb_loop += 1
