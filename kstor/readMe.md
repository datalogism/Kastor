# KASTOR PROCESS
## STEP 0- Initialize the Kastor KB: $\mathcal{K}$
[See the CORESE dir readMe](https://github.com/datalogism/Kastor/tree/main/corese#starting-from-scratch-data-base-initialization)

## STEP 1-  Tag the entities related to the shape class: $\mathcal{K}_{\mathbb{P}(s^*)}$ 

This step associates a random uuid to each entity related to dbo:class focused by the maximal shape chosen. The dbo:Person shape is accessible here [PersonShape.ttl](https://github.com/datalogism/Kastor/blob/main/shapes/PersonShape.ttl)
```
python 1_initializeKastorFromShape.py -s SHAPE_PATH
```

## STEP 2-  Run inferences rules (optional): $\mathcal{G}^{\mathcal{R}\models}_{\mathbb{P}(s^*)}$
This step is applying the rules defined by the user, it use SPARQL construct queries gathered into a rul file as described [here](https://files.inria.fr/corese/doc/rule.html)
```
 python 2_inferencesRules.py -r RULES_PATH -m insert
```

## STEP 3-  Wikicheck: $\mathcal{K}^{\mathcal{WR}\models}_{\mathbb{P}(s^*)}$
```
 python 3_WikicheckNamedGraph.py -s SHAPE_PATH -ng SEARCHSPACE_NAMEDGRAPH
```
