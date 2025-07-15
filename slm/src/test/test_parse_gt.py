from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer
import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/slm/src/')
import score_fct as scr_fct
g_sent=":%2819255%29_1994_VK8 a :CelestialBody ;\n   :epoch \"2006-12-31\" ."
format_="turtleS"

list_rel_gt, parsed_gt = scr_fct.toListRel(g_sent, format_, True)
txt = scr_fct.cleanDecoded3(g_sent)
print(txt)
list_rel = scr_fct.TurtleSToList(txt, True)
print(list_rel)
