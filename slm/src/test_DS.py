#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for sequence-to-sequence language models with grammar constraints.
This script handles model loading, testing, and evaluation with support for k-fold cross validation.
"""

import omegaconf
import hydra
import torch
from transformers import AutoConfig, AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer, T5Tokenizer, RobertaTokenizer, AutoModelForCausalLM
import lightning.pytorch as pl
import json
from lightning.pytorch.loggers.wandb import WandbLogger
from rdflib import Graph
import wandb
from pl_data_modules import BasePLDataModule
from pl_modules import BasePLModule
from generate_samples import GenerateNotParsedCallback, GenerateNotValidCallback, GenerateWrongSubjCallback, GenerateToInspectCallback
from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer
import gc
from codecarbon import OfflineEmissionsTracker
from collections import OrderedDict


def clean_and_load_CKPT(model, ckpt):
    """
    Load and clean model checkpoint state dictionary.
    Handles different model architectures by adjusting the state dict keys.
    
    Args:
        model: Model name or path
        ckpt: Path to checkpoint file
        
    Returns:
        OrderedDict: Cleaned state dictionary
    """
    checkpoint = torch.load(ckpt, map_location=torch.device('cpu'), weights_only=False)
    new_state_dict = OrderedDict()
    
    # Handle BART model architecture specifically
    if "bart" in model:
        for k, v in checkpoint["state_dict"].items():
            name = k.replace("model.model", "model")  # Fix model key structure
            if k in ["model.final_logits_bias", "model.lm_head.weight"]:
                name = k.replace("model.", "")
            new_state_dict[name] = v
    else:
        # Standard handling for other models
        for k, v in checkpoint["state_dict"].items():
            name = k.replace("model.", "")  # Remove 'model.' prefix
            new_state_dict[name] = v
    return new_state_dict


def report_gpu():
    """Utility function to report GPU memory usage and clean up CUDA cache."""
    print(torch.cuda.list_gpu_processes())
    gc.collect()
    torch.cuda.empty_cache()


def test(conf: omegaconf.DictConfig) -> None:
    """
    Main testing function that handles model loading and evaluation.
    
    Args:
        conf: Configuration object containing all test parameters
    """
    pl.seed_everything(conf.seed)
    
    print("Loading SHACL shape file:", conf.shape_file)
    shacl_g = Graph()
    shacl_g.parse(conf.shape_file)

    # Load grammar for constrained generation
    with open(conf.grammar_file, "r") as file:
        grammar_str = file.read()
    parsed_grammar = parse_ebnf(grammar_str)
    start_rule_id = parsed_grammar.symbol_table["root"]
    grammar_recognizer = StringRecognizer(parsed_grammar.grammar_encoding, start_rule_id)

    # Initialize model configuration
    model_name = conf.config_name.split("/")[-1]
    project = conf.project
    group = f"{conf.syntax_name}_{model_name}"
    
    # Load model config
    config = AutoConfig.from_pretrained(
        conf.config_name if conf.config_name else conf.model_name_or_path,
        decoder_start_token_id=0,
        no_repeat_ngram_size=0,
        dropout=conf.dropout,
        forced_bos_token_id=None,
        trust_remote_code=True
    )

    # Initialize appropriate tokenizer based on model type
    tokenizer_kwargs = {"use_fast": conf.use_fast_tokenizer}
    
    if "codet5" in conf.model_name_or_path:
        print("Using CodeT5 tokenizer")
        tokenizer = RobertaTokenizer.from_pretrained(
            conf.tkn_path,
            trust_remote_code=True,
            **tokenizer_kwargs
        )
    elif "t5" in conf.model_name_or_path and not any(x in conf.model_name_or_path for x in ["flan-t5", "mt5", "pile-t5"]):
        tokenizer = T5Tokenizer.from_pretrained(
            conf.tkn_path,
            **tokenizer_kwargs
        )
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            conf.tkn_path,
            **tokenizer_kwargs
        )

    # Initialize appropriate model
    print(f"Loading model from {conf.ckpt_path}")
    if "gpt" in conf.model_name_or_path:
        model = AutoModelForCausalLM.from_pretrained(
            conf.model_name_or_path,
            config=config,
        )
    elif "codet5p-220m" in conf.model_name_or_path:
        model = AutoModel.from_pretrained(
            conf.model_name_or_path,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            config=config
        )
    elif "codet5" in conf.model_name_or_path:
        model = AutoModelForSeq2SeqLM.from_pretrained(
            conf.model_name_or_path,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            config=config
        )
    else:
        model = AutoModelForSeq2SeqLM.from_pretrained(
            conf.model_name_or_path,
            config=config,
        )

    # Create output file for test results
    with open(f"{conf.test_save_dir}{group}_test.json", "w") as outfile:
        json.dump({"test": "test"}, outfile)

    # Single fold testing
    if conf.nb_folds == 0:
        _run_single_fold_test(conf, model, tokenizer, shacl_g, grammar_recognizer, group, project)
    # K-fold cross validation
    else:
        _run_kfold_validation(conf, model, tokenizer, shacl_g, grammar_recognizer, group, project)


def _run_single_fold_test(conf, model, tokenizer, shacl_g, grammar_recognizer, group, project):
    """Run testing for a single model checkpoint."""
    wandblogger = WandbLogger(project=project, name=f"{group}_0", group=group)
    
    # Load and clean checkpoint
    cpt_name = "last.ckpt"
    ckpt = clean_and_load_CKPT(conf.model_name_or_path, f"{conf.ckpt_path}{cpt_name}")
    model.resize_token_embeddings(len(tokenizer))
    model.load_state_dict(ckpt)

    # Initialize data module
    pl_data_module = BasePLDataModule(conf, tokenizer, model)
    
    # Initialize emissions tracker
    tracker = OfflineEmissionsTracker(country_iso_code="FRA")
    
    # Set up callbacks for generation and validation
    callbacks = [
        GenerateToInspectCallback(conf.samples_interval),
        GenerateNotParsedCallback(conf.samples_interval),
        GenerateNotValidCallback(conf.samples_interval),
        GenerateWrongSubjCallback(conf.samples_interval)
    ]
    
    # Initialize PyTorch Lightning module and trainer
    pl_module = BasePLModule(conf, model.config, tokenizer, model, shacl_g, grammar_recognizer)
    
    trainer = pl.Trainer(
        devices=conf.gpus,
        accumulate_grad_batches=conf.gradient_acc_steps,
        gradient_clip_val=conf.gradient_clip_value,
        val_check_interval=conf.val_check_interval,
        callbacks=callbacks,
        max_steps=conf.max_steps,
        precision=conf.precision,
        logger=wandblogger,
        limit_val_batches=conf.val_percent_check
    )
    
    # Run testing
    print("Starting test process...")
    tracker.start()
    results = trainer.test(model=pl_module, datamodule=pl_data_module, verbose=False)
    tracker.stop()
    
    # Save results
    all_data_exp = {
        "test_data_last_step": results,
        "carbon_data": {
            "test_emissions": tracker.final_emissions_data.emissions,
            "test_energy_consumed": tracker.final_emissions_data.energy_consumed
        }
    }
    
    with open(f"{conf.test_save_dir}{group}.json", "w") as outfile:
        json.dump(all_data_exp, outfile)


def _run_kfold_validation(conf, model, tokenizer, shacl_g, grammar_recognizer, group, project):
    """Run k-fold cross validation testing."""
    all_data_exp = {}
    
    for i in range(conf.nb_folds):
        print(f"===== Starting fold {i+1}/{conf.nb_folds} =====")
        
        # Initialize wandb logger for this fold
        wandblogger = WandbLogger(project=project, name=f"{group}_{i}", group=group)
        
        # Load checkpoint for this fold
        cpt_name = "last.ckpt" if i == 0 else f"last-v{i}.ckpt"
        all_data_exp[f"fold{i}"] = {}
        
        print(f"Loading checkpoint: {cpt_name}")
        ckpt = clean_and_load_CKPT(conf.model_name_or_path, f"{conf.ckpt_path}{cpt_name}")
        
        # Prepare model for this fold
        model.resize_token_embeddings(len(tokenizer))
        model.load_state_dict(ckpt)
        
        # Initialize data module and callbacks
        pl_data_module = BasePLDataModule(conf, tokenizer, model)
        callbacks = [
            GenerateToInspectCallback(conf.samples_interval),
            GenerateNotParsedCallback(conf.samples_interval),
            GenerateNotValidCallback(conf.samples_interval),
            GenerateWrongSubjCallback(conf.samples_interval)
        ]
        
        # Initialize PyTorch Lightning module with object extraction
        pl_module = BasePLModule(conf, model.config, tokenizer, model, shacl_g, grammar_recognizer, obj_ext=True)
        
        # Initialize trainer
        trainer = pl.Trainer(
            devices=conf.gpus,
            accumulate_grad_batches=conf.gradient_acc_steps,
            gradient_clip_val=conf.gradient_clip_value,
            val_check_interval=conf.val_check_interval,
            callbacks=callbacks,
            max_steps=conf.max_steps,
            precision=conf.precision,
            logger=wandblogger,
            limit_val_batches=conf.val_percent_check
        )
        
        # Run testing for this fold
        print(f"Starting test process for fold {i+1}...")
        results = trainer.test(model=pl_module, datamodule=pl_data_module, verbose=False)
        
        # Save fold results
        all_data_exp[f"fold{i}"]["test_data_last_step"] = results
        all_data_exp[f"fold{i}"]["carbon_data"] = {}
        
        # Clean up
        wandb.finish()
    
    # Save all fold results
    with open(f"{conf.test_save_dir}{group}.json", "w") as outfile:
        json.dump(all_data_exp, outfile)
    print("Test results saved successfully")


@hydra.main(config_path='../conf', config_name='root')
def main(conf: omegaconf.DictConfig):
    """Main entry point for the testing script."""
    test(conf)


if __name__ == '__main__':
    main()
