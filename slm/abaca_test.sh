#!/bin/bash
#################### OAR config
#OAR -q production
#OAR -l host=1/gpu=1
#OAR -l walltime=3:00:00
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
echo "test message START" | mailx -s "Test" celian.ringwald@inria.fr
ls -l
echo "test message END" | mailx -s "Test" celian.ringwald@inria.fr