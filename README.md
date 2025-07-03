# Kastor - Fine-tuned Small Language Models for Shape-based Active Relation Extraction
  ![kstor](img/intro_kastor.png)


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


## Test the produced models 

The produced models are available here, including the tokenizer as well as the last checkpoint obtained from the finetuning for M(DR-),  M'(DR0), M'(DR1+): https://zenodo.org/records/14498940
You can easily test the resulting extractor via [this notebook](./Test_models.ipynb)
