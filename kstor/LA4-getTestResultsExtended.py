import wandb
from argparse import ArgumentParser
import pandas as pd

import pandas as pd

from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import FOAF, RDF, SH


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
    args.dir_save="/user/cringwal/home/Desktop/RESULTS_DATA/"
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
        to_delete_in_name=["DS_turtleS_0datatype_1inLine_1facto_","_kg_bart-base","_kg2_bart-base","_kg3_bart-base","_bart-base"]
        #to_delete_in_name=["DS_turtleS_0datatype_1inLine_1facto_BART_","bart-base_"]
        user=args.wandb_user
        project=args.wandb_project
        runs= api.runs(
            path=user+"/"+project
        )

        cols=[ 'model','fold','test_BLEU', 'test_F1_macro', 'test_F1_micro', 'test_accuracy',
              'test_dist_edit', 'test_fn_rate', 'test_fp_rate', 'test_loss', 'test_part_parsed',
              'test_part_subj_ok', 'test_part_valid_s', 'test_part_valid_r', 'test_prec_macro', 'test_prec_micro', 'test_recall_macro',
              'test_recall_micro',"g_not_valid_r","g_valid_s","p_valid_s","FP_ext","RDF_p_g","RDF_p_FP"]
        data_results=[]
        for run in runs:
            name_orig = run.name
          #  if("University_kg" in run.name or "WrittenWork_kg" in run.name):

            name_orig = run.name
            name = name_orig
            print(name)
            current_fold = name.split("_")[-1]
            print(current_fold)

            data_summary = run.summary
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
            for col in cols:
                if col in data_summary.keys():
                   tempo[col]= data_summary[col]
            print("---------")
            print(tempo)
            print("---------")
            tempo["model"]=model
            tempo["fold"]=current_fold
            tempo["g_not_valid_r"]=0
            tempo["g_valid_s"]=0
            tempo["p_valid_s"]=0
            tempo["rdf_ext"]=0
            tempo["RDF_g"]=0
            tempo["RDF_p"]=0
            tempo["R_PD"]=0

            for artifact in run.logged_artifacts():
                art_name=artifact.name
                print(art_name)
                if("ToInspecttable" in art_name):
                    print("before")
                    #artifact_dir = artifact.download(skip_cache=True)
                    #print(artifact_dir)
                    table=artifact.get("To Inspect table")
                    print("after")


                    if(table):
                        print("HEY")
                        df0 = pd.DataFrame(data=table.data, columns=table.columns)
                        print(df0)

                        interest = df0[df0["type"] != "FP_different"]

                        ent_dict = {}
                        for index, row in interest.iterrows():
                            if (row["ent_uri"] not in ent_dict.keys()):
                                ent_dict[row["ent_uri"]] = {}
                            rel_name = row['pred']
                            rel_type = row['type']
                            if (rel_type == "FN"):
                                val = row['val_gold']
                            else:
                                val = row['val_pred']

                            if (val not in ent_dict[row["ent_uri"]].keys()):
                                ent_dict[row["ent_uri"]][val] = {}
                            if (rel_type not in ent_dict[row["ent_uri"]][val].keys()):
                                ent_dict[row["ent_uri"]][val][rel_type] = []
                            ent_dict[row["ent_uri"]][val][rel_type].append(rel_name)

                        nb_val = 0
                        n_pb_val = 0
                        pb_by_rel = {}
                        for ent in ent_dict.keys():
                            for k in ent_dict[ent].keys():
                                nb_val += 1
                                if (len(ent_dict[ent][k].keys()) == 2):
                                    n_pb_val += 1

                        tempo["NB_val"] = nb_val
                        tempo["NB_PB_val"] = n_pb_val

                        ############################################################
                        interest2 = df0[df0["type"] != "FN"]
                        uri_to_check = set()
                        for index, row in interest2.iterrows():
                            if(":" in str(row["val_pred"])):
                                uri_to_check.add(str(row["pred"]) + "$" + str(row['val_pred']) + "$" + str(row['val_gold']))

                        print(uri_to_check)
                        stats_res = {"new": [], "diff": []}

                        print("START")
                        for uris_str in uri_to_check:
                            uris = uris_str.split("$")
                            print(uris)
                            tempo_here = {"found_uri": False, "sim_pred_shape": None, "sim_pred_gold": None,
                                     "sim_gold_shape": None}
                            simpli_uri = dict_simply_real[uris[0]]
                            print(uris)
                            shape_domain = getClassOrEquivClass(onto_g, type_prop[simpli_uri])
                            print(shape_domain)

                            if (str(uris[1]) != "nan"):
                                print("FP NEWWWWWWWWWWWWWWWWWW")
                                uri_pred = uris[1].replace(":", "")
                                query = "SELECT  ?t WHERE {<http://dbpedia.org/resource/" + uri_pred + "> a ?t. FILTER regex(?t, '^http://dbpedia.org/ontology/') }"
                                sparql = SPARQLWrapper(dbpedia_endpoint)
                                sparql.setQuery(query)
                                sparql.setReturnFormat(JSON)
                                qres = sparql.query().convert()
                                types_found = [x["t"]["value"].replace("http://dbpedia.org/ontology/", "dbo:").replace(
                                    "http://www.w3.org/2002/07/owl#", "owl:") for x in qres["results"]["bindings"]]
                                if (len(types_found) > 0):

                                    tempo_here["found_uri"] = True
                                    types_found_depth = {}
                                    for typ_ in types_found:
                                        type_c = getClassOrEquivClass(onto_g, typ_)
                                        #print("type>", typ_, " and ", shape_domain)
                                        # c_a=getLowerCommonAncestor(onto_g,typ_,shape_domain)
                                        if(type_c and shape_domain):
                                            WP = fabien_dist(onto_g, shape_domain, type_c, class_root)
                                            types_found_depth[typ_] = WP
                                    # print(types_found_depth)
                                    if(len(list(types_found_depth.keys()))>0):
                                        c1 = max(types_found_depth.items(), key=lambda k: k[1])[0]

                                        tempo_here["sim_pred_shape"] = types_found_depth[c1]
                                    else:
                                            c1 = None
                                            tempo_here["sim_pred_shape"] = 0

                                    if (str(uris[2]) != "nan"):
                                        uri_gold = uris[2].replace(":", "")
                                        query = "SELECT  ?t WHERE {<http://dbpedia.org/resource/" + uri_gold + "> a ?t. FILTER regex(?t, '^http://dbpedia.org/ontology/') }"
                                        sparql = SPARQLWrapper(dbpedia_endpoint)
                                        sparql.setQuery(query)
                                        sparql.setReturnFormat(JSON)
                                        qres = sparql.query().convert()
                                        types_found2 = [
                                            x["t"]["value"].replace("http://dbpedia.org/ontology/", "dbo:").replace(
                                                "http://www.w3.org/2002/07/owl#", "owl:") for x in
                                            qres["results"]["bindings"]]
                                        if (len(types_found2) > 0):

                                            types_found_depth2 = {}
                                            for typ_ in types_found2:
                                                c2 = getClassOrEquivClass(onto_g, typ_)
                                               # print("type>", typ_, " and ", shape_domain)
                                                # c_a=getLowerCommonAncestor(onto_g,typ_,shape_domain)
                                                if (c1 and c2):
                                                    dist = fabien_dist(onto_g, c1, c2, class_root)
                                                    types_found_depth2[typ_] = dist

                                            if (len(list(types_found_depth2.keys())) > 0):
                                                closest = max(types_found_depth2.items(), key=lambda k: k[1])[0]
                                                tempo_here["sim_pred_gold"] = types_found_depth2[closest]

                                                types_found_depth3 = {}
                                                for typ_ in types_found2:
                                                    c2 = getClassOrEquivClass(onto_g, typ_)
                                                    #print("type>", typ_, " and ", shape_domain)
                                                    # c_a=getLowerCommonAncestor(onto_g,typ_,shape_domain)
                                                    dist = getWuPalmer(onto_g, shape_domain, c2, class_root)
                                                    types_found_depth3[typ_] = dist
                                                if(len(list(types_found_depth3.keys()))):
                                                    closest = max(types_found_depth3.items(), key=lambda k: k[1])[0]
                                                    tempo_here["sim_gold_shape"] = types_found_depth3[closest]
                                                else:
                                                    tempo_here["sim_gold_shape"] = 0
                                        else:
                                            print("PB HERE")
                                            #print(types_found2)

                                if (str(uris[2]) != ""):
                                    stats_res["diff"].append(tempo_here)
                                else:
                                    stats_res["new"].append(tempo_here)

                        print(stats_res)
                        results = []
                        nb_new = len([x for x in stats_res["new"]])
                        print(nb_new)
                        nb_diff = len([x for x in stats_res["diff"]])

                        nb_uri_ok_diff = len([x for x in stats_res["diff"] if x["found_uri"] == True])
                        nb_uri_ok_new = len([x for x in stats_res["new"] if x["found_uri"] == True])

                        if((nb_uri_ok_diff )>0):
                            #avg_sim_diff = sum([x["type_sim"] for x in stats_res["diff"] if x["found_uri"] == True and x["type_sim"] != None]) / (nb_uri_ok_diff)

                            avg_sim_gold_pred = sum([x["sim_pred_gold"] for x in stats_res["diff"] if
                                                     x["found_uri"] == True and x["sim_pred_gold"] != None]) / (
                                                    nb_uri_ok_diff)
                            avg_sim_gold_shape = sum([x["sim_pred_gold"] for x in stats_res["diff"] if
                                                      x["found_uri"] == True and x["sim_gold_shape"] != None]) / (
                                                     nb_uri_ok_diff)
                        else:
                            avg_sim_gold_pred = 0
                            avg_sim_gold_shape = 0
                        if((nb_uri_ok_new + nb_uri_ok_diff)>0):
                            avg_sim_pred_shape = (sum([x["sim_pred_shape"] for x in stats_res["new"] if
                                                       x["found_uri"] == True and x["sim_pred_shape"] != None]) + sum(
                                [x["sim_pred_shape"] for x in stats_res["diff"] if
                                 x["found_uri"] == True and x["sim_pred_shape"] != None])) / (
                                                             nb_uri_ok_new + nb_uri_ok_diff)

                        else:
                            avg_sim_pred_shape=0
                        if(nb_new>0):
                            tempo["FPnew_URIOK"]=  nb_uri_ok_new / nb_new
                        else:
                            tempo["FPnew_URIOK"] = 0

                        if(nb_diff>0):
                            tempo["FPdiff_URIOK"]=   nb_uri_ok_diff / nb_diff
                        else:
                            tempo["FPdiff_URIOK"]=   0
                        #prit(tempo)

                        tempo["SemSim_gold_pred"]=  avg_sim_gold_pred
                        tempo["SemSim_gold_shape"]=  avg_sim_gold_shape
                        tempo["SemSim_pred_shape"]=  avg_sim_pred_shape

                        tempo["FN"]=len(df0[ df0["type"].str.contains("FN")])
                        tempo["FP"]= len(df0[ df0["type"].str.contains("FP")])

                        #tempo["R_PD"]=len(FP[ FP["found"]=="True" ])/len(FP)
                        print("FN>",tempo["FN"],"and FP> ",tempo["FP"])

                        TP_fn_estim=0
                        TP_fp_estim=0
                        if("test_recall_micro" in tempo.keys() and tempo["test_recall_micro"]!=100 and tempo["FN"]!=0):
                            TP_fn_estim=-(tempo["test_recall_micro"]*tempo["FN"])/(tempo["test_recall_micro"]-100)
                        if("test_prec_micro" in tempo.keys() and tempo["test_prec_micro"] != 100 and tempo["FP"]!=0):
                            TP_fp_estim = -(tempo["test_prec_micro"] * tempo["FP"]) / (
                                        tempo["test_prec_micro"] - 100)
                        tempo["TP"] = max(TP_fn_estim,TP_fp_estim)
                        tempo["NbRelPred"] = tempo["TP"]+tempo["FP"]
                        tempo["NbRelGt"] = tempo["FN"]+tempo["TP"]
                        if(tempo["NbRelPred"]>0):
                            tempo["NewFP_rate"] = tempo["FP"]/tempo["NbRelPred"]
                        else:
                            tempo["NewFP_rate"] = 0
                        if(tempo["NbRelGt"]>0):
                            tempo["NewFN_rate"] = tempo["FN"]/tempo["NbRelGt"]
                        else:
                            tempo["NewFN_rate"] = 0

                        print("================>", tempo["NewFP_rate"],"-",tempo["NewFN_rate"] )
                if("Notvalid" in art_name):

                    print(art_name)
                    table=artifact.get("Notvalid")

                    df = pd.DataFrame(data=table.data, columns=table.columns)
                    nb_not_valid=len(df)

                    motifs_p=[]
                    motifs_g=[]
                    for index, row in df.iterrows():
                        tempo["g_not_valid_r"]+=1
                        p_preds=set(row["p_pred"].replace("{'","").replace("'}","").replace("'","").replace(" ","").strip().split(","))
                        g_preds=set(row["g_pred"].replace("{'","").replace("'}","").replace("'","").replace(" ","").strip().split(","))

                        if p_preds not in motifs_p:
                            motifs_p.append(p_preds)
                            tempo["RDF_p"]+=1

                        if g_preds not in motifs_g:
                            motifs_g.append(g_preds)
                            tempo["RDF_g"]+=1
                        if(p_preds==g_preds):
                            print('HEY')

                        donot_produce=g_preds.difference(p_preds)
                        if(len(donot_produce)==0 and len(g_preds)<len(p_preds)):
                            tempo["rdf_ext"]+=1




                data_results.append(tempo)
                print(tempo)
        df = pd.DataFrame.from_dict(data_results)
        df.to_csv(save_dir+"Test_results_wb_BigXP_DT&OP_Final_test.csv")
