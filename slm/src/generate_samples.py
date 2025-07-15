from typing import Sequence

import torch
from lightning.pytorch import Callback, LightningModule, Trainer
from torch import nn
import pandas as pd
from torch.nn.utils.rnn import pad_sequence
import wandb


def cleanDecoded(list_labels):
    decoded_labels_clean = []
    for label in list_labels:
        clean = label.replace("<s>", "").replace("</s>", "")
        clean = clean.replace('=" ', '="').replace(" : ", ":").replace(" :", ":").replace(": ", ":").replace(' #',
                                                                                                             '#').replace(
            "< ", "<").replace("</ ", "</").replace("= ", "=").replace('<? ', '<?').replace('# ', '#').replace(' >',
                                                                                                               '>').replace(
            " <", "<").replace(' =', '=').replace('/ ', '/').replace('/ ', '/')
        # xml
        clean = clean.replace(' "/>', '"/>').replace(' ">', '">')
        # turtle
        # .replace(' "','"')
        clean = clean.replace(":<", ": <").replace(" ^", "^").replace("^ ", "^")
        # ntriples
        clean = clean.replace("><", "> <")
        decoded_labels_clean.append(clean)
    return decoded_labels_clean


class GenerateTextSamplesCallback(Callback):  # pragma: no cover
    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_train_batch_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule,
            outputs: Sequence,
            batch: Sequence,
            batch_idx: int,
            # dataloader_idx: int,
    ) -> None:
        wandb_table = wandb.Table(columns=["Source", "Pred", "Gold"])
        # pl_module.logger.info("Executing translation callback")

        # TEST
        if (batch_idx + 1) % self.logging_batch_interval != 0:  # type: ignore[attr-defined]
            return
        # if (trainer.batch_idx + 1) % self.logging_batch_interval != 0:  # type: ignore[attr-defined]
        #    return
        labels = batch.pop("labels")
        # print(labels)
        gen_kwargs = {
            "max_length": pl_module.hparams.val_max_target_length
            if pl_module.hparams.val_max_target_length is not None
            else pl_module.config.max_length,
            "early_stopping": False,
            "no_repeat_ngram_size": 0,
            "num_beams": pl_module.hparams.eval_beams if pl_module.hparams.eval_beams is not None else pl_module.config.num_beams,
        }
        pl_module.eval()

        decoder_inputs = torch.roll(labels, 1, 1)[:, 0:2]
        # TEST WITHOUT
        # print("labels :")
        # print(labels)

        # print(">>>decoder_inputs before")
        # print(decoder_inputs)

        decoder_inputs[:, 0] = 0

        # print(">>>decoder_inputs after")
        # print(decoder_inputs)
        generated_tokens = pl_module.model.generate(
            batch["input_ids"].to(pl_module.model.device),
            attention_mask=batch["attention_mask"].to(pl_module.model.device),
            decoder_input_ids=decoder_inputs.to(pl_module.model.device),
            **gen_kwargs,
        )
        # in case the batch is shorter than max length, the output should be padded
        if generated_tokens.shape[-1] < gen_kwargs["max_length"]:
            generated_tokens = pl_module._pad_tensors_to_max_len(generated_tokens, gen_kwargs["max_length"])
        pl_module.train()
        decoded_preds = pl_module.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True,
                                                         spaces_between_special_tokens=True)

        if pl_module.hparams.ignore_pad_token_for_loss:
            # Replace -100 in the labels as we can't decode them.
            labels = torch.where(labels != -100, labels, pl_module.tokenizer.pad_token_id)
        # print('>>generated_tokens')
        # print(generated_tokens)

        decoded_labels = pl_module.tokenizer.batch_decode(labels, skip_special_tokens=True,
                                                          spaces_between_special_tokens=True)
        decoded_inputs = pl_module.tokenizer.batch_decode(batch["input_ids"], skip_special_tokens=True,
                                                          spaces_between_special_tokens=True)

        decoded_labels = cleanDecoded(decoded_labels)
        decoded_preds = cleanDecoded(decoded_preds)

        # pl_module.logger.experiment.log_text('generated samples', '\n'.join(decoded_preds).replace('<pad>', ''))
        # pl_module.logger.experiment.log_text('original samples', '\n'.join(decoded_labels).replace('<pad>', ''))
        for source, translation, gold_output in zip(decoded_inputs, decoded_preds, decoded_labels):
            wandb_table.add_data(
                source.replace('<pad>', ''), translation.replace('<pad>', ''), gold_output.replace('<pad>', '')
            )
        pl_module.logger.experiment.log({"Triplets": wandb_table})


# class GenerateDiscoveriesCallback(Callback):  # pragma: no cover

#     """
#     PL Callback to generate triplets along training
#     """

#     def __init__(
#         self,
#         logging_batch_interval
#     ):
#         """
#         Args:
#             logging_batch_interval: How frequently to inspect/potentially plot something
#         """
#         super().__init__()
#         self.logging_batch_interval = logging_batch_interval


#     def on_test_end(
#         self,
#         trainer: Trainer,
#         pl_module: LightningModule       # dataloader_idx: int,
#     ) -> None:
#         print("CB : on_test_epoch_end")
#         print(pl_module.discoveries)

#         #trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

#         if(len(pl_module.discoveries)>0):
#             wandb_table = wandb.Table(columns=["ent_uri", "pred", "val","abstract","found?"])

#             print("****************************************")
#             print("****************************************")

#             print(pl_module.discoveries)
#             print("****************************************")
#             print("****************************************")

#             for fn_examples in pl_module.discoveries :
#                 for example in fn_examples:

#                     #trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
#                     wandb_table.add_data(
#                         example["ent_uri"], example["pred"],example["val"], example["abs"], example["found"]
#                     )
#             trainer.logger.experiment.log({"FP": wandb_table})

class GenerateWrongSubjCallback(Callback):  # pragma: no cover

    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_test_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule  # dataloader_idx: int,
    ) -> None:

        # trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

        if (len(pl_module.wrongsubj) > 0):
            wandb_table = wandb.Table(columns=["subj_gt", "subj_pred"])

            for fn_examples in pl_module.wrongsubj:
                for example in fn_examples:
                    # trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
                    wandb_table.add_data(
                        example["subj_gt"], example["subj_pred"]
                    )
            trainer.logger.experiment.log({"WrongSubject": wandb_table})


class GenerateNotValidCallback(Callback):  # pragma: no cover

    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_test_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule  # dataloader_idx: int,
    ) -> None:

        # trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

        if (len(pl_module.notvalid) > 0):
            wandb_table = wandb.Table(columns=["ent_uri", "p_pred", "g_pred"])
            for fn_examples in pl_module.notvalid:
                for example in fn_examples:
                    print(example.keys())
                    # trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
                    wandb_table.add_data(
                        example["ent_uri"], example["p_pred"], example["g_pred"]
                    )
            trainer.logger.experiment.log({"Notvalid": wandb_table})


class GenerateNotParsedCallback(Callback):  # pragma: no cover

    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_test_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule  # dataloader_idx: int,
    ) -> None:
        # trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

        if (len(pl_module.notparsed) > 0):
            wandb_table = wandb.Table(columns=["p_sent", "g_sent", "dist"])
            for fn_examples in pl_module.notparsed:
                for example in fn_examples:
                    # trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
                    wandb_table.add_data(
                        example["p_sent"], example["g_sent"], example["dist"]
                    )
            trainer.logger.experiment.log({"NotParsed": wandb_table})


class GenerateFPCallback(Callback):  # pragma: no cover

    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_test_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule  # dataloader_idx: int,
    ) -> None:
        print("CB : on_test_epoch_end")
        print(pl_module.fp_examples)

        # trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

        if (len(pl_module.fp_examples) > 0):

            wandb_table = wandb.Table(columns=["type", "ent_uri", "pred", "val_pred", "val_gold", "abstract", "found?"])

            for fp_examples in pl_module.fp_examples:
                for example in fp_examples:
                    # trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
                    wandb_table.add_data(
                        example["type"], example["ent_uri"], example["pred"], example["val_pred"], example["val_gold"],
                        example["abs"], example["found"]
                    )
            trainer.logger.experiment.log({"FP": wandb_table})


class GenerateToInspectCallback(Callback):  # pragma: no cover

    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_test_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule  # dataloader_idx: int,
    ) -> None:
        print("CB : on_test_epoch_end")
        print(pl_module.to_inspect)

        # trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

        if (len(pl_module.to_inspect) > 0):

            wandb_table = wandb.Table(columns=["type", "ent_uri", "pred", "val_pred", "val_gold", "abs", "found"])

            for fn_example in pl_module.to_inspect:
                for example in fn_example:
                    # trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
                    wandb_table.add_data(
                        example["type"], example["ent_uri"], example["pred"], example["val_pred"], example["val_gold"],
                        example["abs"], str(example["found"])

                    )
            trainer.logger.experiment.log({"To Inspect table": wandb_table})


class GenerateRDFpatternsCallback(Callback):  # pragma: no cover

    """
    PL Callback to generate triplets along training
    """

    def __init__(
            self,
            logging_batch_interval
    ):
        """
        Args:
            logging_batch_interval: How frequently to inspect/potentially plot something
        """
        super().__init__()
        self.logging_batch_interval = logging_batch_interval

    def on_test_end(
            self,
            trainer: Trainer,
            pl_module: LightningModule  # dataloader_idx: int,
    ) -> None:
        print("CB : on_test_epoch_end")
        print(pl_module.rdf_patterns)

        # trainer.logger.log_text('discoveries>'+ str(pl_module.discoveries) )

        if (len(pl_module.rdf_patterns) > 0):

            wandb_table = wandb.Table(columns=["fold", "rdf_motif", "nb"])

            for fn_example in pl_module.rdf_patterns:
                for example in fn_example:
                    # trainer.logger.log_text('discoveries>'+ example["pred"]+":"+example["val"] )
                    wandb_table.add_data(
                        example[0], example[1], example[2]
                    )
            trainer.logger.experiment.log({"generated_triples": wandb_table})
