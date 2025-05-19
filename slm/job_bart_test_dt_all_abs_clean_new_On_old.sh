#!/bin/bash
#
#### JOB INFO
#SBATCH --job-name=DS_turtleS_0datatype_1inLine_1facto_bart_test_obj_and_dt_prop_abs_clean_new_ON_old
#SBATCH --output=DS_turtleS_0datatype_1inLine_1facto_bart_test_obj_and_dt_prop_abs_clean_new_ON_old.txt
###### CONF
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --account=rdf
####### CONTACT
#SBATCH --mail-user=celian.ringwald@inria.fr
#SBATCH --mail-type=BEGIN,END,FAIL
######### GPU
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu

module purge
module load miniconda
conda activate env_shapes

export TOKENIZERS_PARALLELISM=True
export WANDB_API_KEY=5f4208dc97c7b3542281b94b64eb42833243cc71
python ./src/test_DS.py  model=bart_base_model data=DS_turtleS_0datatype_1inLine_1facto_bart_test_obj_and_dt_prop_abs_clean_new_ON_old train=bart_dbpedia