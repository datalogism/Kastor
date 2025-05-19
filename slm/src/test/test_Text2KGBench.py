import omegaconf
import hydra
import torch
from transformers import AutoConfig,AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer, T5Tokenizer, RobertaTokenizer, AutoModelForCausalLM
import lightning.pytorch as pl
import json
from lightning.pytorch.loggers.wandb import WandbLogger
from rdflib import Graph
import wandb
from pl_data_modules import BasePLDataModule
from pl_modules import BasePLModule
from generate_samples import  GenerateNotParsedCallback, GenerateNotValidCallback, GenerateWrongSubjCallback, GenerateToInspectCallback

from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer

import gc

from codecarbon import OfflineEmissionsTracker
from collections import OrderedDict

def clean_and_load_CKPT(model,ckpt):
    
    checkpoint=torch.load(ckpt,map_location=torch.device('cpu'),weights_only=False)
    new_state_dict = OrderedDict()
    if("bart" in model):
        for k, v in checkpoint["state_dict"].items():
            name = k.replace("model.model", "model") # remove `module.`
            if(k in ["model.final_logits_bias","model.lm_head.weight"]):
                name = k.replace("model.", "")
            new_state_dict[name] = v
    else:
        for k, v in checkpoint["state_dict"].items():
            name = k.replace("model.", "") # remove `module.`
            new_state_dict[name] = v
    return new_state_dict


def report_gpu():
   print(torch.cuda.list_gpu_processes())
   gc.collect()
   torch.cuda.empty_cache()

def test(conf: omegaconf.DictConfig) -> None:
    pl.seed_everything(conf.seed)
    
    print(">>>>>>>>>>>>>>>> EXTRACTION FROM SHAPE")
    print(conf.shape_file)

    shacl_g = Graph()
    shacl_g.parse(conf.shape_file)

    print(">>>>>>>>>>>>>>>> LOAD GRAMMAR")
    print(conf.shape_file)
    with open(conf.grammar_file, "r") as file:
        grammar_str = file.read()

    parsed_grammar = parse_ebnf(grammar_str)

    start_rule_id = parsed_grammar.symbol_table["root"]
    grammar_recognizer = StringRecognizer(parsed_grammar.grammar_encoding, start_rule_id)

    model_name=conf.config_name.split("/")[-1]
    project=conf.project
    group=conf.syntax_name+"_"+model_name
    print(">>>>>>>>>>>>>>>> LOAD VOCAB FILE")


    config = AutoConfig.from_pretrained(
        conf.config_name if conf.config_name else conf.model_name_or_path,
        decoder_start_token_id = 0,
        #early_stopping = False,
        no_repeat_ngram_size = 0,
        dropout=conf.dropout,
        forced_bos_token_id=None,
        trust_remote_code=True

    )
    
    print("LOAD TOKENIZER >>>>>>>>>>>>",conf.tkn_path)
    tokenizer_kwargs = {
        "use_fast": conf.use_fast_tokenizer,
        #"add_tokens": all_vocab
    }
    if("codet5" in conf.model_name_or_path):
        print("CODE T5 TOKENIZER")
        tokenizer = RobertaTokenizer.from_pretrained(
            conf.tkn_path,
            trust_remote_code=True,
            **tokenizer_kwargs
        )
    elif("t5" in conf.model_name_or_path and not "flan-t5" in conf.model_name_or_path  and not "mt5" in conf.model_name_or_path and not "pile-t5" in conf.model_name_or_path ):
        # torch.backends.cuda.matmul.allow_tf32 = True
        # torch.backends.cudnn.allow_tf32 = True
        tokenizer = T5Tokenizer.from_pretrained(
            conf.tkn_path,
            **tokenizer_kwargs
        )
    else:
        
        tokenizer = AutoTokenizer.from_pretrained(
            conf.tkn_path,
            **tokenizer_kwargs
        )

    print("============+ LOAD MODEL>",conf.ckpt_path)
  
    if("gpt" in conf.model_name_or_path):
        model = AutoModelForCausalLM.from_pretrained(
            conf.model_name_or_path,
            config=config,
        )
    elif("codet5p-220m" in conf.model_name_or_path):
        model = AutoModel.from_pretrained(
                conf.model_name_or_path,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                config=config)
    elif("codet5" in conf.model_name_or_path):
        model = AutoModelForSeq2SeqLM.from_pretrained(
                conf.model_name_or_path,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                config=config)
    else:
        model = AutoModelForSeq2SeqLM.from_pretrained(
            conf.model_name_or_path,
            config=config,
        )

    model_name=conf.config_name.split("/")[-1]
    project=conf.project
    group=conf.syntax_name+"_"+model_name
    with open(conf.test_save_dir+group+"_test.json", "w") as outfile:
            json.dump({"test":"test"}, outfile)

    if conf.nb_folds==1:
        ckpt=clean_and_load_CKPT(conf.model_name_or_path,conf.ckpt_path)

        model.resize_token_embeddings(len(tokenizer))
        model.load_state_dict( ckpt)


        ########### TEST IT

       

        print("SIZE AFTER >",len(tokenizer))


        ### ADDED FOR LOCAL
        #model.to(torch.device('cpu'))
            # data module declaration
        print("TRAIN FILE")
        print(conf.train_file)
        pl_data_module = BasePLDataModule(conf, tokenizer, model)
       # pl_data_module.load_from_checkpoint_custom(checkpoint_path = cpt, config = config, tokenizer = tokenizer, model = model)

        train_dataloader=pl_data_module.train_dataloader()
        val_dataloader=pl_data_module.val_dataloader()
        

        tracker = OfflineEmissionsTracker(country_iso_code="FRA")
        
        all_data_exp = {}

        pl_module = BasePLModule(conf, config, tokenizer, model, shacl_g,grammar_recognizer)

        callbacks_store = [GenerateToInspectCallback(conf.samples_interval), GenerateNotParsedCallback(conf.samples_interval), GenerateNotValidCallback(conf.samples_interval), GenerateWrongSubjCallback(conf.samples_interval)]

        print("BEFORE TRAINER")
        trainer = pl.Trainer(
           # accelerator="cpu",#### ADDed
            #accelerator="cpu",
           # gpus=conf.gpus,
            devices=conf.gpus,
            accumulate_grad_batches=conf.gradient_acc_steps,
            gradient_clip_val=conf.gradient_clip_value,
            val_check_interval=conf.val_check_interval,
            callbacks=callbacks_store,
            max_steps=conf.max_steps,
            # max_steps=total_steps,
            precision=conf.precision,
            #amp_level=conf.amp_level,
            logger=wandblogger,
            #ckpt_path=conf.checkpoint_path,
            limit_val_batches=conf.val_percent_check
        )
        print("==================================================")
        print('START TEST PROCESS')
        tracker.start()
        results = trainer.test(model=pl_module, datamodule=pl_data_module, verbose=False)
        tracker.stop()
        #wandb.finish()

        all_data_exp["test_data_last_step"]=results
        all_data_exp["carbon_data"]={}
        all_data_exp["carbon_data"]["test_emissions"] = tracker.final_emissions_data.emissions
        all_data_exp["carbon_data"]["test_energy_consumed"] = tracker.final_emissions_data.energy_consumed

        with open(conf.test_save_dir+group+".json", "w") as outfile:
            json.dump(all_data_exp, outfile)

    elif(conf.nb_folds > 0):

        

        all_data_exp = {}

        for i in range(conf.nb_folds):

            wandblogger = WandbLogger(project = project, name = group+"_"+str(i),group=group)
            cpt_name="last.ckpt"
            if(i != 0):
                cpt_name="last-v"+str(i)+".ckpt"

            all_data_exp["fold"+str(i)]={}
            print(f"===== Starting fold {i}/{conf.nb_folds} =====")
            print("-",cpt_name)
            ckpt=clean_and_load_CKPT(conf.model_name_or_path,conf.ckpt_path+cpt_name)

            model.resize_token_embeddings(len(tokenizer))
            model.load_state_dict( ckpt)


            ########### TEST IT

            model_name=conf.config_name.split("/")[-1]
            project=conf.project
            group=conf.syntax_name+"_"+model_name

            print("SIZE AFTER >",len(tokenizer))


            ### ADDED FOR LOCAL
            #model.to(torch.device('cpu'))
                # data module declaration
            print("TRAIN FILE")
            print(conf.train_file)
            pl_data_module = BasePLDataModule(conf, tokenizer, model)
           # pl_data_module.load_from_checkpoint_custom(checkpoint_path = cpt, config = config, tokenizer = tokenizer, model = model)

            train_dataloader=pl_data_module.train_dataloader()
            val_dataloader=pl_data_module.val_dataloader()
            

            tracker = OfflineEmissionsTracker(country_iso_code="FRA")

            pl_module = BasePLModule(conf, config, tokenizer, model, shacl_g, grammar_recognizer, obj_ext=True)
            #pl_module = BasePLModule(conf, config, tokenizer, model, shacl_g,grammar_recognizer)
            callbacks_store = [GenerateToInspectCallback(conf.samples_interval), GenerateNotParsedCallback(conf.samples_interval), GenerateNotValidCallback(conf.samples_interval), GenerateWrongSubjCallback(conf.samples_interval)]

            print("CALL BACK")   
     
            print("BEFORE TRAINER")
            trainer = pl.Trainer(
               # accelerator="cpu",#### ADDed
                #accelerator="cpu",
               # gpus=conf.gpus,
                devices=conf.gpus,
                accumulate_grad_batches=conf.gradient_acc_steps,
                gradient_clip_val=conf.gradient_clip_value,
                val_check_interval=conf.val_check_interval,
                callbacks=callbacks_store,
                max_steps=conf.max_steps,
                # max_steps=total_steps,
                precision=conf.precision,
                #amp_level=conf.amp_level,
                logger=wandblogger,
                #ckpt_path=conf.checkpoint_path,
                limit_val_batches=conf.val_percent_check
            )
            print("==================================================")
            print('START TEST PROCESS')
            tracker.start()
            results = trainer.test(model=pl_module, datamodule=pl_data_module, verbose=False)
            tracker.stop()
            #wandb.finish()

            all_data_exp["fold"+str(i)]["test_data_last_step"]=results
            all_data_exp["fold"+str(i)]["carbon_data"]={}
            all_data_exp["fold"+str(i)]["carbon_data"]["test_emissions"] = tracker.final_emissions_data.emissions
            all_data_exp["fold"+str(i)]["carbon_data"]["test_energy_consumed"] = tracker.final_emissions_data.energy_consumed

            
            wandb.finish()
        with open(conf.test_save_dir+group+".json", "w") as outfile:
            json.dump(all_data_exp, outfile)
        print("===================> CREATE DIR")

@hydra.main(config_path='../../conf', config_name='root')
def main(conf: omegaconf.DictConfig):
    test(conf)


if __name__ == '__main__':
   
   # print(torch.cuda.list_gpu_processes())
    #gc.collect()
    #torch.cuda.empty_cache()
    main()
