import sys
sys.path.append('/user/cringwal/home/PycharmProjects/Kastor/kstor/')
import  src.abstractExtended as ae
import src.corese_tools as ct

sparql_ep = 'http://localhost:8080/sparql'
#ng_to_delete=['http://ns.inria.fr/kstor/samples/PersonShape_op_and_dp/abtract_md/only_old_sample_0', 'http://ns.inria.fr/kstor/samples/PersonShape_op_and_dp/abtract_md/only_new_sample_1', 'http://ns.inria.fr/kstor/samples/PersonShape_op_and_dp/abtract_md/mix_sample_2','http://ns.inria.fr/kstor/samples/PersonShape_op_and_dp/abtract_md/only_new_sample_3']
for ng in ng_to_delete:
    query="DROP GRAPH <"+ng+">"
    results=ct.sparql_service_update(sparql_ep, query)
    print(results)