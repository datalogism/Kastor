import re
import src.corese_tools as ct
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
import logging


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    parser.add_argument("-r", "--rules_file_path", default=None)
    parser.add_argument("-m", "--mode", default="insert")

    args = parser.parse_args()
    print(args.shape_file_path)

    sparql_ep = 'http://localhost:8080/sparql'
    #query = 'SELECT DISTINCT ?g  {  GRAPH ?g {}}'
    #results = ct.get_sparql_dataframe(sparql_ep, query)
    #print(" NG>", )
    #print(results)
    #sys.exit()
    if args.rules_file_path :

        if( args.mode == "insert" or args.mode=="delete"):
            query= ""

            ##### PARSE RULES FILES
            tree = ET.parse(args.rules_file_path)
            root = tree.getroot()
            rules=root.findall("{http://ns.inria.fr/corese/rule/}rule/")

            pattern_replace = "$INFERENCE_NS$"
            named_graph_used=None

            print(">>>>>>NB RULES TO APPLY:",len(rules))

            if args.mode == "delete":

                if (args.shape_file_path):
                    shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")

                    print("DELETE>", shape_name)
                    named_graph_used = "<http://ns.inria.fr/kstor/inferences/" + shape_name + ">"
                    print("DELETE")
                    query_delete="DROP GRAPH "+named_graph_used
                    res = ct.sparql_service_update(sparql_ep, query_delete)
            else:
                for rule in rules:

                    if args.mode == "insert":
                        #print("========================INSERT RULE")
                        query=rule.text.replace("CONSTRUCT", "INSERT")
                        #print(query)


                    print("############# MATCHES")
                    print(query)
                    if (args.shape_file_path):
                        shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
                        if (pattern_replace in query):
                            named_graph_used = "<http://ns.inria.fr/kstor/inferences/" + shape_name + ">"

                    if (pattern_replace in query):
                        print('INSIDE')
                        regex1 = r"GRAPH \$INFERENCE_NS\$"
                    else:
                        regex1 = r"GRAPH ks:[\w|\"_\"]+"
                    matches = re.findall(regex1, query, re.MULTILINE)

                    if(len(matches)>0):
                        if(named_graph_used is None):
                            named_graph_used = matches[0].replace("GRAPH", "").strip()

                        if(pattern_replace in query):
                            regex2 = r" GRAPH \$INFERENCE_NS\$ {([^}]+)}"
                            added_ = re.findall(regex2, query, re.MULTILINE)
                            added = added_[0].strip()
                            query = query.replace(pattern_replace, named_graph_used)

                        else:
                            regex2 = r" GRAPH " + named_graph_used + " {([^}]+)}"
                            added_ = re.findall(regex2, query, re.MULTILINE)
                            added = added_[0].strip()



                        count_query = "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX ks: <http://ns.inria.fr/kstor/#> SELECT (COUNT(*) as ?Triples)  FROM " + named_graph_used + " { " + added + " } "
                        print(count_query)
                        res_count = ct.sparql_service_to_int(sparql_ep, count_query)

                        print(">>>>>>>>>>>", res_count, " before "+args.mode)
                        print(query)
                        res = ct.sparql_service_update(sparql_ep, query)
                        #splited = query.split("WHERE")
                        #delete_query = splited[0] + "WHERE {" + added + "}"
                        #print("DELTE")
                        #print(delete_query)
                        #res = ct.sparql_service_update(sparql_ep, delete_query)

                        res_count = ct.sparql_service_to_int(sparql_ep, count_query)
                        print(">>>>>>>>>>>", res_count, " after  "+args.mode)
    else:
        logging.error("Rules file path not provided AND mode must be equals to 'insert' or 'delete'")

