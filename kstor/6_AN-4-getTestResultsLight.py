import wandb
from argparse import ArgumentParser
import pandas as pd

import pandas as pd

from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import FOAF, RDF, SH

import src.NLI_TripletCritic as llm_eval
from datetime import date
import urllib.parse
def uncodeurl(URL):
    if("%" in URL):
        print("HEY")
        return urllib.parse.unquote(URL)
    else:
        return URL
def concept_path_dist(onto_g, c1, c2):
    dist_q = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    select  (count( distinct ?mid) as ?length) where {
    """ + c1 + """ rdfs:subClassOf* ?mid .
    ?mid rdfs:subClassOf* """ + c2 + """ .
    }
    """

    # print(dist_q)
    qres = onto_g.query(dist_q)
    res = [row.length for row in qres]
    dist = res[0]
    return int(dist) - 1


def concept_path(onto_g, c1, c2):
    dist_q = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    select  distinct ?mid  where {
    """ + c1 + """ rdfs:subClassOf* ?mid .
    ?mid rdfs:subClassOf* """ + c2 + """ .
    }
    """

    # print(dist_q)
    qres = onto_g.query(dist_q)
    res = [
        str(row.mid).replace("http://dbpedia.org/ontology/", "dbo:").replace("http://www.w3.org/2002/07/owl#", "owl:")
        for row in qres]
    return res


def getLowerCommonAncestor(onto_g, c1, c2):
    lca_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    SELECT DISTINCT ?superclass
    WHERE {
       ?superclass ^rdfs:subClassOf* """ + c1 + """.
       ?superclass ^rdfs:subClassOf*  """ + c2 + """ .
    filter not exists { 
      ?moreSpecificSuperclass rdfs:subClassOf ?superclass ;
                              ^rdfs:subClassOf* """ + c1 + """, """ + c2 + """ .
    }

    }"""

    #print(lca_query)
    qres = onto_g.query(lca_query)
    if(len(qres)>0):
        res = [row.superclass for row in qres]
       # print(res)
        lca = str(res[0]).replace("http://dbpedia.org/ontology/", "dbo:").replace("http://www.w3.org/2002/07/owl#", "owl:")
        return lca
    else:
        return None


def getShapeType(shacl_g):
    get_types = """
        SELECT DISTINCT ?target_class
        WHERE {
            ?a sh:targetClass ?target_class
        }"""
    qres = shacl_g.query(get_types)
    return [str(row[0]) for row in qres][0]


def getShapeProp(shacl_g):
    get_prop = """
    SELECT DISTINCT ?target_prop
    WHERE {
        ?a sh:path ?target_prop
    }"""
    qres = shacl_g.query(get_prop)
    return [str(row[0]) for row in qres]


def getShapePropWithType(shacl_g):
    get_prop = """
    SELECT DISTINCT ?target_prop ?datatype
    WHERE {
        ?a sh:path ?target_prop;
           sh:datatype|sh:class ?datatype.
    }"""
    qres = shacl_g.query(get_prop)
    return {str(row[0]): str(row[1]).replace("http://www.w3.org/2001/XMLSchema#", "xsd:").replace(
        "http://dbpedia.org/ontology/", "dbo:") for row in qres}


def getSimplifiedProp(prop):
    if ("#" in prop):
        splitted = prop.split("#")
    else:
        splitted = prop.split("/")
    return splitted[-1]


def simplify_label(label):
    temp_label = label
    if ("(" in temp_label):
        temp_label = label[:label.index("(")]
    if ("," in temp_label):
        temp_label = label[:label.index(",")]

    if ("." in temp_label):
        temp_label2 = temp_label.split()
        temp_label_clean = []
        for token in temp_label2:
            if ("." not in token):
                temp_label_clean.append(token)
        temp_label = " ".join(temp_label_clean)
    return temp_label.strip()


def fabien_dist(onto_g,c1, c2, root):
    if (c1 != c2):
        # c1_root=concept_path_dist(onto_g,c1,root)
        # c2_root=concept_path_dist(onto_g,c2,root)

        c3 = getLowerCommonAncestor(onto_g, c1, c2)
        if(c3):
            # if(c1!=c3):
            c3_c1 = concept_path_dist(onto_g, c1, c3)
            c3_c2 = concept_path_dist(onto_g, c2, c3)
            c3_root = concept_path_dist(onto_g, c3, root)

            dist_min_c = min(c3_c1, c3_c2)
            # print(concept_path(onto_g,c1,root))
            # print("xxx")
            # print(concept_path(onto_g,c2,root))
            # print("xxx")
            # print(concept_path(onto_g,c3,root))
            # print("xxx")
            sim = (1 - pow(0.5, c3_root)) / ((1 - pow(0.5, c3_c1)) + (1 - pow(0.5, c3_c2)) + (1 - pow(0.5, c3_root)))
            return sim
        else:
            return 0
    else:
        return 1


def getWuPalmer(onto_g, c1, c2, root):
    if (c1 != c2):
        c3 = getLowerCommonAncestor(onto_g, c1, c2)
        # if(c1!=c3):
        c3_c1 = concept_path_dist(onto_g, c1, c3)
        c3_c2 = concept_path_dist(onto_g, c2, c3)
        c3_root = concept_path_dist(onto_g, c3, root)

        wu_palmer = (2 * c3_root) / (c3_c1 + c3_c2 + (2 * c3_root))
        return wu_palmer
    else:
        return 1


def getClassOrEquivClass(onto_g, class_):
    class_search = str(class_).replace("http://dbpedia.org/ontology/", "dbo:").replace("http://www.w3.org/2002/07/owl#",
                                                                                       "owl:")
    #print(class_search)
    Q_class_exist = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        ASK {
           """ + class_search + """ a owl:Class
        }"""
    # print(Q_class_exist)
    qres = onto_g.query(Q_class_exist)

    res = [row for row in qres]
    if (res[0] == True):
        return class_
    else:
        #print(">>>>>>>>>>>>>>>>>>>>>")
        #print(Q_class_exist)
        #print(res)
        Qget_equiv = """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT DISTINCT ?target_class
            WHERE {
                ?target_class owl:equivalentClass """ + class_search + """
            }"""
        #print(Qget_equiv)
        qres = onto_g.query(Qget_equiv)
        res = [row.target_class for row in qres]
        if (len(res) > 0):
            return res[0].replace("http://dbpedia.org/ontology/", "dbo:").replace("http://www.w3.org/2002/07/owl#",
                                                                                  "owl:")
        else:
            return None
import json
import requests
def get_table_data_from_url(source_url: str, api_key= None) -> None:
    response = requests.get(source_url, auth=("api", api_key), stream=True, timeout=5)
    response.raise_for_status()
    bytes_list = []
    for data in response.iter_content(chunk_size=1024):
        bytes_list.append(data)
    final_byte_data = b"".join(bytes_list)
    data_dict = json.loads(final_byte_data.decode("utf-8"))
    table_df = pd.DataFrame(data=data_dict["data"], columns=data_dict["columns"])
    return table_df


if __name__ == '__main__':
    parser = ArgumentParser()
    print("YEAH")
    parser.add_argument("-wapik", "--wandb_api_key", default=None)
    parser.add_argument("-wuser", "--wandb_user", default=None)
    parser.add_argument("-wproj", "--wandb_project", default=None)
    parser.add_argument("-output", "--dir_save", default=None)
    args = parser.parse_args()
    args.wandb_api_key="5f4208dc97c7b3542281b94b64eb42833243cc71"
    args.wandb_user="inria_test"
    args.wandb_project="BigXP_DT&OP_MOREex"
    args.dir_save="/user/cringwal/home/Desktop/RESULTS_DATA/CONTROL_TEST/"
    dbpedia_endpoint = "http://localhost:8080/sparql"


    onto_g = Graph()

    #onto_g.parse("https://mappings.dbpedia.org/server/ontology/dbpedia.owl")
    onto_g.parse("/user/cringwal/home/Desktop/CORESE_LAB/ontology.owl")


    class_root = "owl:Thing"

    if args.wandb_api_key and args.wandb_user and args.wandb_project and args.dir_save:
        save_dir=args.dir_save

        print(">>>>>>>>>>>>>>>>>>>>>>>>>> START HERE")


        api = wandb.Api()
        API_KEY = args.wandb_api_key
        wandb.login(key=API_KEY)
        #to_delete_in_name=["DS_turtleS_0datatype_1inLine_1facto_BART_","_bart-base"]
        to_delete_in_name=["DS_turtleS_0datatype_1inLine_1facto_BART_DTOP_","_kg_bart-base","_kg2_bart-base","_kg3_bart-base","_bart-base"]
        #to_delete_in_name=["DS_turtleS_0datatype_1inLine_1facto_BART_","bart-base_"]
        user=args.wandb_user
        project=args.wandb_project
        runs= api.runs(
            path=user+"/"+project
        )

        cols=[ 'model','fold','test_BLEU', 'test_F1_macro_ALL', 'test_F1_micro_ALL', 'test_accuracy',
              'test_dist_edit', 'test_fn_rate', 'test_fp_rate', 'test_loss', 'test_part_parsed',
              'test_part_subj_ok', 'test_part_valid_s', 'test_part_valid_r', 'test_prec_macro', 'test_prec_micro', 'test_recall_macro',
              'test_recall_micro',"g_not_valid_r","g_valid_s","p_valid_s","FP_ext","RDF_p_g","RDF_p_FP"]

        data_results = []
        for run in runs:
            name_orig = run.name
            #or "AbsClean_Oldx4" in name_orig
            if("X10" in name_orig ):

                name_orig = run.name
                name = name_orig
                print(name)
                current_fold = name.split("_")[-1]
                print(current_fold)

                data_summary = run.summary
                print(">>>>>>>>>>>>>>>")
                print(data_summary)
                # if("test_model_-" in name):
                model = run.group
                for token in to_delete_in_name:
                   model = model.replace(token, "")

                print(model, "->", current_fold)
                shape = Graph()
                shape_file = "/user/cringwal/home/PycharmProjects/Kastor/shapes/PersonShape_op_and_dp.ttl"

                #shape_file = "/user/cringwal/home/Desktop/RES_XP_last/ALL_SHAPES/REPLACEShapeTXT2KG_clean.ttl"
                #shape_file = shape_file.replace("REPLACE",model)
                shape.parse(shape_file)
                namespaces = shape.namespaces()
                prop_focus = getShapeProp(shape)
                dict_simply_real = {}
                for p in prop_focus:
                    dict_simply_real[getSimplifiedProp(p)] = p
                type_prop = getShapePropWithType(shape)
                type_triples = getShapeType(shape)

                tempo={}
                tempo["model"] = model
                tempo["fold"] = current_fold
                tempo["g_not_valid_r"] = 0
                tempo["g_valid_s"] = 0
                for key in  data_summary.keys():
                    if key in cols  or ("test_F1_micro_" in key ):
                       tempo[key]= data_summary[key]
                data_results.append(tempo)
        df = pd.DataFrame.from_dict(data_results)
        df.to_csv(save_dir+"Test_results_wb_BigXP_DT&OP_MORELightx10.csv")
