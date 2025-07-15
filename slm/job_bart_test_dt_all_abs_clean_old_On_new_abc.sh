#!/bin/bash
#################### OAR config
#OAR -O OAR_%jobid%.out
#OAR -E OAR_%jobid%.err

# display some information about attributed resources
hostname
nvidia-smi

module purge
module load conda
conda activate rdf_shape_env


export TOKENIZERS_PARALLELISM=True
export WANDB_API_KEY=5f4208dc97c7b3542281b94b64eb42833243cc71
python ./src/test_DS.py model=bart_base_model data=DS_turtleS_0datatype_1inLine_1facto_bart_test_obj_and_dt_prop_abs_clean_old_ON_new_abc train=bart_dbpedia
