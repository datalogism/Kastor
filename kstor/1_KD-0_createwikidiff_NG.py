"""
1_KD-0_createwikidiff_NG.py

Script to tag new Wikipedia articles and insert them into a knowledge graph
>>>>>>>>>>>>>>>>>>>>>> IMPORTANT:
Chose your turtle dump from https://databus.dbpedia.org/dbpedia :
old_wiki_ttl_path
new_wiki_ttl_path
class_ttl_path
And select the focus class (class_focus) you want to process from the DBpedia Ontology
"""

from argparse import ArgumentParser
import src.corese_tools as ct
import re

if __name__ == '__main__':
    # Set up command line argument parsing
    parser = ArgumentParser(description='Process new Wikipedia articles and add them to the knowledge graph')
    parser.add_argument("-old", "--old_wiki_ttl_path",
                        default="/user/cringwal/home/Desktop/CORESE_LAB/WiffWiki/page_lang=en_ids_202004.ttl",
                        help="Path to the old Wikipedia dump")
    parser.add_argument("-new", "--new_wiki_ttl_path",
                        default="/user/cringwal/home/Desktop/CORESE_LAB/WiffWiki/page_lang=en_ids202209.ttl",
                        help="Path to the new Wikipedia dump")
    parser.add_argument("-cf", "--class_focus",
                        default="Person",
                        help="Path to the new Wikipedia dump")
    parser.add_argument("-cf", "--class_ttl_path",
                        default="/user/cringwal/home/Desktop/THESE/WikiDiff/instance-types_lang=en_transitive.tt",
                        help="Path to the new Wikipedia dump")
    parser.add_argument("-ng", "--new_articles_ng",
                        default="http://ns.inria.fr/kstor/wikinew_202004/",
                        help="Path to the new Wikipedia dump")
    args = parser.parse_args()

    print('START')
    subj_list = set()
    with open(args.old_wiki_ttl_path) as file:
        for line in file:
            sbj = re.findall("<http://dbpedia.org/resource/(.*)> <", line)
            look_at = sbj[0]
            subj_list.add(look_at)

    not_found= set()
    with open(args.new_wiki_ttl_path) as file:
        for line in file:
            sbj = re.findall("<http://dbpedia.org/resource/(.*)> <", line)
            look_at = sbj[0]
            if (look_at not in subj_list):
                not_found.add(look_at)

    print('END')
    not_found_article = set()
    with open(args.class_ttl_path) as file:
        for line in file:
            person = re.findall("<http://dbpedia.org/ontology/{}>".format(args.class_focus), line)
            if (len(person) > 0):
                sbj = re.findall("<http://dbpedia.org/resource/(.*)> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                                 line)
                look_at = sbj[0]
                if (look_at in not_found):
                    not_found_article.add(look_at)

    # Configuration
    sparql_ep = 'http://localhost:8080/sparql'  # SPARQL endpoint
    current_ng = args.new_articles_ng  # Target named graph for new data

    total_articles = len(not_found_article)

    # Process each article
    for i, article_title in enumerate(not_found_article):
        print(f"Processing article {i + 1}/{total_articles}")

        # Create URI for the article
        uri = f"http://dbpedia.org/resource/{article_title}"

        # SPARQL update query to insert the article as a dbo:Thing
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX ks: <http://ns.inria.fr/kstor/#>
        INSERT DATA {{
            GRAPH <{current_ng}> {{
                <{uri}> a dbo:{args.class_focus}
            }}
        }}"""

        # Execute the SPARQL update
        ct.sparql_service_update(sparql_ep, query)
