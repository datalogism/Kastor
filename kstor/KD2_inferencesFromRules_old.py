import re
import src.corese_tools as ct
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
import logging


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-r", "--rules_file_path", default=None)
    parser.add_argument("-m", "--mode", default="insert")

    args = parser.parse_args()
    print(args.mode=="insert" and args.rules_file_path)
    if args.rules_file_path :
        if( args.mode == "insert" or args.mode=="delete"):
            sparql_ep = 'http://localhost:8080/sparql'
            query= ""

            ##### PARSE RULES FILES
            tree = ET.parse(args.rules_file_path)
            root = tree.getroot()
            rules=root.findall("{http://ns.inria.fr/corese/rule/}rule/")

            regex1 = r"GRAPH ks:[\w|\"_\"]+"
            if args.mode == "insert":
                for rule in rules:
                    print("========================INSERT RULE")
                    query=rule.text.replace("CONSTRUCT", "INSERT")
                    print(query)


            if args.mode == "delete":
                for rule in rules:
                    print("========================DELETE RULE")
                    query=rule.text.replace("CONSTRUCT", "DELETE")

            matches = re.findall(regex1, query, re.MULTILINE)
            named_graph_used = matches[0].replace("GRAPH", "").strip()
            print(named_graph_used)
            regex2 = r" GRAPH " + named_graph_used + " {([^}]+)}"
            added_ = re.findall(regex2, query, re.MULTILINE)
            added = added_[0].strip()

            count_query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT (COUNT(*) as ?Triples)  FROM " + named_graph_used + " { " + added + " } "
            res_count = ct.sparql_service_to_int(sparql_ep, count_query)

            print(">>>>>>>>>>>", res_count, " before "+args.mode)

            splited = query.split("WHERE")
            delete_query = splited[0] + "WHERE {" + added + "}"
            res = ct.sparql_service_update(sparql_ep, delete_query)

            res_count = ct.sparql_service_to_int(sparql_ep, count_query)
            print(">>>>>>>>>>>", res_count, " after  "+args.mode)
    else:
        logging.error("Rules file path not provided AND mode must be equals to 'insert' or 'delete'")

