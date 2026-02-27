# Kastor - Shape-based relation extraction framework
  ![kstor](img/intro_kastor.png)

**Kastor** is a modular framework for extracting RDF triples from unstructured text using shape-aware SLMs (Small Language Models). By combining SHACL shape definitions, a distilled knowledge graph, and active fine-tuning, Kastor builds lightweight, task-specific extractors. It's ideal for applications in semantic web, knowledge graph construction, and structured data mining.


## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/datalogism/Kastor.git
cd Kastor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📁 Project Overview

```
Kastor/
├── corese/           # Corese RDF engine and knowledge base loader
├── kstor/            # Knowledge distillation and SHACL-based filtering
├── slm/              # Finetuning material
├── shapes/           # SHACL templates used for extraction
├── XP_results/       # Experimental outputs
├── doc/              # Documentation
├── img/              # Illustrations
└── README.md         # This file
```

---

## 🤗 Using Pre-trained Kastor Models

Pre-trained Kastor models for 16 entity types are available on HuggingFace under the `Datartisan` organization (e.g. `Datartisan/KastorArtist`). They can be used out-of-the-box to extract RDF triples from plain text without any training.

👉 See **[`doc/UseKastorsModelsInTheWild.md`](./doc/UseKastorsModelsInTheWild.md)** for the full usage guide (pipeline scripts, programmatic API, input/output format, evaluation).

### Sample evaluation result

A preliminary evaluation on the Artist class (1 entity, Wikipedia markdown abstract, DBpedia ground-truth) gives the following results:

| Metric | Value |
|---|---|
| Extract vs. correct — property precision | **100%** |
| Extract vs. correct — property recall | 50% |
| Extract vs. correct — property F1 | 66.67% |
| Grounding rate | **100%** |
| Shape coverage | 5.56% |

All extracted triples were correct and grounded in the source text. The low coverage reflects that only 1 property was extracted from a very short abstract (283 chars) out of 18 properties defined in the shape. See [`test_all_results.json`](./hugging_face_models/test_all_results.json) for the full output.

---

## 🧠 How It Works
1.  **Knowledge Base init.** — [Initialize your KB with DBpedia data](./doc/KB_init.md)
2. **Shape Definition** — [Describe your desired RDF structure in a SHACL shape file.](./doc/ShapeDefinition.md)
3. **Knowledge Distillation** — [Filter and align text and RDF from a knowledge base using the SHACL shape.](./doc/KnowledgeDistill.md)
4. **Data Augmentation** — [Augment your knowledge base to ensure sufficient exposure of rare properties](./doc/AugStrategies.md)
5. **SLM Training** — [Train a language model distilled and enrich models to learn text-to-RDF extractor](./doc/SLMFinetuning)
4. **Light Active Learning** — [Use your models to create gold dataset](./doc/LightActiveLearning.md)
5. **Testing & Inference** — [Use the trained model to extract RDF triples from new text](Test_models.ipynb)

---
## 🛠 Requirements

* Python >= 3.8
* PyTorch
* HuggingFace Transformers
* RDFlib
* Java 11+ (for Corese)

Install via `pip install -r requirements.txt`

---

## ✅ Best Practices

* Use concise, complete SHACL definitions to improve distillation quality.
* Visualize RDF outputs to validate structure.
* Use active training for iterative improvement.
* Pre-filter knowledge base to reduce noise.

---

## 📜 License

Kastor is released under the MIT License.

---

## 📬 Questions or Issues?

Open a GitHub issue or contact the maintainers via [https://github.com/datalogism/Kastor](https://github.com/datalogism/Kastor)


---

## 📝 Related publications

### 1- Kastor: Fine-Tuned Small Language Models for Shape-Based Active Relation Extraction [PUBLISHED]
:tada: Accepted at the Research Track of [ESWC 2025](https://2025.eswc-conferences.org/)

If you use the code or cite our work, please reference this one as follows :
```
@inproceedings{DBLP:conf/esws/RingwaldGFMA25,
  author       = {C{\'{e}}lian Ringwald and
                  Fabien Gandon and
                  Catherine Faron and
                  Franck Michel and
                  Hanna Abi Akl},
  editor       = {Edward Curry and
                  Maribel Acosta and
                  Mar{\'{\i}}a Poveda{-}Villal{\'{o}}n and
                  Marieke van Erp and
                  Adegboyega K. Ojo and
                  Katja Hose and
                  Cogan Shimizu and
                  Pasquale Lisena},
  title        = {Kastor: Fine-Tuned Small Language Models for Shape-Based Active Relation
                  Extraction},
  booktitle    = {The Semantic Web - 22nd European Semantic Web Conference, {ESWC} 2025,
                  Portoroz, Slovenia, June 1-5, 2025, Proceedings, Part {I}},
  series       = {Lecture Notes in Computer Science},
  volume       = {15718},
  pages        = {94--115},
  publisher    = {Springer},
  year         = {2025},
  url          = {https://doi.org/10.1007/978-3-031-94575-5\_6},
  doi          = {10.1007/978-3-031-94575-5\_6},
  timestamp    = {Tue, 10 Jun 2025 17:38:39 +0200},
  biburl       = {https://dblp.org/rec/conf/esws/RingwaldGFMA25.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```
### Associated material: 

* [Produced Knowledge Base](https://zenodo.org/records/14382674) 
* [Models](https://zenodo.org/records/14498940) 
* [WanDB Project](https://wandb.ai/inria_test/KSTOR_xp) 

The resulting extractor could be tested using [this notebook](./Test_models.ipynb)


### 2- Overcoming the Generalization Limits of SLM Finetuning for Shape-Based Extraction of Datatype and Object Properties [UNDER-REVIEW]

* [Datasets produced](https://zenodo.org/records/15917325) 
* [WanDB Project - Part 1](https://wandb.ai/celian-ringwald/GenLimits_Part1) 
* [WanDB Project - Part 2 - trained models](https://wandb.ai/celian-ringwald/GenLimitsPart2_train) 
* [WanDB Project - Part 2 - cross-evaluation](https://wandb.ai/celian-ringwald/GenLimitsPart2_crossEval) 
* [WanDB Project - Part 3 - trained models](https://wandb.ai/celian-ringwald/GenLimitsPart3_train) 
* [WanDB Project - Part 3 - cross-evaluation](https://wandb.ai/celian-ringwald/GenLimitsPart3_crossEval) 

