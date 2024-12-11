import omegaconf
import hydra
import torch
from transformers import AutoConfig,AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer, T5Tokenizer, AddedToken, RobertaTokenizer, AutoModelForCausalLM
import lightning.pytorch as pl
import json
from lightning.pytorch.utilities import rank_zero_info
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint, LearningRateMonitor
from lightning.pytorch.loggers.wandb import WandbLogger
from kfold.datamodule import KFoldDataModule
from rdflib import Graph
import wandb
from pl_data_modules import BasePLDataModule
from pl_modules import BasePLModule
from generate_samples import GenerateTextSamplesCallback
from token_norm import TokenNormalizer
from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer

# torch.cuda.empty_cache()
import gc

from codecarbon import OfflineEmissionsTracker

# gc.collect()
def report_gpu():
   print(torch.cuda.list_gpu_processes())
   gc.collect()
   torch.cuda.empty_cache()


def train(conf: omegaconf.DictConfig) -> None:
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

    print(">>>>>>>>>>>>>>>> LOAD VOCAB FILE")

    with open(conf.vocab_file, 'r') as f: 
        vocab_syntaxes = json.load(f) 


    print("--------")
  
    all_vocab = []
    if(conf.add_vocab==True):
        if("list" in conf.train_file):
                all_vocab=vocab_syntaxes["list"]
        elif("turtleS" in conf.train_file or "turtleLight" in conf.train_file or "TurtleUtlraLight" in conf.train_file):
                all_vocab=vocab_syntaxes["turtleS"]
        elif("tags" in conf.train_file):
                all_vocab=vocab_syntaxes["tags"]
        elif("json-ld" in conf.train_file):
                all_vocab=vocab_syntaxes["json-ld"]
        elif("ntriples" in conf.train_file):
                all_vocab=vocab_syntaxes["ntriples"]
        elif("turtle" in conf.train_file):
                all_vocab=vocab_syntaxes["turtle"]
        elif("xml" in conf.train_file):
                all_vocab=vocab_syntaxes["xml"]

        all_vocab=list(set(all_vocab))

    config = AutoConfig.from_pretrained(
        conf.config_name if conf.config_name else conf.model_name_or_path,
        decoder_start_token_id = 0,
        no_repeat_ngram_size = 0,
        dropout=conf.dropout,
        forced_bos_token_id=None,
        trust_remote_code=True

    )
    
    print("USE FAST >>>>>>>>>>>>",conf.use_fast_tokenizer)
    tokenizer_kwargs = {
        "use_fast": conf.use_fast_tokenizer,
    }
    if("codet5" in conf.model_name_or_path):
        tokenizer = RobertaTokenizer.from_pretrained(
            conf.tokenizer_name if conf.tokenizer_name else conf.model_name_or_path,
            trust_remote_code=True,
            **tokenizer_kwargs
        )
    elif("t5" in conf.model_name_or_path and not "flan-t5" in conf.model_name_or_path  and not "mt5" in conf.model_name_or_path and not "pile-t5" in conf.model_name_or_path ):
        tokenizer = T5Tokenizer.from_pretrained(
            conf.tokenizer_name if conf.tokenizer_name else conf.model_name_or_path,
            **tokenizer_kwargs
        )
    else:
        
        tokenizer = AutoTokenizer.from_pretrained(
            conf.tokenizer_name if conf.tokenizer_name else conf.model_name_or_path,
            **tokenizer_kwargs
        )

    print("============+>",conf.train_file)
  
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


    #if not conf.finetune:
    print("SIZE BEFORE >",len(tokenizer))
    print("TOKEN NORMALIZER INIT")
    normalizer=TokenNormalizer(conf.model_name_or_path)

    if("t5" in conf.dataset_name and conf.add_vocab==True):

        if("<s>" in all_vocab):
            all_vocab.remove("<s>") 
        if("["  in all_vocab):
            all_vocab.remove("[")
        if("]"  in all_vocab):
            all_vocab.remove("]")
        if("\n" in all_vocab):
            all_vocab.remove('\n')
            
        tokenizer.add_tokens(AddedToken("[", normalized=False))
        tokenizer.add_tokens(AddedToken("]", normalized=False))
        tokenizer.add_tokens(AddedToken("\n", normalized=False))
        tokenizer.add_tokens(AddedToken("<s>", normalized=False))
        for voc in all_vocab:
           tokenizer.add_tokens(AddedToken(voc, normalized=False))

    else:
            #https://stackoverflow.com/questions/72214408/why-does-huggingface-t5-tokenizer-ignore-some-of-the-whitespaces

        if(normalizer.byte_encoder):
            ##### BYTES ENCODE FOR POTENTIAL GRAMMAR CONSTRAINED DECODING
            norm_vocab=[]
            for voc in all_vocab:
                norm_vocab.append(normalizer.normalize(voc))
            tokenizer.add_tokens(norm_vocab)
                
        else:
            tokenizer.add_tokens(all_vocab)
    ## ADDED FOR PILET5
    if("pile-t5" in conf.model_name_or_path.lower()):
        tokenizer.add_special_tokens({'pad_token': '[PAD]'})

    ########### TEST IT

    model_name=conf.config_name.split("/")[-1]
    project=conf.project
    group=conf.syntax_name+"_"+model_name


    print("SAVE TOKENIZE VOCAB >")
    tokenizer.save_pretrained( f'experiments/experiments/{group}_tokenizer')
    print("SAVED TOKENIZE VOCAB !")


    print("SIZE AFTER >",len(tokenizer))
    model.resize_token_embeddings(len(tokenizer))

    ### ADDED FOR LOCAL
    #model.to(torch.device('cpu'))
        # data module declaration
    print("TRAIN FILE")
    print(conf.train_file)
    pl_data_module = BasePLDataModule(conf, tokenizer, model)

    train_dataloader=pl_data_module.train_dataloader()
    val_dataloader=pl_data_module.val_dataloader()
    




    tracker = OfflineEmissionsTracker(country_iso_code="FRA")

    if(conf.nb_folds==0 and conf.importance_sampling==False):

        print("===================> CREATE DIR")
        test_save={"test":"test"}
        with open( group+'test_save_nocv.json', "w") as outfile:
            json.dump(test_save, outfile)



        results, paths = [], []
        all_data_exp = {}

        pl_module = BasePLModule(conf, config, tokenizer, model, shacl_g,grammar_recognizer)
        wandblogger = WandbLogger(project = project, name = group,group=group)
        
        callbacks_store = []
        if conf.apply_early_stopping:
                callbacks_store.append(
                    EarlyStopping(
                        monitor=conf.monitor_var,
                        mode=conf.monitor_var_mode,
                        patience=conf.patience
                    )
                )

        checkpoint_callback=ModelCheckpoint(
                monitor=conf.monitor_var,
                # monitor=None,
                dirpath='experiments/'+group+'/',
                filename=group+'-{epoch:02d}-{val_loss:.2f}',
                save_top_k=conf.save_top_k,
                verbose=True,
                save_last=True,
                mode=conf.monitor_var_mode
            )
        callbacks_store.append(checkpoint_callback)

        callbacks_store.append(GenerateTextSamplesCallback(conf.samples_interval))
        callbacks_store.append(LearningRateMonitor(logging_interval='step'))

        trainer = pl.Trainer(
           # accelerator="cpu",#### ADDed
            #accelerator="cpu",
            devices=conf.gpus,
            accumulate_grad_batches=conf.gradient_acc_steps,
            gradient_clip_val=conf.gradient_clip_value,
            val_check_interval=conf.val_check_interval,
            callbacks=callbacks_store,
            max_steps=conf.max_steps,
            precision=conf.precision,
            logger=wandblogger,
            limit_val_batches=conf.val_percent_check
        )


        tracker.start()
        res=trainer.fit(pl_module, datamodule=pl_data_module)
        tracker.stop()


        all_data_exp["train_data"]=res
        all_data_exp["carbon_data"]={}

        all_data_exp["carbon_data"]["train_emissions"] = tracker.final_emissions_data.emissions
        all_data_exp["carbon_data"]["train_energy_consumed"] = tracker.final_emissions_data.energy_consumed

        print("=====================BEST MODEL")

        all_data_exp["best_model_path"]=checkpoint_callback.best_model_path

        print(">>>>>>>>>>>>>>>>>> TEST")
        tracker.start()
        res = trainer.test(model=pl_module, datamodule=pl_data_module, verbose=False)
        tracker.stop()

        all_data_exp["test_data_last_step"]=res
        all_data_exp["carbon_data"]["test_emissions"] = tracker.final_emissions_data.emissions
        all_data_exp["carbon_data"]["test_energy_consumed"] = tracker.final_emissions_data.energy_consumed

        wandb.finish()

        print("SAVE DATA")

        with open( group+'all_data.json', "w") as outfile:
            json.dump(results, outfile)
    elif(conf.nb_folds==0 and conf.importance_sampling==True):
        print("HEY")
    elif(conf.nb_folds > 0):

        print("===================> CREATE DIR")
        test_save={"test":"test"}
        with open( group+'test_save.json', "w") as outfile:
            json.dump(test_save, outfile)

        kfold_data_module=KFoldDataModule(
                num_folds=conf.nb_folds,
                shuffle=False,
                stratified=False,
                train_dataloader=train_dataloader,
                val_dataloaders=val_dataloader
            )

        models = [BasePLModule(conf, config, tokenizer, model, shacl_g,grammar_recognizer) for _ in range(conf.nb_folds)]

        results, paths = [], []
        all_data_exp = {}

        for i in range(conf.nb_folds):
            rank_zero_info(f"===== Starting fold {i+1}/{conf.nb_folds} =====")

           

            wandblogger = WandbLogger(project = project, name = group+"_"+str(i),group=group)
            all_data_exp["fold"+str(i)]={}
            callbacks_store = []
        
            if conf.apply_early_stopping:
                callbacks_store.append(
                    EarlyStopping(
                        monitor=conf.monitor_var,
                        mode=conf.monitor_var_mode,
                        patience=conf.patience
                    )
                )

            checkpoint_callback=ModelCheckpoint(
                    monitor=conf.monitor_var,
                    # monitor=None,
                    dirpath='experiments/'+group+'/',
                    #filename=group+"_"+str(i)+'-{epoch:02d}',
                    #every_n_epochs=1,
                    #save_top_k=-1,
                    # UNCOMMENT FOR BASIC CASE
                    filename=group+"_"+str(i)+'-{epoch:02d}-{val_loss:.2f}',
                    save_top_k=conf.save_top_k,
                    verbose=True,
                    save_last=True,
                    mode=conf.monitor_var_mode
                )
            callbacks_store.append(checkpoint_callback)

            callbacks_store.append(GenerateTextSamplesCallback(conf.samples_interval))
            callbacks_store.append(LearningRateMonitor(logging_interval='step'))

            kfold_data_module.fold_index=i
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
            print(">>>>>>>>>>>>>>>>>> TRAIN")
            tracker.start()
            res=trainer.fit(models[i], datamodule=kfold_data_module)
            tracker.stop()
            

            all_data_exp["fold"+str(i)]["train_data"]=res
            all_data_exp["fold"+str(i)]["carbon_data"]={}

            all_data_exp["fold"+str(i)]["carbon_data"]["train_emissions"] = tracker.final_emissions_data.emissions
            all_data_exp["fold"+str(i)]["carbon_data"]["train_energy_consumed"] = tracker.final_emissions_data.energy_consumed

                      #trainer.save_checkpoint(fold_path)
            #state=trainer.state
          

            print("=====================BEST MODEL")

            all_data_exp["fold"+str(i)]["best_model_path"]=checkpoint_callback.best_model_path


            print(">>>>>>>>>>>>>>>>>> TEST")
            tracker.start()

            res=trainer.test(models[i], datamodule=kfold_data_module)
            tracker.stop()
            all_data_exp["fold"+str(i)]["test_data_last_step"]=res
            all_data_exp["fold"+str(i)]["carbon_data"]["test_emissions"] = tracker.final_emissions_data.emissions
            all_data_exp["fold"+str(i)]["carbon_data"]["test_energy_consumed"] = tracker.final_emissions_data.energy_consumed

            wandb.finish()

        print("SAVE DATA")


        with open( group+'all_data.json', "w") as outfile:
            json.dump(all_data_exp, outfile)

@hydra.main(config_path='../conf', config_name='root')
def main(conf: omegaconf.DictConfig):
    train(conf)


if __name__ == '__main__':
   
   # print(torch.cuda.list_gpu_processes())
    #gc.collect()
    #torch.cuda.empty_cache()
    main()
