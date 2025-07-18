# 🔬 Knowledge distillation
![kstor](../img/knowledgedistill4.png)

## KD-STEP 0 [OPTIONNAL] - Create a data partition for a specific purpose 

In the case of our last work, we proposed to identify Wikipedia articles published after a given date, see [1_KD-0_createwikidiff_NG.py](../kstor/1_KD-0_createwikidiff_NG.py) for details

## KD-STEP 1-  Tag the entities related to the shape class: 

This step associates a random uuid to each entity related to dbo:class focused by the maximal shape chosen and having an abstract, it creates $\mathcal{K}_{\mathbb{P}(s^*)}$ . The dbo:Person shape is accessible here [PersonShape.ttl](../shapes/PersonShape.ttl)
```
python KD1_initializeKastorFromShape.py -s SHAPE_PATH
```
We can then get a sample of  $\mathcal{K}_{\mathbb{P}(s^*)}$ [with a SPARQL query](../corese/sparql_queries/get_sample_K_P_s_star.sparql)

## KD-STEP 2-  Run inferences rules (optional):
This step is applying the rules defined by the user and create $\mathcal{G}^{\mathcal{R}\models}_{\mathbb{P}(s^*)}$, it uses SPARQL construct queries gathered into a rul file as described [here](https://files.inria.fr/corese/doc/rule.html)
```
 python KD2_inferencesRules.py -r RULES_PATH -m insert
```
In [REF] we applied in our case the following rules: 
$$dbo:deathDate \models dbo:deathYear$$ and  $$dbo:birthDate  \models dbo:birthYear$$ available in [./rules/Person_rules.rul](../kstor/rules/Person_rules.rul) file

We can then count the number of triples infered [ with a SPARQL query](../corese/sparql_queries/get_inferences_nb.sparql)

We proposed in [REF] a new set of rules in [./rules/Person_dataobj_rules_NS.rul](../kstor/rules/Person_dataobj_rules_NS.rul)

### KD-STEP 3-  the Wikicheck: 

#### 3-1: Based on the Plain abstracts and only effective for the datatypes properties

The [1_KD-31_wikicheck_plain_dt_only](../kastor/1_KD-31_wikicheck_plain_dt_only.py) script check if the values of the datatype properties objects could be found in the Wikipedia abstracts, it creates $\mathcal{K}^{\mathcal{WR}\models}_{\mathbb{P}(s^*)}$
```
 python 1_KD-31_wikicheck_plain_dt_only.py -s SHAPE_PATH -ng SEARCHSPACE_NAMEDGRAPH
```
We can then count the number of entities in $\mathcal{K}^{\mathcal{WR}\models}_{\mathbb{P}(s^*)}$ [ with a SPARQL query](../corese/sparql_queries/get_found_in_abstract_nb.sparql)

### 3-2: Based on the Markdown abstracts and effective for both object and datatypes properties
![kstor](../img/Wikicheck(2).png)

To make possible the Wikicheck of Object Properties we propose to rely the verification on a simplified Markdown version of the Wikipedia page.
This process is depending of two steps :
1. the retrieval of the Wikipedia Markdown version of the abstracts and the recording of them in the KG via the [1_KD-321_RetrieveWikiMD](../kastor/1_KD-321_RetrieveWikiMD.py) script:
```
 python 1_KD-321_RetrieveWikiMD.py -s SHAPE_PATH
```
2. The wikicheck is then applied on the retrieved Markdown articles :
```
 python KD3-21_RetrieveWikiMD.py -s SHAPE_PATH -ng SEARCHSPACE_NAMEDGRAPH
```

## KD-STEP 4 - The exemples-specific patterns 
This script is used to analyse the example-specific patterns set $\mathbb{P}_{\mathcal{K}}(s^*)$ 
```
 python 1_KD-321_RetrieveWikiMD -s SHAPE_PATH -output output_dir -ng named_graph_sample 
```
Result will be saved in [a csv file](../XP_results/XP1/outputs/results_data/RDF_motif_foundNG_for_graph.csv); note that the given script could be also used on a sample level (see results on [DR0](../XP_results/XP1/outputs/results_data/RDF_motif_sample_0.csv),DR2,DR-..) 

## KD-STEP 5-  Create a Random Sample
This script was used to create $DR^0$, $DR^1$, $DR^2$
```
 python KD5_CreateNewRandomSample.py -s SHAPE_PATH -sz 1200 
```
A sample can then be described with a [SPARQL query](./corese/sparql_queries/get_sample_nli_stats.sparql)

## KD-STEP 6-  Export a TurtleLight dataset for training a SLM
Export a previously create sample in TurtleLight datasets splitted in train/test/eval  
```
 python KD6_createTurtleLightdatasetFromNG.py -s SHAPE_PATH -output output_dir -ng named_graph_sample 
```

examples of samples produced is given in [DS_turtleS_0datatype_1inLine_1facto_train_sample.json](./samples/DS_turtleS_0datatype_1inLine_1facto_train_sample.json)
