#!/bin/bash
#
#### JOB INFO
#SBATCH --job-name=$JOB_NAME$
#SBATCH --output=$LOGS_OUPUT_FILE$
###### CONF
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#SBATCH --account=$YOURACCOUNT$
####### CONTACT
#SBATCH --mail-user=$YOURMAIL$
#SBATCH --mail-type=BEGIN,END,FAIL
######### GPU
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu

module purge
module load miniconda
conda activate env_shapes

export TOKENIZERS_PARALLELISM=True
export WANDB_API_KEY="YOURAPIKEY"
python ./src/train_withShape.py model=bart_base_model data=YOURDATACONFIGFILE train=bart_dbpedia