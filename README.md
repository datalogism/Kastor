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
├── slm/              # Training routines and model logic
├── shapes/           # SHACL templates defining extraction targets
├── data/             # Distilled datasets
├── models/           # Saved model checkpoints
├── notebooks/        # Evaluation and demo notebooks
└── README.md         # This file
```

---

## 🧠 How It Works
1.  **Knowledge Base init.** — Initialize your KB with DBpedia data 
2. **Shape Definition** — Describe your desired RDF structure in a SHACL shape file.
3. **Knowledge Distillation** — Filter and align text and RDF from a knowledge base using the SHACL shape.
4. **SLM Training** — Train a language model on these examples to learn text-to-RDF mappings.
5. **Testing & Inference** — Use the trained model to extract RDF triples from new text.

---

## 🧩 Full Pipeline

### Step 1: Knowledge Base init.

```bash
cd corese
sh load_kb.sh  # or run the corresponding loader script manually
```

### Step 1: Define SHACL Shape

* Create a new `.shacl` file in `shapes/`
* Follow examples to specify classes, properties, and constraints

### Step 3: Distill Examples

```bash
cd ../kstor
python distill.py \
  --shape_path ../shapes/your_shape.shacl \
  --output ../data/your_dataset.json
```

### Step 4: Train a Language Model

```bash
cd ../slm
python train.py \
  --data ../data/your_dataset.json \
  --output ../models/your_model
```

### Step 5: Evaluate or Use Model

```bash
jupyter notebook ../notebooks/Run_Extractor.ipynb
```

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




## First version : The active learning process

:tada: Kastor was accepted at the Research Track of [ESWC 2025](https://2025.eswc-conferences.org/)

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

This gathers all the material to reproduce the experiments or to re-use Kastor, which could be easily extended to create a new RDF-pattern-based extractor focused on a new given SHACL shape. 
The produced KB is available on [Zenodo](https://zenodo.org/records/14382674) and could be easily queried or used to produce new samples.

## Full pipeline
![kstor](img/KstorOverview.png)

0- Initialise a KB> see [corese instructions](./corese/)
DESIGN A SHAPE AND LOAD a DBpediaxWikipedia dual base 
> The two steps are explained in detail in the Kstor [code directory](./kstor/), they are:

1- Knowledge Distillation: Filter/consolidate the KB to get samples from a characterized example-specific pattern distribution  
2- Light Active SLM Learning: learn models and iterate over it to build ground-truth and gold text-to-rdf extractors


# Kastor: Structured Text-to-RDF Extraction with SHACL-Aware Language Models

**Kastor** is a modular framework for extracting RDF triples from unstructured text using shape-aware SLMs (Small Language Models). By combining SHACL shape definitions, a distilled knowledge graph, and active fine-tuning, Kastor builds lightweight, task-specific extractors. It's ideal for applications in semantic web, knowledge graph construction, and structured data mining.

---

## Test the produced models 

The produced models are available here, including the tokenizer as well as the last checkpoint obtained from the finetuning for M(DR-),  M'(DR0), M'(DR1+): https://zenodo.org/records/14498940
You can easily test the resulting extractor via [this notebook](./Test_models.ipynb)
