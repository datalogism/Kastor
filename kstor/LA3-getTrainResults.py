#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 15:18:10 2024

@author: cringwal
"""

import wandb
from argparse import ArgumentParser
import pandas as pd


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-wapik", "--wandb_api_key", default=None)
    parser.add_argument("-wuser", "--wandb_user", default=None)
    parser.add_argument("-wproj", "--wandb_project", default=None)
    parser.add_argument("-output", "--dir_save", default=None)
    args = parser.parse_args()

    if args.wandb_api_key and args.wandb_user and args.wandb_project and args.dir_save:
        print(">>>>>>>>>>>>>>>>>>>>>>>>>> START HERE")
        save_dir=args.dir_save
        api = wandb.Api()
        API_KEY = args.wandb_api_key
        wandb.login(key=API_KEY)
        to_delete_in_name=["DS_turtleS_0datatype_1inLine_1facto_BART_","bart-base_"]
        user=args.wandb_user
        project=args.wandb_project
        runs= api.runs(
            path=user+"/"+project
        )

        cols=[ 'model','fold','test_BLEU', 'test_F1_macro', 'test_F1_micro', 'test_accuracy',
              'test_dist_edit', 'test_fn_rate', 'test_fp_rate', 'test_loss', 'test_part_parsed',
              'test_part_subj_ok', 'test_part_valid_r', 'test_part_valid_s', 'test_prec_macro', 'test_prec_micro', 'test_recall_macro',
              'test_recall_micro', "_runtime"]
        data_results=[]
        for run in runs:
            name_orig=run.name
            name=name_orig
            print(name)
            current_fold=name.split("_")[-1]
            print(current_fold)
            data_summary=run.summary
            if("train" in name and "V2" in name) or ("train" in name and "-" in name):
                model=run.group
                for token in to_delete_in_name:
                    model=model.replace(token,"")

                print(model,"->",current_fold)

                tempo={}
                for col in cols:
                    if col in data_summary.keys():
                       tempo[col]= data_summary[col]

                tempo["model"]=model
                tempo["fold"]=current_fold
                data_results.append(tempo)

        df = pd.DataFrame.from_dict(data_results)
        df.to_csv(save_dir+"Train_results_wb_export_Corrected.csv")
