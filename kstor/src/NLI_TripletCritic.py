#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 13:58:18 2024
"""
import transformers 

model_name_or_path0 = 'joeddav/xlm-roberta-large-xnli'
model_name_or_path1="Babelscape/mdeberta-v3-base-triplet-critic-xnli"
tokenizer0 = transformers.AutoTokenizer.from_pretrained(
model_name_or_path0)
tokenizer1 = transformers.AutoTokenizer.from_pretrained(
model_name_or_path1)
model_config0 = transformers.AutoConfig.from_pretrained(
model_name_or_path0,
 # num_labels=2,
output_hidden_states=True,
output_attentions=True,
)
model_config1 = transformers.AutoConfig.from_pretrained(
model_name_or_path1,
# num_labels=2,
output_hidden_states=True,
output_attentions=True,
)
model_0 = transformers.AutoModelForSequenceClassification.from_pretrained(model_name_or_path0, config = model_config0)
model_1 = transformers.AutoModelForSequenceClassification.from_pretrained(model_name_or_path1, config = model_config1)

def get_XNLI_proba(row):
    
    verbalized= row["ent_uri"].replace("_", " ")+" "+row["prop"]+" "+ row["value"]
    encoded_input = tokenizer0(
     row["abstract"],verbalized,
    return_tensors="pt",
    add_special_tokens=True,
    max_length=256,
    padding='longest',
    return_token_type_ids=False,
    truncation_strategy='only_first')
    outputs = model_0(**encoded_input, return_dict=True, output_attentions=False, output_hidden_states = False)
    probs = outputs['logits'].softmax(dim=1)
    prob_label_is_true = probs[:,1]
    return float(prob_label_is_true[0])

def getTripletCritic_proba(row):
    verbalized= row["ent_uri"].replace("_", " ")+" "+row["prop"]+" "+ row["value"]
    encoded_input = tokenizer1(
    row["abstract"],verbalized,
    return_tensors="pt",
    add_special_tokens=True,
    max_length=256,
    padding='longest',
    return_token_type_ids=False,
    truncation_strategy='only_first')
    outputs = model_1(**encoded_input, return_dict=True, output_attentions=False, output_hidden_states = False)
    probs = outputs['logits'].softmax(dim=1)
    prob_label_is_true = probs[:,1]
    
    return float(prob_label_is_true[0])
