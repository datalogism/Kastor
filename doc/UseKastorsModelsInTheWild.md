# Kastor HuggingFace Models

This directory contains scripts for running and evaluating the Kastor fine-tuned BART models, which extract RDF triples from Wikipedia-style text and output them in Turtle Light format.

Models are hosted on HuggingFace at `Datartisan/Kastor<EntityType>`.

Each model is tied to a **SHACL shape** (located in `shapes/txt2kg/`) that defines the target entity class and the set of extractable properties (datatype and object properties). The pipeline uses these shapes for RDF conversion, SHACL validation, and metric computation. The `_clean` variants (e.g. `ArtistShapeTXT2KG_clean.ttl`) are the ones actually used at inference time. If you want to extend Kastor to a new entity type, you will need to write a corresponding shape — see [`doc/HowToCreateAShape.md`](HowToCreateAShape.md) for a step-by-step guide covering shape structure, property definitions, supported datatypes, and best practices.

---

## Supported Entity Types

| Entity Type           | HuggingFace Repo                        |
|-----------------------|-----------------------------------------|
| Airport               | Datartisan/KastorAirport                |
| Artist                | Datartisan/KastorArtist                 |
| Athlete               | Datartisan/KastorAthlete                |
| Building              | Datartisan/KastorBuilding               |
| CelestialBody         | Datartisan/KastorCelestialBody          |
| City                  | Datartisan/KastorCity                   |
| Company               | Datartisan/KastorCompany                |
| Film                  | Datartisan/KastorFilm                   |
| Food                  | Datartisan/KastorFood                   |
| MeanOfTransportation  | Datartisan/KastorMeanOfTransportation   |
| MusicalWork           | Datartisan/KastorMusicalWork            |
| Politician            | Datartisan/KastorPolitician             |
| Scientist             | Datartisan/KastorScientist              |
| SportsTeam            | Datartisan/KastorSportsTeam             |
| University            | Datartisan/KastorUniversity             |
| WrittenWork           | Datartisan/KastorWrittenWork            |

---

## Scripts Overview

### `kastor_pipeline.py` — Full extraction pipeline (recommended)

The main entry point. Loads a model, extracts triples, parses them, converts to RDF, validates against SHACL, and reports statistics.

**Usage:**
```bash
# Use default example for a model type
python kastor_pipeline.py --model_type Artist

# Provide your own text
python kastor_pipeline.py --model_type Scientist \
    --id_ent "Marie_Curie" \
    --text "Marie Curie was a Polish physicist and chemist who conducted pioneering research on radioactivity."

# Suppress verbose output
python kastor_pipeline.py --model_type City --quiet
```

**Arguments:**
| Argument       | Default    | Description                                      |
|----------------|------------|--------------------------------------------------|
| `--model_type` | `Artist`   | Entity type (see supported types above)          |
| `--id_ent`     | (built-in) | DBpedia entity ID, e.g. `Albert_Einstein`        |
| `--text`       | (built-in) | Plain text abstract to extract triples from      |
| `--quiet`      | off        | Suppress step-by-step output                     |

**Pipeline steps:**
1. Load SHACL shape (`shapes/txt2kg/<Type>ShapeTXT2KG_clean.ttl`)
2. Download and load model from HuggingFace
3. Extract raw Turtle Light output from the text
4. Parse the output into triples
5. Convert to an RDF graph
6. Validate against the SHACL shape
7. Compute coverage/precision statistics
8. Verify that extracted values are grounded in the source text

**Programmatic usage:**
```python
from kastor_pipeline import KastorPipeline

pipeline = KastorPipeline(model_type="Scientist")
result = pipeline.run(
    id_ent="Albert_Einstein",
    text="Albert Einstein was a German-born theoretical physicist..."
)

print(result.triples)               # List of [subject, property, value]
print(result.rdf_turtle)            # Serialized RDF in Turtle format
print(result.shacl_valid)           # True/False
print(result.statistics.coverage)   # % of shape properties covered
```

---

### `load_kastor_models.py` — Low-level model loading

Handles downloading checkpoints from HuggingFace and loading them as `BartForConditionalGeneration` models. Also defines the `KASTOR_MODELS` registry with sample abstracts for each entity type.

**Programmatic usage:**
```python
from load_kastor_models import load_model_and_tokenizer, extract_triples

model, tokenizer = load_model_and_tokenizer("Datartisan/KastorArtist")

predictions = extract_triples(
    "Pablo_Picasso : Pablo Ruiz Picasso was a Spanish painter...",
    model,
    tokenizer
)
print(predictions[0])  # Raw Turtle Light string
```

**Run all models on built-in examples and save to JSON:**
```bash
python load_kastor_models.py
# Output: kastor_results.json
```

---

### `run_all_models.py` — Full pipeline on all entity types

Runs the complete `kastor_pipeline` (parse + RDF + SHACL + stats) on all 16 entity types using their built-in sample abstracts. Outputs a detailed JSON report and a summary table.

**Usage:**
```bash
python run_all_models.py
python run_all_models.py --output my_results.json
```

**Arguments:**
| Argument    | Default            | Description                     |
|-------------|--------------------|---------------------------------|
| `--output`  | `all_results.json` | Output path for the JSON report |

**Output:** A JSON file with per-model results (triples, RDF, SHACL validity, coverage, precision, grounding rate) and aggregate statistics across all models.

---

### `test_all_models.py` — Evaluation against a SPARQL endpoint

Evaluates Kastor models against real DBpedia data retrieved from a local SPARQL endpoint. For each entity, it:
1. Queries ground-truth triples from the endpoint (`graph_init`)
2. Fetches the Wikipedia markdown abstract via the Wikipedia HTML API
3. Filters ground-truth to values expressible in the abstract (`graph_correct`)
4. Runs the Kastor model on the cleaned abstract (`graph_extract`)
5. Compares the three graphs and computes recall/precision/F1

**Requires a running SPARQL endpoint** (e.g. a local Corese or Fuseki instance loaded with DBpedia data).

**Usage:**
```bash
# Run on all classes, 100 entities each
python test_all_models.py --endpoint http://localhost:8080/sparql

# Run on specific classes, 5 entities each
python test_all_models.py \
    --endpoint http://localhost:8080/sparql \
    --limit 5 \
    --classes Artist Scientist

# Custom output file and Wikipedia user agent
python test_all_models.py \
    --endpoint http://localhost:8080/sparql \
    --limit 50 \
    --output eval_results.json \
    --wiki-agent "MyProject/1.0 (contact@example.com)"
```

**Arguments:**
| Argument       | Default                        | Description                              |
|----------------|--------------------------------|------------------------------------------|
| `--endpoint`   | `http://localhost:8080/sparql` | SPARQL endpoint URL                      |
| `--limit`      | `100`                          | Entities to evaluate per class           |
| `--output`     | `test_all_results.json`        | Output JSON file path                    |
| `--wiki-agent` | (project default)              | Wikipedia API user-agent string          |
| `--classes`    | all 16                         | Restrict to specific entity types        |

**Output metrics per entity:**
- `graph_correct_expressiveness`: % of ground-truth triples expressed in the abstract
- `extract_vs_init`: recall/precision/F1 at property and value level vs. full ground-truth
- `extract_vs_correct`: recall/precision/F1 vs. abstract-grounded ground-truth
- `coverage`, `precision`, `grounding_rate`: standard Kastor pipeline metrics

---

## Dependencies

Install required packages:
```bash
pip install torch transformers huggingface_hub rdflib pyshacl unidecode
# For test_all_models.py:
pip install SPARQLWrapper requests bs4 markdownify ratelimit backoff
# Optional (for date matching):
pip install datefinder
```

---

## Input Format

All models expect input as:
```
<entity_id> : <plain text abstract>
```
Example:
```
Albert_Einstein : Albert Einstein was a German-born theoretical physicist who developed the theory of relativity...
```

The `entity_id` should match the DBpedia resource name (underscores instead of spaces).

## Output Format

Models output **Turtle Light** (factorized, 1-line format):
```
:Albert_Einstein a:Scientist;:birthDate "1879-03-14";:birthPlace :Ulm;:nationality :Germany.
```

The `kastor_pipeline.py` script parses this into structured triples and converts them to standard RDF Turtle.
