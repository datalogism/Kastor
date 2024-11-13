# KASTOR PROCESS

## STEP 1-  Initialize KASTOR KB
This step is associating a random uuid to each entities related to dbo:class focused by the maximal shape chosen 

> python 1_initializeKastorFromShape.py -s SHAPE_PATH


## STEP 2-  Run inferences rules (optional)
This step is applying the rules defined by the user defined via SPARQL construct queries into a rul file as described [here](https://files.inria.fr/corese/doc/rule.html)
> python 2_inferencesRules.py -r RULES_PATH -m insert
