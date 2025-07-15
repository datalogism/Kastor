from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer
import sys

sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/slm/src/')
import score_fct as scr_fct
#Chen_Fubin	birthPlace	:Ziyang
rela="deathPlace"
val=":Moldavian_Soviet_Socialist_Republic"
type_d="dbo:Place"
abstract='''****Kirill Fyodorovich Ilyashenko** (Template:Lang-ro; 27 May [[O.S.](:Old_Style_and_New_Style_dates) 14 May] 1915) – 21 April 1980) was a [Moldavian](:Moldavian_Soviet_Socialist_Republic) politician who served as the Chairman of the Presidium of the [Supreme Soviet of the Moldavian SSR](:Supreme_Soviet_of_the_Moldavian_SSR) from 1963 to 1980. He served the longest as Chairman of the Presidium, serving a total of 17 years.'''

find_in_abs = scr_fct.find_in_abstractWithObj(abstract, rela, val, type_d)
print(find_in_abs)
