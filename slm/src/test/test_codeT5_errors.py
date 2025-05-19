from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer
import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/slm/src/')
import score_fct as scr_fct

gt_triples=":Paula_Arcos  a:Person ;:birthPlace:Spain_women%5C%27s_national_handball_team."
prod_triples=":Paula_Arcos  a:Person ;:birthPlace:Spain_women\'s_national_handball_team. "

o_t=":Vicente_Blanco  a:Person ;:birthPlace:Deusto ;:deathPlace:Bilbao."
work=":Tom_Bull a:Person;:birthPlace:Wagga_Wagga;:deathPlace:Wagga_Wagga."
grammar_file="/user/cringwal/home/PycharmProjects/Kastor/slm/syntax_config/turtle_light_facto.ebnf"
with open(grammar_file, "r") as file:
    grammar_str = file.read()

parsed_grammar = parse_ebnf(grammar_str)

start_rule_id = parsed_grammar.symbol_table["root"]
grammar_recognizer = StringRecognizer(parsed_grammar.grammar_encoding, start_rule_id)
current=o_t.replace("  a"," a")
print(">",current)
print("xxxxxxxxxxxxx>", grammar_recognizer._accept_prefix(current))

test=scr_fct.toListRel(current,format_="turtleS", facto=True,grammar=grammar_recognizer)
print("============ RES")
print(test)
sys.exit()
