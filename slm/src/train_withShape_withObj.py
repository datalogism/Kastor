"""
Train a sequence-to-sequence language model with SHACL shape constraints and object extraction.

This script implements a training pipeline for fine-tuning language models (like T5, GPT, etc.)
with the ability to generate structured outputs that conform to SHACL shapes. It includes
support for k-fold cross-validation, grammar-constrained decoding, and carbon emission tracking.
"""

# Standard library imports
import json
import gc

# Third-party imports
import omegaconf
import hydra
import torch
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint, LearningRateMonitor
from lightning.pytorch.loggers.wandb import WandbLogger
from rdflib import Graph
import wandb
from codecarbon import OfflineEmissionsTracker

# Hugging Face transformers imports
from transformers import (
    AutoConfig, AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer,
    T5Tokenizer, AddedToken, RobertaTokenizer, AutoModelForCausalLM
)

# Local imports
from kfold.datamodule import KFoldDataModule
from pl_data_modules import BasePLDataModule
from pl_modules import BasePLModule
from generate_samples import (
    GenerateTextSamplesCallback, GenerateNotParsedCallback,
    GenerateNotValidCallback, GenerateWrongSubjCallback, GenerateToInspectCallback
)
from token_norm import TokenNormalizer
from transformers_cfg.parser import parse_ebnf
from transformers_cfg.recognizer import StringRecognizer

# Uncomment to enable GPU memory cleanup
# torch.cuda.empty_cache()

def report_gpu():
    """Print GPU memory usage and clean up CUDA cache."""
    print(torch.cuda.list_gpu_processes())
    gc.collect()
    torch.cuda.empty_cache()


def train(conf: omegaconf.DictConfig) -> None:
    """
    Main training function for the language model with shape constraints.
    
    Args:
        conf: Configuration dictionary containing all training parameters
    """
    # Set random seed for reproducibility
    pl.seed_everything(conf.seed)

    print(">>>>>>>>>>>>>>>> EXTRACTION FROM SHAPE")
    print(conf.shape_file)

    # Load SHACL shapes for validation
    shacl_g = Graph()
    shacl_g.parse(conf.shape_file)

    # Load class counts if provided (for class balancing)
    if conf.class_count_file and str(conf.class_count_file) != "None":
        with open(conf.class_count_file, 'r') as f:
            class_count = json.load(f)
    else:
        class_count = None

    print("Loading grammar from:", conf.grammar_file)
    with open(conf.grammar_file, "r") as file:
        grammar_str = file.read()

    # Parse grammar for constrained decoding
    parsed_grammar = parse_ebnf(grammar_str)
    start_rule_id = parsed_grammar.symbol_table["root"]
    grammar_recognizer = StringRecognizer(parsed_grammar.grammar_encoding, start_rule_id)

    # Load vocabulary file
    print("Loading vocabulary from:", conf.vocab_file)
    with open(conf.vocab_file, 'r') as f:
        vocab_syntaxes = json.load(f)

    # Select appropriate vocabulary based on input format
    all_vocab = []
    if conf.add_vocab:
        if "list" in conf.train_file:
            all_vocab = vocab_syntaxes["list"]
        elif any(x in conf.train_file for x in ["turtleS", "turtleLight", "TurtleUtlraLight"]):
            all_vocab = vocab_syntaxes["turtleS"]
        elif "tags" in conf.train_file:
            all_vocab = vocab_syntaxes["tags"]
        elif "json-ld" in conf.train_file:
            all_vocab = vocab_syntaxes["json-ld"]
        elif "ntriples" in conf.train_file:
            all_vocab = vocab_syntaxes["ntriples"]
        elif "turtle" in conf.train_file:
            all_vocab = vocab_syntaxes["turtle"]
        elif "xml" in conf.train_file:
            all_vocab = vocab_syntaxes["xml"]

        # Add markdown symbols to vocabulary
        markdown_symb = ["[", "]", "(", ")", "**"]
        for symb in markdown_symb:
            if symb not in all_vocab:
                all_vocab.append(symb)

        all_vocab = list(set(all_vocab))

    # Load model configuration
    config = AutoConfig.from_pretrained(
        conf.config_name if conf.config_name else conf.model_name_or_path,
        decoder_start_token_id=0,
        no_repeat_ngram_size=0,
        dropout=conf.dropout,
        forced_bos_token_id=None,
        trust_remote_code=True
    )

    # Initialize tokenizer based on model type
    print("Using fast tokenizer:", conf.use_fast_tokenizer)
    tokenizer_kwargs = {"use_fast": conf.use_fast_tokenizer}
    
    if "codet5" in conf.model_name_or_path:
        tokenizer = RobertaTokenizer.from_pretrained(
            conf.tokenizer_name if conf.tokenizer_name else conf.model_name_or_path,
            trust_remote_code=True,
            **tokenizer_kwargs
        )
    elif ("t5" in conf.model_name_or_path and 
          not any(x in conf.model_name_or_path for x in ["flan-t5", "mt5", "pile-t5"])):
        tokenizer = T5Tokenizer.from_pretrained(
            conf.tokenizer_name if conf.tokenizer_name else conf.model_name_or_path,
            **tokenizer_kwargs
        )
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            conf.tokenizer_name if conf.tokenizer_name else conf.model_name_or_path,
            **tokenizer_kwargs
        )

    # Load the appropriate model type
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
            config=config)
    elif "codet5" in conf.model_name_or_path:
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

    # Initialize token normalizer and update tokenizer with special tokens
    print("Tokenizer size before adding special tokens:", len(tokenizer))
    normalizer = TokenNormalizer(conf.model_name_or_path)

    if "t5" in conf.dataset_name and conf.add_vocab:
        # Clean up vocabulary for T5 models
        for token in ["<s>", "[", "]", "\n"]:
            if token in all_vocab:
                all_vocab.remove(token)

        # Add special tokens
        for token in ["[", "]", "\n", "<s>"] + all_vocab:
            tokenizer.add_tokens(AddedToken(token, normalized=False))
    else:
        # Handle vocabulary normalization for other models
        if normalizer.byte_encoder:
            normalized_vocab = [normalizer.normalize(voc) for voc in all_vocab]
            tokenizer.add_tokens(normalized_vocab)
        else:
            tokenizer.add_tokens(all_vocab)

    # Special handling for Pile-T5 models
    if "pile-t5" in conf.model_name_or_path.lower():
        tokenizer.add_special_tokens({'pad_token': '[PAD]'})

    # Save tokenizer and update model embeddings
    model_name = conf.config_name.split("/")[-1]
    project = conf.project
    group = f"{conf.syntax_name}_{model_name}"
    
    print("Saving tokenizer to:", f'experiments/experiments/{group}_tokenizer')
    tokenizer.save_pretrained(f'experiments/experiments/{group}_tokenizer')
    
    print("Tokenizer size after adding special tokens:", len(tokenizer))
    model.resize_token_embeddings(len(tokenizer))

    # Initialize data module
    print("Training file:", conf.train_file)
    pl_data_module = BasePLDataModule(conf, tokenizer, model)
    train_dataloader = pl_data_module.train_dataloader()
    val_dataloader = pl_data_module.val_dataloader()

    # Set up carbon emissions tracking
    tracker = OfflineEmissionsTracker(country_iso_code="FRA")

    # Training without cross-validation
    if conf.nb_folds == 0:
        print("Starting training without cross-validation")
        
        # Create directory for saving results
        with open(group + 'test_save_nocv.json', "w") as outfile:
            json.dump({"test": "test"}, outfile)

        all_data_exp = {}
        pl_module = BasePLModule(
            conf, config, tokenizer, model, 
            shacl_g, grammar_recognizer, obj_ext=True, class_count=class_count
        )
        
        # Initialize Weights & Biases logger
        wandblogger = WandbLogger(project=project, name=group, group=group)

        # Set up callbacks
        callbacks_store = [
            GenerateToInspectCallback(conf.samples_interval),
            GenerateNotParsedCallback(conf.samples_interval),
            GenerateNotValidCallback(conf.samples_interval),
            GenerateWrongSubjCallback(conf.samples_interval)
        ]

        # Add early stopping if enabled
        if conf.apply_early_stopping:
            callbacks_store.append(
                EarlyStopping(
                    monitor=conf.monitor_var,
                    mode=conf.monitor_var_mode,
                    patience=conf.patience
                )
            )

        # Configure model checkpointing
        checkpoint_callback = ModelCheckpoint(
            monitor=conf.monitor_var,
            dirpath='experiments/' + group + '/',
            filename=group + '-{epoch:02d}-{val_loss:.2f}',
            save_top_k=conf.save_top_k,
            verbose=True,
            save_last=True,
            mode=conf.monitor_var_mode
        )
        callbacks_store.extend([
            checkpoint_callback,
            GenerateTextSamplesCallback(conf.samples_interval),
            LearningRateMonitor(logging_interval='step')
        ])

        # Initialize trainer
        trainer = pl.Trainer(
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

        # Start training with carbon tracking
        tracker.start()
        train_result = trainer.fit(pl_module, datamodule=pl_data_module)
        tracker.stop()

        # Save training results and carbon data
        all_data_exp["train_data"] = train_result
        all_data_exp["carbon_data"] = {
            "train_emissions": tracker.final_emissions_data.emissions,
            "train_energy_consumed": tracker.final_emissions_data.energy_consumed
        }
        all_data_exp["best_model_path"] = checkpoint_callback.best_model_path

        # Run testing
        print("Running evaluation on test set")
        tracker.start()
        test_result = trainer.test(model=pl_module, datamodule=pl_data_module, verbose=False)
        tracker.stop()

        # Save test results and carbon data
        all_data_exp["test_data_last_step"] = test_result
        all_data_exp["carbon_data"].update({
            "test_emissions": tracker.final_emissions_data.emissions,
            "test_energy_consumed": tracker.final_emissions_data.energy_consumed
        })

        # Finalize W&B run
        wandb.finish()

        # Save all experiment data
        with open(group + 'all_data.json', "w") as outfile:
            json.dump(all_data_exp, outfile)

    # Training with k-fold cross-validation
    else:
        print(f"Starting {conf.nb_folds}-fold cross-validation")
        
        # Create directory for saving results
        with open(group + 'test_save.json', "w") as outfile:
            json.dump({"test": "test"}, outfile)

        # Initialize k-fold data module
        kfold_data_module = KFoldDataModule(
            num_folds=conf.nb_folds,
            shuffle=False,
            stratified=conf.stratified,
            train_dataloader=train_dataloader,
            val_dataloaders=val_dataloader
        )

        # Initialize models for each fold
        models = [
            BasePLModule(conf, config, tokenizer, model, shacl_g, grammar_recognizer, 
                        obj_ext=True, class_count=class_count)
            for _ in range(conf.nb_folds)
        ]

        all_data_exp = {}
        start_fold = conf.get('start_fold', 0)
        
        print(f"Starting from fold: {start_fold}")
        
        # Train each fold
        for i in range(start_fold, conf.nb_folds):
            print(f"===== Starting fold {i + 1}/{conf.nb_folds} =====")
            
            wandblogger = WandbLogger(project=project, name=f"{group}_{i}", group=group)
            all_data_exp[f"fold{i}"] = {}
            
            # Set up callbacks for this fold
            callbacks_store = [
                GenerateToInspectCallback(conf.samples_interval),
                GenerateNotParsedCallback(conf.samples_interval),
                GenerateNotValidCallback(conf.samples_interval),
                GenerateWrongSubjCallback(conf.samples_interval)
            ]

            # Add early stopping if enabled
            if conf.apply_early_stopping:
                callbacks_store.append(
                    EarlyStopping(
                        monitor=conf.monitor_var,
                        mode=conf.monitor_var_mode,
                        patience=conf.patience
                    )
                )

            # Configure model checkpointing for this fold
            checkpoint_callback = ModelCheckpoint(
                monitor=conf.monitor_var,
                dirpath='experiments/' + group + '/',
                filename=f"{group}_{i}-{epoch:02d}-{val_loss:.2f}",
                verbose=True,
                save_last=True,
                mode=conf.monitor_var_mode
            )
            callbacks_store.extend([
                checkpoint_callback,
                GenerateTextSamplesCallback(conf.samples_interval),
                LearningRateMonitor(logging_interval='step')
            ])

            # Set current fold in data module
            kfold_data_module.fold_index = i
            
            # Initialize trainer for this fold
            trainer = pl.Trainer(
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
            
            # Train the model for this fold
            print(f"Training fold {i+1}")
            train_result = trainer.fit(models[i], datamodule=kfold_data_module)
            
            # Save training results for this fold
            all_data_exp[f"fold{i}"]["train_data"] = train_result
            all_data_exp[f"fold{i}"]["carbon_data"] = {}
            
            # Clean up
            wandb.finish()


def main(conf: omegaconf.DictConfig) -> None:
    """Main entry point for the training script."""
    train(conf)


if __name__ == '__main__':
    # Uncomment to debug GPU memory issues
    # print(torch.cuda.list_gpu_processes())
    # gc.collect()
    
    # Initialize Hydra and start training
    hydra.main(version_base=None, config_path="../../conf", config_name="config")(main)()
