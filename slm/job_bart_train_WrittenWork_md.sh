#!/bin/bash
#
#### JOB INFO
#SBATCH --job-name=DS_turtle_BART_base_WrittenWOrk
#SBATCH --output=DS_turtle_BART_base_WrittenWOrk.txt
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
python ./src/train_withShape_withObj.py model=bart_base_model data=DS_turtleS_0datatype_1inLine_1facto_bart_train_writtenwork_abs_md train=bart_dbpedia