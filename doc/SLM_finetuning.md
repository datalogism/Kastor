# SLM finetuning modules

All the current code is extending [12ShadesOfRDFSyntax](https://github.com/datalogism/12ShadesOfRDFSyntax)

## STEP0- CONDA ENV config

Please create a Python environment based on [requierements.txt](./requierements.txt)

## STEP1 - Train a model

* First config the data files [DS_turtleS_0datatype_1inLine_1facto_bart_train_init](./conf/data/DS_turtleS_0datatype_1inLine_1facto_bart_train_init.yaml): 
this one must point to your datasets / to your WanDB config / your SHACL shape / training set size and split config
* Train your model via slurm via [../job_bart_train_init.sh](job_bart_train_init.sh)
* The resulting model, checkpoints and basic statistics will be recorded into the current *./outputs/* dir

The process will callback and send the metrics, as well as, samples of the data computed during the training on a given WanDB plateform


## STEP2 - Test a model

* First config the data files [DS_turtleS_0datatype_1inLine_1facto_bart_test_init](./conf/data/DS_turtleS_0datatype_1inLine_1facto_bart_test_init.yaml): 
this one must point to your datasets / to your WanDB config / your SHACL shape/training set size and split config
It must also point to the checkpoint of your models as well as to the tokenizer you finetuned during the last step
* Train your model via slurm via [job_bart_test_init.sh](job_bart_test_init.sh)
* The metrics and performance results computed will be recorded into the defined *test_save_dir* 

The process will callback and send the metrics computed during the test on a given WanDB plateform: 
it will record the parsing errors, the FP/FN triples underlined during the process, the errors of subject made during the prediction and the list of all the examples-specific patterns generated that isn't following the expected one ($\widehat{\mathbb{G}}^{\nleftrightarrow}_{D}$)


## Finetunings options

- The KASTOR extractor could be obtained using different linearization technics, or models all theses detailed are available in our previous work : [12ShadesOfRDF](https://github.com/datalogism/12ShadesOfRDFSyntax)
- We recently propose the usage of custom Loss function, all of them are available in 
