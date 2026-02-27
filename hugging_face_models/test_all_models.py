"""
Evaluate Kastor models against real data from a SPARQL endpoint,
using Wikipedia markdown abstracts as text source.

For each class:
1. Query entity URIs + graph_init properties from the SPARQL endpoint
2. Fetch Wikipedia markdown abstracts via the Wikipedia HTML API
3. Check which graph_init values are expressed in the markdown (graph_correct)
   using the same method as 1_KD-322_Wikicheck_md_dt_and_op.py
4. Run Kastor model extraction on a cleaned version of the abstract (graph_extract)
5. Compare graph_init / graph_correct / graph_extract

Usage:
    python test_all_models.py --endpoint http://localhost:8080/sparql --limit 5 --classes Artist
    python test_all_models.py --endpoint http://localhost:8080/sparql --limit 100
"""

import argparse
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import bs4
import requests
from markdownify import markdownify
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
from unidecode import unidecode
from SPARQLWrapper import JSON, SPARQLWrapper

try:
    import datefinder
    HAS_DATEFINDER = True
except ImportError:
    HAS_DATEFINDER = False

from kastor_pipeline import (
    ShapeHandler, ENTITY_TYPES,
    parse_turtle_light, triples_to_rdf, validate_shacl,
    compute_statistics, verify_grounding
)
from load_kastor_models import load_model_and_tokenizer, extract_triples, KASTOR_MODELS

# Default Wikipedia user agent - override via --wiki-agent
DEFAULT_WIKI_AGENT = "KastorTestScript/1.0 (https://datalogism.github.io/; celian.ringwald@inria.fr)"



# =============================================================================
# Wikipedia Markdown Retrieval
# (adapted from abstractExtended.py getAbstractMD2, without revision_id)
# =============================================================================

def clean_url_for_md(entity: str) -> str:
    """URL-encode an entity name for markdown links (from rdf_synthax_fct.cleanURL)."""
    if "%" not in entity:
        txt = urllib.parse.quote(
            entity.replace("http://dbpedia.org/resource/", "")
                   .replace("https://dbpedia.org/resource/", "")
        ).replace(".", "%2E").replace("'", "%27")
    else:
        txt = entity.replace("http://dbpedia.org/resource/", "") \
                     .replace("https://dbpedia.org/resource/", "")
    return txt


@on_exception(expo, RateLimitException, max_tries=1)
@limits(calls=150, period=1)
def get_abstract_md(entity: str, usr_agent: str) -> str:
    """Fetch Wikipedia markdown abstract for an entity (no revision_id).

    Adapted from getAbstractMD2 in abstractExtended.py.
    Uses the current/latest revision since we don't have a revision_id.
    """
    url_wikiapi = "https://en.wikipedia.org/api/rest_v1/page/html/"
    headers = {
        "User-Agent": usr_agent,
        "Accept": "text/html"
    }

    params = {
        "redirect": "true"
    }

    res = requests.get(
        url_wikiapi + entity,
        headers=headers,
        params=params,
        timeout=10
    )
    res_all = ""

    if res.status_code == 200:
        content = res.text
        bs_html = bs4.BeautifulSoup(content, 'html.parser')
        disamb = bs_html.find("div", {"id": "_disambigbox"})
        if disamb is None:
            sections = bs_html.select("section")
            if not sections:
                return ""
            abstract = sections[0]
            links = abstract.findAll("a")
            for link in links:
                if link.has_attr("title"):
                    del link["title"]
            paragraphs = abstract.select("p")
            res_all = ""
            for para in paragraphs:
                class_to_delete = ["ext-phonos", "IPA", "IPA-label",
                                   "Inline-Template", "reference"]
                para_str = str(para)
                for class_ in class_to_delete:
                    found_ipa_content = para.findAll(["span", "sup"], {"class": class_})
                    if found_ipa_content:
                        for ipa_content in found_ipa_content:
                            para_str = para_str.replace(str(ipa_content), "")
                para_str = para_str.replace("(  ;", "(")

                md_p = markdownify(str(para_str))
                replaced = md_p.replace("](./", "](:")  # TO ttl light
                res_all += replaced

            markdown_link_rgx = r'\[(.*?)\]\(.*?\)?\)'
            markdown_links = [x.group() for x in re.finditer(markdown_link_rgx, res_all)]
            delete_list = []
            for links_found in markdown_links:
                label = re.findall(r'\[(.*?)\]', links_found)
                link = re.findall(r'\(\:(.*?\)?)?\)', links_found)
                if "redlink=1" in links_found:
                    delete_list.append([links_found, label[0]])
                elif len(link) > 0:
                    encoded = clean_url_for_md(link[0])
                    res_all = res_all.replace("(:" + link[0] + ")", "(:" + encoded + ")")

            for delete in delete_list:
                res_all = res_all.replace(delete[0], delete[1])
            res_all = res_all.replace("\n", "")

    if res.status_code == 404:
        res_all = ""
    return res_all


def clean_md_to_abstract(md_text: str) -> str:
    """Clean markdown text into a plain abstract suitable for model extraction.

    Strips markdown links, bold/italic markers, and cleans up whitespace
    so the text looks like a standard DBpedia abstract.
    """
    text = md_text

    # Replace markdown links [label](:target) or [label](url) with just label
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)

    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)

    # Remove any remaining markdown image syntax ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)

    # Clean up HTML entities that may remain
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")

    # Remove leftover parentheses from cleaned IPA/phonetic content: ( ) or (  )
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\(\s*;\s*\)', '', text)

    # Collapse multiple spaces and strip
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()

    return text


# =============================================================================
# Markdown-aware value matching
# (from triple_shapes.py find_in_abstractWithObj, as used in 1_KD-322)
# =============================================================================

def find_in_abstract_md(abstract: str, prop_uri: str, value: str, type_str: str) -> bool:
    """Check if a property value is expressed in a markdown abstract.

    Uses the same logic as triple_shapes.find_in_abstractWithObj:
    - Year/gYear: simple string containment
    - date: datefinder matching
    - string: case-insensitive containment + unidecode fallback
    - dbo: (object property): regex match on markdown links [label](:Entity_Name)

    Args:
        abstract: The markdown abstract text.
        prop_uri: Full property URI (used for label special case).
        value: The property value to look for.
        type_str: Type string, e.g. "xsd:gYear", "xsd:date", "xsd:string", "dbo:Place".
    """
    if not abstract or not value:
        return False

    value = str(value).strip()

    # Year
    if "Year" in type_str:
        return value in abstract

    # Date
    if "date" in type_str:
        if HAS_DATEFINDER:
            try:
                matches = datefinder.find_dates(abstract)
                dates = []
                for match in matches:
                    if match != '':
                        dates.append(match.strftime('%Y-%m-%d'))
                if len(dates) > 0:
                    return value in dates
                return False
            except Exception:
                return value in abstract
        return value in abstract

    # String
    if "string" in type_str:
        if "label" in prop_uri:
            parts = value.split(" ")
            ok = True
            for part in parts:
                if part.lower() not in abstract.lower():
                    ok = False
            if ok:
                return True
        elif value.lower() in abstract.lower():
            return True
        else:
            if unidecode(value.lower()) in unidecode(abstract.lower()):
                return True
        return False

    # Object property: look for markdown link [label](:Entity_Name)
    if "dbo:" in type_str:
        print("dbo****",value)
        val2 = value.replace("_", r"\_")
        val2 = val2.replace("http://dbpedia.org/resource/", "") \
                    .replace("https://dbpedia.org/resource/", "")
        if(":" in val2):
            val2=val2.replace(":","")
        if ("." in val2):#### TOCHECK
            val2 = val2.replace(".", r"\.")

        print(unidecode(val2))
        print(unidecode(abstract))
        prefix = r"\:"

        rgx = r'\[.*\]\(' + prefix + val2 + r'\)'

        res = re.search(rgx, unidecode(abstract))
        if res:
            return True

    return False


# =============================================================================
# SPARQL Query Functions
# =============================================================================

def sparql_select(endpoint: str, query: str) -> List[Dict]:
    """Execute a SPARQL SELECT query and return results as list of dicts."""
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()
    processed = json.load(result.response)
    cols = processed['head']['vars']
    rows = []
    for row in processed['results']['bindings']:
        item = {}
        for c in cols:
            if c in row:
                item[c] = row[c]['value']
        rows.append(item)
    return rows


def query_entities_of_class(
    endpoint: str,
    class_uri: str,
    limit: int
) -> List[Dict]:
    """Get N entity URIs of a class from the SPARQL endpoint.

    Returns list of dicts with key: entity
    """
    query = f"""
    SELECT DISTINCT ?entity WHERE {{
        ?entity a <{class_uri}> .
    }}
    ORDER BY RAND()
    LIMIT {limit}
    """
    return sparql_select(endpoint, query)


def query_entity_properties_batch(
    endpoint: str,
    entity_uris: List[str],
    property_uris: List[str]
) -> Dict[str, List[Dict]]:
    """Batch query using VALUES clause to get all shape properties for all entities.

    Returns dict mapping entity URI -> list of {property, value} dicts.
    """
    if not entity_uris or not property_uris:
        return {}

    values_entities = " ".join(f"<{uri}>" for uri in entity_uris)
    values_props = " ".join(f"<{uri}>" for uri in property_uris)

    query = f"""
    SELECT ?entity ?property ?value WHERE {{
        VALUES ?entity {{ {values_entities} }}
        VALUES ?property {{ {values_props} }}
        ?entity ?property ?value .
    }}
    """
    rows = sparql_select(endpoint, query)

    result = {uri: [] for uri in entity_uris}
    for row in rows:
        entity = row.get("entity", "")
        if entity in result:
            result[entity].append({
                "property": row.get("property", ""),
                "value": row.get("value", "")
            })
    return result


# =============================================================================
# Shape Utilities
# =============================================================================

def get_target_class_uri(shape: ShapeHandler) -> str:
    """Extract sh:targetClass URI from the SHACL shape graph."""
    query = """
    SELECT ?class WHERE {
        ?shape sh:targetClass ?class .
    }"""
    for row in shape.graph.query(query):
        return str(row[0])
    return f"http://dbpedia.org/ontology/{shape.model_type}"


def get_property_uris(shape: ShapeHandler) -> List[str]:
    """Get all property URIs defined in the shape."""
    return [str(info["ns"]) for info in shape.relations_map.values()]


def get_property_type_map(shape: ShapeHandler) -> Dict[str, str]:
    """Get property URI -> type string map from the shape.

    Same as triple_shapes.getShapePropWithType:
    returns {full_prop_uri: type_string} where type_string is like
    "xsd:gYear", "xsd:date", "xsd:string", "dbo:Place", etc.
    """
    query = """
    SELECT DISTINCT ?target_prop ?datatype
    WHERE {
        ?a sh:path ?target_prop;
           sh:datatype|sh:class ?datatype.
    }"""
    qres = shape.graph.query(query)
    return {
        str(row[0]): str(row[1])
            .replace("http://www.w3.org/2001/XMLSchema#", "xsd:")
            .replace("http://dbpedia.org/ontology/", "dbo:")
        for row in qres
    }


# =============================================================================
# Graph Building
# =============================================================================

def build_graph_init_triples(
    entity_uri: str,
    entity_props: List[Dict],
    shape: ShapeHandler
) -> List[List[str]]:
    """Build graph_init (ground truth) triples from endpoint data.

    Returns triples as [subject, property_name, value] matching Kastor format.
    """
    entity_name = entity_uri.split("/")[-1]
    triples = []

    # Reverse map: full URI -> short property name
    uri_to_name = {}
    for name, info in shape.relations_map.items():
        uri_to_name[str(info["ns"])] = name

    for prop_data in entity_props:
        prop_uri = prop_data["property"]
        value = prop_data["value"]
        prop_name = uri_to_name.get(prop_uri)
        if prop_name is None:
            continue

        # Format value like Kastor output
        if value.startswith("http://dbpedia.org/resource/"):
            value = ":" + value.replace("http://dbpedia.org/resource/", "")
        triples.append([entity_name, prop_name, value])

    return triples


def clean_value_for_md_check(value: str) -> str:
    """Clean a value for markdown-based checking (from rdf_synthax_fct.cleanTxt)."""
    value = str(value).strip()
    if value and value[0] == " ":
        value = value[1:]
    if value and value[-1] == " ":
        value = value[:-1]
    return value.strip()


def build_graph_correct_triples(
    graph_init_triples: List[List[str]],
    abstract_md: str,
    shape: ShapeHandler,
    type_prop_map: Dict[str, str]
) -> List[List[str]]:
    """Build graph_correct: subset of graph_init whose values are grounded
    in the markdown abstract.

    Uses find_in_abstract_md (same method as 1_KD-322_Wikicheck_md_dt_and_op.py).
    """
    # Reverse map: short name -> full URI
    name_to_uri = {}
    for name, info in shape.relations_map.items():
        name_to_uri[name] = str(info["ns"])

    graph_correct = []
    for triple in graph_init_triples:
        prop_name = triple[1]
        value = triple[2]
        prop_uri = name_to_uri.get(prop_name, "")
        type_str = type_prop_map.get(prop_uri, "")

        # Handle Year dates: extract year from full date
        if "Year" in prop_name and "-" in str(value):
            value = str(value).split("-")[0][0:4]

        val_clean = clean_value_for_md_check(value)
        if not val_clean or val_clean in ("nan", "NaN", ""):
            continue

        found = find_in_abstract_md(abstract_md, prop_uri, val_clean, type_str)
        if found:
            graph_correct.append(triple)

    return graph_correct


# =============================================================================
# Graph Comparison
# =============================================================================

def normalize_value(value: str) -> str:
    """Normalize a value for comparison."""
    v = str(value).strip()
    if v.startswith("http://dbpedia.org/resource/"):
        v = v.replace("http://dbpedia.org/resource/", "")
    v = v.lstrip(":")
    v = v.replace("_", " ").lower().strip()
    return v


def compare_graphs(
    graph_init: List[List[str]],
    graph_correct: List[List[str]],
    graph_extract: List[List[str]],
    shape: ShapeHandler
) -> Dict:
    """Compare graph_init, graph_correct, graph_extract and compute metrics."""
    extract_filtered = [t for t in graph_extract if t[1] not in ("type", "a")]

    # Property sets
    init_props = set(t[1] for t in graph_init)
    correct_props = set(t[1] for t in graph_correct)
    extract_props = set(t[1] for t in extract_filtered)

    # graph_correct expressiveness
    correct_expressiveness = len(correct_props) / len(init_props) * 100 if init_props else 0.0

    # graph_extract vs graph_init property-level
    ext_init_prop_tp = extract_props & init_props
    ext_init_prop_recall = len(ext_init_prop_tp) / len(init_props) * 100 if init_props else 0.0
    ext_init_prop_precision = len(ext_init_prop_tp) / len(extract_props) * 100 if extract_props else 0.0
    ext_init_prop_f1 = (2 * ext_init_prop_recall * ext_init_prop_precision /
                        (ext_init_prop_recall + ext_init_prop_precision)
                        if (ext_init_prop_recall + ext_init_prop_precision) > 0 else 0.0)

    # graph_extract vs graph_correct property-level
    ext_corr_prop_tp = extract_props & correct_props
    ext_corr_prop_recall = len(ext_corr_prop_tp) / len(correct_props) * 100 if correct_props else 0.0
    ext_corr_prop_precision = len(ext_corr_prop_tp) / len(extract_props) * 100 if extract_props else 0.0
    ext_corr_prop_f1 = (2 * ext_corr_prop_recall * ext_corr_prop_precision /
                        (ext_corr_prop_recall + ext_corr_prop_precision)
                        if (ext_corr_prop_recall + ext_corr_prop_precision) > 0 else 0.0)

    # Value-level comparison
    def triple_set(triples):
        return set((t[1], normalize_value(t[2])) for t in triples)

    init_values = triple_set(graph_init)
    correct_values = triple_set(graph_correct)
    extract_values = triple_set(extract_filtered)

    # graph_extract vs graph_init value-level
    ext_init_val_tp = extract_values & init_values
    ext_init_val_recall = len(ext_init_val_tp) / len(init_values) * 100 if init_values else 0.0
    ext_init_val_precision = len(ext_init_val_tp) / len(extract_values) * 100 if extract_values else 0.0
    ext_init_val_f1 = (2 * ext_init_val_recall * ext_init_val_precision /
                       (ext_init_val_recall + ext_init_val_precision)
                       if (ext_init_val_recall + ext_init_val_precision) > 0 else 0.0)

    # graph_extract vs graph_correct value-level
    ext_corr_val_tp = extract_values & correct_values
    ext_corr_val_recall = len(ext_corr_val_tp) / len(correct_values) * 100 if correct_values else 0.0
    ext_corr_val_precision = len(ext_corr_val_tp) / len(extract_values) * 100 if extract_values else 0.0
    ext_corr_val_f1 = (2 * ext_corr_val_recall * ext_corr_val_precision /
                       (ext_corr_val_recall + ext_corr_val_precision)
                       if (ext_corr_val_recall + ext_corr_val_precision) > 0 else 0.0)

    return {
        "graph_init_property_count": len(init_props),
        "graph_correct_property_count": len(correct_props),
        "graph_extract_property_count": len(extract_props),
        "graph_init_triple_count": len(graph_init),
        "graph_correct_triple_count": len(graph_correct),
        "graph_extract_triple_count": len(extract_filtered),
        "graph_correct_expressiveness": round(correct_expressiveness, 2),
        "extract_vs_init": {
            "property_recall": round(ext_init_prop_recall, 2),
            "property_precision": round(ext_init_prop_precision, 2),
            "property_f1": round(ext_init_prop_f1, 2),
            "value_recall": round(ext_init_val_recall, 2),
            "value_precision": round(ext_init_val_precision, 2),
            "value_f1": round(ext_init_val_f1, 2),
        },
        "extract_vs_correct": {
            "property_recall": round(ext_corr_prop_recall, 2),
            "property_precision": round(ext_corr_prop_precision, 2),
            "property_f1": round(ext_corr_prop_f1, 2),
            "value_recall": round(ext_corr_val_recall, 2),
            "value_precision": round(ext_corr_val_precision, 2),
            "value_f1": round(ext_corr_val_f1, 2),
        },
    }


# =============================================================================
# Processing
# =============================================================================

def process_entity(
    entity_uri: str,
    abstract_md: str,
    abstract_clean: str,
    entity_props: List[Dict],
    shape: ShapeHandler,
    type_prop_map: Dict[str, str],
    model,
    tokenizer,
    entity_type: str
) -> Optional[Dict]:
    """Process a single entity: build graph_init, graph_correct, graph_extract, compare.

    abstract_md is the full markdown (used for graph_correct matching).
    abstract_clean is the cleaned plain-text version (used for model extraction).
    """
    entity_name = entity_uri.split("/")[-1]

    # Build graph_init
    graph_init = build_graph_init_triples(entity_uri, entity_props, shape)
    if not graph_init:
        return None

    # Build graph_correct using markdown-aware matching (1_KD-322 method)
    graph_correct = build_graph_correct_triples(graph_init, abstract_md, shape, type_prop_map)
    print("================")
    print(abstract_md)
    print("-------------")
    print(graph_init)
    print("----------------")
    print(graph_correct)
    print("----------------")
    # Build graph_extract: run Kastor extraction on the clean abstract
    input_text = f"{entity_name} : {abstract_clean}"
    predictions = extract_triples(input_text, model, tokenizer)
    raw_output = predictions[0] if predictions else ""
    graph_extract, parsed = parse_turtle_light(raw_output)

    # Standard pipeline metrics
    rdf_graph = triples_to_rdf(graph_extract, shape.relations_map, shape.graph, entity_type)
    rdf_turtle = rdf_graph.serialize(format="turtle") if rdf_graph else None

    if rdf_graph:
        shacl_valid, shacl_report = validate_shacl(rdf_graph, shape.graph)
    else:
        shacl_valid, shacl_report = False, "No RDF graph"

    stats = compute_statistics(graph_extract, shape)
    grounding = verify_grounding(graph_extract, shape.relations_map, abstract_md)

    # Compare graphs
    comparison = compare_graphs(graph_init, graph_correct, graph_extract, shape)

    return {
        "entity_uri": entity_uri,
        "entity_name": entity_name,
        "abstract_md_length": len(abstract_md),
        "abstract_clean_length": len(abstract_clean),
        "raw_output": raw_output,
        "parsed": parsed,
        "graph_init_triples": graph_init,
        "graph_correct_triples": graph_correct,
        "graph_extract_triples": graph_extract,
        "comparison": comparison,
        "shacl_valid": shacl_valid,
        "statistics": {
            "coverage": round(stats.coverage, 2),
            "precision": round(stats.precision, 2),
            "matched_properties": stats.matched_properties,
            "shape_properties": stats.shape_properties,
        },
        "grounding": {
            "grounding_rate": round(grounding.grounding_rate, 2),
            "found_count": grounding.found_count,
            "total_count": grounding.total_count,
        },
    }


def process_class(
    entity_type: str,
    endpoint: str,
    limit: int,
    wiki_agent: str
) -> Dict:
    """Process all entities for a given class.

    1. Load SHACL shape
    2. Query entity URIs from SPARQL endpoint
    3. Batch query graph_init properties from SPARQL endpoint
    4. Fetch Wikipedia markdown abstracts via API
    5. Load Kastor model once, process each entity
    """
    print(f"\n  Loading shape for {entity_type}...")
    shape = ShapeHandler(entity_type)
    class_uri = get_target_class_uri(shape)
    property_uris = get_property_uris(shape)
    type_prop_map = get_property_type_map(shape)

    print(f"  Target class: {class_uri}")
    print(f"  Shape properties: {len(property_uris)}")
    print(f"  Typed properties: {len(type_prop_map)}")

    # Query entity URIs from SPARQL endpoint
    print(f"  Querying entities from {endpoint}...")
    entities = query_entities_of_class(endpoint, class_uri, limit)
    print(f"  Found {len(entities)} entities")

    if not entities:
        return {
            "entity_type": entity_type,
            "class_uri": class_uri,
            "entities_found": 0,
            "entities_processed": 0,
            "aggregate": {},
            "entity_results": [],
            "status": "no_entities"
        }

    # Batch query graph_init properties for all entities
    entity_uris = [e["entity"] for e in entities]
    print(f"  Batch querying properties for {len(entity_uris)} entities...")
    all_props = query_entity_properties_batch(endpoint, entity_uris, property_uris)

    # Load model once for this class
    model_key = f"Kastor{entity_type}"
    if model_key not in KASTOR_MODELS:
        print(f"  WARNING: No model found for {model_key}, skipping")
        return {
            "entity_type": entity_type,
            "class_uri": class_uri,
            "entities_found": len(entities),
            "entities_processed": 0,
            "aggregate": {},
            "entity_results": [],
            "status": "no_model"
        }

    model_repo = KASTOR_MODELS[model_key]["repo"]
    print(f"  Loading model {model_repo}...")
    model, tokenizer = load_model_and_tokenizer(model_repo)

    # Process each entity
    entity_results = []
    for i, ent in enumerate(entities):
        entity_uri = ent["entity"]
        entity_name = entity_uri.replace("http://dbpedia.org/resource/", "") \
                                .replace("https://dbpedia.org/resource/", "")
        # URL-decode for Wikipedia API (e.g. %22Bassy%22 -> "Bassy")
        entity_name_decoded = urllib.parse.unquote(entity_name)
        entity_props = all_props.get(entity_uri, [])

        print(f"  [{i+1}/{len(entities)}] {entity_name_decoded} "
              f"(props: {len(entity_props)})")

        if not entity_props:
            print(f"    Skipping: no properties found in endpoint")
            continue

        # Fetch Wikipedia markdown abstract
        try:
            abstract_md = get_abstract_md(entity_name_decoded, wiki_agent)
        except Exception as e:
            print(f"    Skipping: Wikipedia fetch failed: {e}")
            continue

        if not abstract_md:
            print(f"    Skipping: empty abstract from Wikipedia")
            continue

        # Clean markdown to plain abstract for extraction
        abstract_clean = clean_md_to_abstract(abstract_md)

        print(f"    Abstract MD: {len(abstract_md)} chars -> clean: {len(abstract_clean)} chars")

        try:
            result = process_entity(
                entity_uri, abstract_md, abstract_clean, entity_props, shape,
                type_prop_map, model, tokenizer, entity_type
            )
            if result:
                entity_results.append(result)
                init_n = len(result["graph_init_triples"])
                correct_n = len(result["graph_correct_triples"])
                extract_n = result["comparison"]["graph_extract_triple_count"]
                print(f"    graph_init={init_n} graph_correct={correct_n} graph_extract={extract_n}")
        except Exception as e:
            print(f"    ERROR: {e}")

    # Free model memory
    del model, tokenizer
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass

    # Aggregate metrics
    aggregate = compute_aggregate(entity_results)

    return {
        "entity_type": entity_type,
        "class_uri": class_uri,
        "model_repo": model_repo,
        "entities_found": len(entities),
        "entities_processed": len(entity_results),
        "aggregate": aggregate,
        "entity_results": entity_results,
        "status": "success"
    }


def compute_aggregate(entity_results: List[Dict]) -> Dict:
    """Compute aggregate metrics over a list of entity results."""
    if not entity_results:
        return {}

    n = len(entity_results)

    def avg(key_path):
        """Average a nested key. key_path is a list of keys."""
        total = 0.0
        for r in entity_results:
            val = r
            for k in key_path:
                val = val.get(k, 0) if isinstance(val, dict) else 0
            total += val
        return round(total / n, 2)

    return {
        "count": n,
        "avg_graph_correct_expressiveness": avg(["comparison", "graph_correct_expressiveness"]),
        "avg_extract_vs_init_prop_recall": avg(["comparison", "extract_vs_init", "property_recall"]),
        "avg_extract_vs_init_prop_precision": avg(["comparison", "extract_vs_init", "property_precision"]),
        "avg_extract_vs_init_prop_f1": avg(["comparison", "extract_vs_init", "property_f1"]),
        "avg_extract_vs_init_val_recall": avg(["comparison", "extract_vs_init", "value_recall"]),
        "avg_extract_vs_init_val_precision": avg(["comparison", "extract_vs_init", "value_precision"]),
        "avg_extract_vs_init_val_f1": avg(["comparison", "extract_vs_init", "value_f1"]),
        "avg_extract_vs_correct_prop_recall": avg(["comparison", "extract_vs_correct", "property_recall"]),
        "avg_extract_vs_correct_prop_precision": avg(["comparison", "extract_vs_correct", "property_precision"]),
        "avg_extract_vs_correct_prop_f1": avg(["comparison", "extract_vs_correct", "property_f1"]),
        "avg_extract_vs_correct_val_recall": avg(["comparison", "extract_vs_correct", "value_recall"]),
        "avg_extract_vs_correct_val_precision": avg(["comparison", "extract_vs_correct", "value_precision"]),
        "avg_extract_vs_correct_val_f1": avg(["comparison", "extract_vs_correct", "value_f1"]),
        "avg_coverage": avg(["statistics", "coverage"]),
        "avg_precision": avg(["statistics", "precision"]),
        "avg_grounding": avg(["grounding", "grounding_rate"]),
    }


# =============================================================================
# Run & Summary
# =============================================================================

def run_all(
    endpoint: str,
    limit: int,
    output_file: str,
    wiki_agent: str,
    classes: Optional[List[str]] = None
) -> Dict:
    """Run evaluation on all (or selected) classes."""
    entity_types = classes if classes else ENTITY_TYPES

    print(f"\n{'#'*70}")
    print(f"# KASTOR SPARQL + WIKIPEDIA MD EVALUATION")
    print(f"# Endpoint: {endpoint}")
    print(f"# Limit: {limit} entities per class")
    print(f"# Classes: {len(entity_types)}")
    print(f"# Abstract source: Wikipedia HTML API (markdown)")
    print(f"{'#'*70}")

    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "limit": limit,
            "abstract_source": "wikipedia_md",
            "entity_types": entity_types
        },
        "classes": {},
    }

    for i, entity_type in enumerate(entity_types, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(entity_types)}] {entity_type}")
        print(f"{'='*70}")

        try:
            class_result = process_class(entity_type, endpoint, limit, wiki_agent)
            results["classes"][entity_type] = class_result
        except Exception as e:
            print(f"  FATAL ERROR for {entity_type}: {e}")
            results["classes"][entity_type] = {
                "entity_type": entity_type,
                "status": "error",
                "error": str(e),
                "aggregate": {},
                "entity_results": [],
            }

    # Compute overall summary
    results["summary"] = compute_overall_summary(results["classes"])

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    # Print summary table
    print_summary(results)

    return results


def compute_overall_summary(classes: Dict) -> Dict:
    """Compute overall averages across all classes."""
    successful = [v for v in classes.values() if v.get("aggregate")]
    if not successful:
        return {}

    n = len(successful)
    agg_keys = [
        "avg_graph_correct_expressiveness",
        "avg_extract_vs_init_prop_recall", "avg_extract_vs_init_prop_precision",
        "avg_extract_vs_init_prop_f1",
        "avg_extract_vs_init_val_recall", "avg_extract_vs_init_val_precision",
        "avg_extract_vs_init_val_f1",
        "avg_extract_vs_correct_prop_recall", "avg_extract_vs_correct_prop_precision",
        "avg_extract_vs_correct_prop_f1",
        "avg_extract_vs_correct_val_recall", "avg_extract_vs_correct_val_precision",
        "avg_extract_vs_correct_val_f1",
        "avg_coverage", "avg_precision", "avg_grounding",
    ]

    summary = {"classes_evaluated": n, "total_entities": 0}
    for key in agg_keys:
        vals = [c["aggregate"].get(key, 0) for c in successful]
        summary[key] = round(sum(vals) / n, 2) if vals else 0.0
    summary["total_entities"] = sum(c.get("entities_processed", 0) for c in successful)

    return summary


def print_summary(results: Dict):
    """Print a formatted summary table to the console."""
    classes = results.get("classes", {})
    summary = results.get("summary", {})

    print(f"\n{'#'*100}")
    print("# SUMMARY TABLE")
    print(f"{'#'*100}")

    header = (f"  {'Class':<22} {'N':>4}  {'Corr%':>6}"
              f"  {'ExIniR':>6} {'ExIniP':>6}"
              f"  {'ExCorR':>6} {'ExCorP':>6}"
              f"  {'Cov':>6} {'Gnd':>6}")
    separator = (f"  {'-'*20}  {'----':>4}  {'------':>6}"
                 f"  {'------':>6} {'------':>6}"
                 f"  {'------':>6} {'------':>6}"
                 f"  {'------':>6} {'------':>6}")

    print(header)
    print(separator)

    for entity_type, data in classes.items():
        agg = data.get("aggregate", {})
        n = data.get("entities_processed", 0)
        if not agg or n == 0:
            print(f"  {entity_type:<22} {n:>4}  {'---':>6}"
                  f"  {'---':>6} {'---':>6}"
                  f"  {'---':>6} {'---':>6}"
                  f"  {'---':>6} {'---':>6}")
            continue

        print(f"  {entity_type:<22} {n:>4}"
              f"  {agg.get('avg_graph_correct_expressiveness', 0):>5.1f}%"
              f"  {agg.get('avg_extract_vs_init_prop_recall', 0):>5.1f}%"
              f" {agg.get('avg_extract_vs_init_prop_precision', 0):>5.1f}%"
              f"  {agg.get('avg_extract_vs_correct_prop_recall', 0):>5.1f}%"
              f" {agg.get('avg_extract_vs_correct_prop_precision', 0):>5.1f}%"
              f"  {agg.get('avg_coverage', 0):>5.1f}%"
              f" {agg.get('avg_grounding', 0):>5.1f}%")

    if summary:
        print(separator)
        total_n = summary.get("total_entities", 0)
        print(f"  {'OVERALL':<22} {total_n:>4}"
              f"  {summary.get('avg_graph_correct_expressiveness', 0):>5.1f}%"
              f"  {summary.get('avg_extract_vs_init_prop_recall', 0):>5.1f}%"
              f" {summary.get('avg_extract_vs_init_prop_precision', 0):>5.1f}%"
              f"  {summary.get('avg_extract_vs_correct_prop_recall', 0):>5.1f}%"
              f" {summary.get('avg_extract_vs_correct_prop_precision', 0):>5.1f}%"
              f"  {summary.get('avg_coverage', 0):>5.1f}%"
              f" {summary.get('avg_grounding', 0):>5.1f}%")

    print(f"\n{'#'*100}\n")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate Kastor models against SPARQL endpoint + Wikipedia markdown"
    )
    parser.add_argument(
        "--endpoint", type=str,
        default="http://localhost:8080/sparql",
        help="SPARQL endpoint URL (default: http://localhost:8080/sparql)"
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="Number of entities per class (default: 100)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSON file (default: test_all_results.json in script dir)"
    )
    parser.add_argument(
        "--wiki-agent", type=str, default=DEFAULT_WIKI_AGENT,
        help="Wikipedia API user agent string"
    )
    parser.add_argument(
        "--classes", type=str, nargs="+", default=None,
        choices=ENTITY_TYPES,
        help="Test specific classes only (default: all)"
    )

    args = parser.parse_args()

    if args.output is None:
        script_dir = Path(__file__).parent
        output_file = str(script_dir / "test_all_results.json")
    else:
        output_file = args.output

    run_all(
        endpoint=args.endpoint,
        limit=args.limit,
        output_file=output_file,
        wiki_agent=args.wiki_agent,
        classes=args.classes,
    )
