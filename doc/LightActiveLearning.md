# 📥 Light Active SLM learning

> This part is specific to the work [REF]

![kstor](../img/ActiveLearningFinal.png)
## STEP LA0- Train a model
Please follow the instructions given in [SLM section](../slm/)

## STEP LA1- Test a model and retrieve errors
```
 python LA1-retrieveWbArtifacts.py  -wapik YOU_API_KEY -wuser YOUR_USER_NAME -wproj YOUR_WDB_PROJECT -wgroup YOUR_WDB_group -output /OUTPUT_DIR/
```
The resulting */OUTPUT_DIR/ToInspectTable.csv* file is dedicated to the latter annotation.


## STEP LA2- Annotate the FP/FN triples And Push the annotations to the KB

The */OUTPUT_DIR/ToInspectTable.csv* file contains two specifics columns dedicated to the annotation:
* The column "verif" is dedicated to classify as *TRUE* or *FALSE* classification. 
* The column "reason" allows the annotation given the typology of errors proposed in the paper
```
 python LA2-PushAnnotationsToKB.py   -s SHAPE_PATH -annot annotated_file -samp named_graph_sample 
```
