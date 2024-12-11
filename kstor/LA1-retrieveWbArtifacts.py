#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 08:02:23 2024

@author: cringwal
"""

import json 
import pandas as pd
import os
import wandb

api = wandb.Api()
API_KEY="YOURAPIKEY"
user="inria_test"
project="YOURWANDBPROJECT"

group="YOURMODEL" # here the model must be a test done a on RD dataset with a model M
current_dir=group.replace("DS_turtleS_0datatype_1inLine_1facto_BART_","").replace("_bart-base","")
dir_save="./Artifacts/"

wandb.login(key=API_KEY)

if not os.path.exists(dir_save+current_dir):
    os.makedirs(dir_save+current_dir)
    
dir_save+current_dir
runs= api.runs(
    path=user+"/"+project,
    filters={"$or": [{"group": group}]}
)
for run in runs:
    name=run.name
    print(name)
    fold_nb=name.split("_")[-1]
    run_dir=dir_save+current_dir+"/"+fold_nb
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
        
    for artifact in run.logged_artifacts():
      if artifact.type == "run_table":
          print(artifact.name)
          table_dir = artifact.download(root=run_dir)

tables_files = ["To Inspect table.table.json", "NotParsed.table.json", "Notvalid.table.json", "WrongSubject.table.json"]
dirs = os.listdir(dir_save)

for dir_ in dirs:
    curent_dir = dir_save + dir_
    subdirs = os.listdir(curent_dir)

    tables_files_dict = {}
    for file in tables_files:
        tables_files_dict[file] = []
    for subdir_ in subdirs:
        current_subdir = curent_dir + "/" + subdir_
        for table in tables_files:
            if os.path.isfile(os.path.join(current_subdir, table)):
                with open(os.path.join(current_subdir, table)) as current_file:
                    data = json.load(current_file)
                    colnames = data["columns"]
                    row_data = data["data"]
                    for idx_i in range(len(row_data)):

                        tempo = {}
                        for idx_j in range(len(colnames)):
                            tempo[colnames[idx_j]] = row_data[idx_i][idx_j]
                            if (len(tempo.keys()) > 0):
                                if (tempo not in tables_files_dict[table]):
                                    tables_files_dict[table].append(tempo)

    for k in tables_files_dict.keys():
        curent_file = curent_dir + "/" + k
        with open(curent_file, 'w') as f:
            json.dump(tables_files_dict[k], f)

    #### SAVE TO INSPECT INTO CSV
    df = pd.DataFrame(tables_files_dict["To Inspect table.table.json"])

    df.to_csv(curent_dir + "/" + 'ToInspectData.csv', encoding='utf-8', index=True)