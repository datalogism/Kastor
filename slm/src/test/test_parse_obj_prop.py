from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer
import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/slm/src/')
import score_fct as scr_fct

triples='''@prefix dbo: <http://dbpedia.org/ontology/> .\n@prefix dbr: <http://dbpedia.org/resource/> .\n\ndbr:Vanessa_Delgado a dbo:Person ;\n dbo:birthPlace dbr:California .\n\n'''

test=scr_fct.TurtleToList(triples)
print(test)
#triples=':Matthew_Clempner a:Person;:birthDate "1956-05-20";:birthYear "1956", "1956-05-20".'
grammar_file="/user/cringwal/home/PycharmProjects/Kastor/slm/syntax_config/turtle_light_facto.ebnf"
with open(grammar_file, "r") as file:
    grammar_str = file.read()

#triples=":Nothando_Vilakazi a:Person;:birthPlace:South_Africa_women%5C%27s_national_soccer_team. "
list_triples=[":Thomas_Frederick_Onslow a :Person; :birthPlace :Hampshire_county_cricket_teams; :deathPlace:Hampshire_county_cricket_teams, :New_Alresford. ",
              ":J%C3%A1nos_L%C3%A1szai a :Person; :label \"J\u00e1nos L\u00e1szai\"; :deathDate \"1523-08-17\"; :deathYear \"1523\"; :nationality :Hungary .:J\u00e1nos_L\u00e1szai :birthYear \"1448\" ."]
import urllib.parse
import re
regex = r"\:(.*?)(\s|\;|\.|\,)"
for triples in list_triples:
    tempo=triples.replace(":"," :").replace("  :"," :")

    matches = re.finditer(regex, tempo, re.MULTILINE)

    for matchNum, match in enumerate(matches, start=1):
        orig=str(match.group(1)).strip()
        encoded = urllib.parse.quote(orig)
        if("%" in encoded):
            tempo=tempo.replace(orig,encoded)

    triples_after=tempo.replace("  :"," :").replace(" :",":")
    print(triples_after)


    parsed_grammar = parse_ebnf(grammar_str)

    start_rule_id = parsed_grammar.symbol_table["root"]
    grammar_recognizer = StringRecognizer(parsed_grammar.grammar_encoding, start_rule_id)
    print("xxxxxxxxxxxxx>", grammar_recognizer._accept_prefix(triples_after))

    test=scr_fct.toListRel(triples_after,format_="turtleS", facto=True,grammar=grammar_recognizer)
    print("============ RES")
    print(test)
sys.exit()
