# KASTOR PROCESS
## STEP 0- Initialize the Kastor KB: $\mathcal{K}$
[See the CORESE dir readMe](https://github.com/datalogism/Kastor/tree/main/corese#starting-from-scratch-data-base-initialization)

## STEP 1-  Tag the entities related to the shape class: 

This step associates a random uuid to each entity related to dbo:class focused by the maximal shape chosen and having an abstract, it creates $\mathcal{K}_{\mathbb{P}(s^*)}$ . The dbo:Person shape is accessible here [PersonShape.ttl](https://github.com/datalogism/Kastor/blob/main/shapes/PersonShape.ttl)
```
python 1_initializeKastorFromShape.py -s SHAPE_PATH
```

## STEP 2-  Run inferences rules (optional):
This step is applying the rules defined by the user and create $\mathcal{G}^{\mathcal{R}\models}_{\mathbb{P}(s^*)}$, it uses SPARQL construct queries gathered into a rul file as described [here](https://files.inria.fr/corese/doc/rule.html)
```
 python 2_inferencesRules.py -r RULES_PATH -m insert
```

## STEP 3-  Wikicheck: 
This script check if the values of the datatype properties objects could be found in the Wikipedia abstracts, it creates $\mathcal{K}^{\mathcal{WR}\models}_{\mathbb{P}(s^*)}$
```
 python 3_WikicheckNamedGraph.py -s SHAPE_PATH -ng SEARCHSPACE_NAMEDGRAPH
```
## STEP 4 - The exemples-specific patterns 
This script is used to analyse the example-specific patterns set $\mathbb{P}_{\mathcal{K}}(s^*)$ 
```
 python 4_getExampleSpecificPatternsStats.py -s SHAPE_PATH -output output_dir -ng named_graph_sample 
```
## STEP 5-  Create a Random Sample
This script was used to create $DR^0$, $DR^1$, $DR^2$
```
 python 5_CreateNewRandomSample.py -s SHAPE_PATH -sz 1200 
```
## STEP 6-  Export a TurtleLight dataset for training a SLM
Export a previously create sample in TurtleLight datasets splitted in train/test/eval  
```
 python 6_createTurtleLightdatasetFromNG.py -s SHAPE_PATH -output output_dir -ng named_graph_sample 
```
