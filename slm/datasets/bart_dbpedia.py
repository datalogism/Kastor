# coding=utf-8
# Copyright 2020 The TensorFlow Datasets Authors and the HuggingFace Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""REBEL"""

from __future__ import absolute_import, division, print_function

import pandas as pd

import datasets

import re 
import json
import logging
import math
from collections import defaultdict

_DESCRIPTION = """
DBpedia first test 
"""

_URL = ""
_URLS = {
    "train": _URL + "_train.jsonl",
    "dev": _URL + "_val.jsonl",
    "test": _URL + "_test.jsonl",
}


class DBPediaTestConfig(datasets.BuilderConfig):
    """BuilderConfig for DBpediatest."""

    def __init__(self, **kwargs):
        """BuilderConfig for REBEL.
        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(DBPediaTestConfig, self).__init__(**kwargs)


class DBpediaTest(datasets.GeneratorBasedBuilder):
    """Rebel 1.0"""

    BUILDER_CONFIGS = [
        DBPediaTestConfig(
            name="plain_text",
            version=datasets.Version("1.0.0", ""),
            description="Plain text",
        ),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "label": datasets.Value("string"),
                    "context": datasets.Value("string"),
                    "triplets": datasets.Value("string"),
                }
            ),
            # No default supervised_keys (as we have to pass both question
            # and context as input).
            supervised_keys=None,
            # homepage="",
#             citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        if self.config.data_files:
            print("SplitGenerator")
            print("train :")
            print(self.config.data_files)
            downloaded_files = {
                "train": self.config.data_files["train"][0], # self.config.data_dir + "en_train.jsonl",
                "dev": self.config.data_files["dev"][0], #self.config.data_dir + "en_val.jsonl",
                "test": self.config.data_files["test"][0], #self.config.data_dir + "en_test.jsonl",
            }
        else:
            print("DOWNLOAD AND EXTRACT")
            downloaded_files = dl_manager.download_and_extract(_URLS)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": downloaded_files["train"]}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": downloaded_files["dev"]}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"filepath": downloaded_files["test"]}),
        ]

    def _generate_examples(self, filepath):
        """This function returns the examples in the raw (text) form."""
        logging.info("generating examples from = %s", filepath)
        
        with open(filepath) as json_file:
            f = json.load(json_file)
            print("============================")
            

            for id_, row in enumerate(f):
                triples=str(row["triples"])
                if(triples[0:3]!="<s>"):
                    triples="<s>"+triples+"</s>"
                else:
                    triples=row["triples"]
                
                if("ent" in row.keys()):
                    entity=row["ent"]
                elif("entity" in row.keys()):
                    entity=row["entity"]

                if(row["abstract"][0:3]=="<s>"):
                    asbtract=row["abstract"][3:len(row["abstract"])]
                else:
                    asbtract=row["abstract"]  

                asbtract=entity+" : "+row["abstract"]
                yield str(id_), {
                    "label": entity,
                    "context": asbtract,
                    "id": str(id_),
                    "triplets": triples
                }