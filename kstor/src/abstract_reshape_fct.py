#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:04:47 2023

@author: cringwal
"""

from transformers import BartForConditionalGeneration, AutoTokenizer, T5Tokenizer

def getShortenAbstract(model,entity,context_shorter ):
    max_token = 1024
    if("t5" in model):
        max_token = 512
    if("flan-t5" in model):
        max_token = 256

    if(model=="google/flan-t5-base"):    
        tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")
    if(model=="t5-base"):    
        tokenizer = T5Tokenizer.from_pretrained("t5-base")
    if(model=="t5-large"):    
        tokenizer = T5Tokenizer.from_pretrained("t5-large")
    if(model=="bart-large"):  
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large")
    if(model=="bart-base"):
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-base")
    
    
    entity=entity.replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")
    len_added=0
    if("bart" in model):
        len_added=len("<s>"+entity+" : "+"</s>")
    if("t5" in model):
        len_added=len("Translate English to syntax name : ["+ entity+"] <s></s>")
    
    tokenized=tokenizer.encode(context_shorter, add_special_tokens=True)

    n=0
    while(len(tokenized)+len_added>max_token):
        context_shorter=".".join([part for part in context_shorter.split(".") if part != ""][:-1])
        tokenized=tokenizer.encode(context_shorter, add_special_tokens=True)
        n += 1
    # if(context_shorter[0:3]=="<s>"):
    #     context_shorter=context_shorter[3:len(context_shorter)]
    return context_shorter

def CheckTriplesLength(model,context_shorter ):
    max_token = 1024
    if("t5" in model):
        max_token = 512
    if("flan-t5" in model):
        max_token = 256

    if(model=="google/flan-t5-base"):    
        tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")
    if(model=="t5-base"):    
        tokenizer = T5Tokenizer.from_pretrained("t5-base")
    if(model=="t5-large"):    
        tokenizer = T5Tokenizer.from_pretrained("t5-large")
    if(model=="bart-large"):  
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large")
    if(model=="bart-base"):
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-base")
    
    tokenized=tokenizer.encode(context_shorter, add_special_tokens=True)
    print(str(len(tokenized)),"/",str(max_token))
    if(len(tokenized)>max_token):
        return False
    else:
        return True
