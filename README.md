# Kastor - Fine-tuned Small Language Models for Shape-based Active Relation Extraction
  ![kstor](img/intro_kastor.png)

This anonymous repository is related to the submission at the ESWC2025 research track "Kastor: Fine-tuned Small Language Models for Shape-based Active Relation Extraction" 
It gathers all the material to reproduce the experiments, which could be easily extended to create a new RDF-pattern-based extractor focused on a new given SHACL shape. 
The produced KB is available on [Zenodo](https://zenodo.org/records/14382674) and could be easily queried or used to produce new samples.

## Full pipeline
  ![kstor](img/full_pipeline.png)

0- **Initialise a KB** > see [corese instructions](./kstor/corese/)
DESIGN A SHAPE AND LOAD a DBpediaxWikipedia dual base 
1- Knowledge Distillation  > see [corese instructions](./kstor/corese/)
Filter/consolidate the KB to get  
Light Active SLM Learning
