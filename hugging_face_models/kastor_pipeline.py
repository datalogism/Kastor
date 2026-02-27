"""
Kastor Pipeline: Load model, extract triples, parse, validate with SHACL.
Usage: python kastor_pipeline.py --model_type Artist --text "Your text here"
"""

import argparse
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rdflib import Graph, Literal, Namespace, URIRef
from pyshacl import validate
from unidecode import unidecode

try:
    import datefinder
    HAS_DATEFINDER = True
except ImportError:
    HAS_DATEFINDER = False

from load_kastor_models import load_model_and_tokenizer, extract_triples, KASTOR_MODELS

# =============================================================================
# Configuration
# =============================================================================

SHAPES_DIR = Path(__file__).parent.parent / "shapes" / "txt2kg"

ENTITY_TYPES = [
    "Airport", "Artist", "Athlete", "Building", "CelestialBody", "City",
    "Company", "Film", "Food", "MeanOfTransportation", "MusicalWork",
    "Politician", "Scientist", "SportsTeam", "University", "WrittenWork"
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PropertyStats:
    shape_count: int = 0
    extracted_count: int = 0
    matched_count: int = 0
    missing_count: int = 0
    coverage: float = 0.0
    matched_list: List[str] = field(default_factory=list)
    missing_list: List[str] = field(default_factory=list)


@dataclass
class Statistics:
    shape_properties: int = 0
    extracted_triples: int = 0
    extracted_properties: int = 0
    matched_properties: int = 0
    extra_properties: int = 0
    missing_properties: int = 0
    coverage: float = 0.0
    precision: float = 0.0
    matched_list: List[str] = field(default_factory=list)
    extra_list: List[str] = field(default_factory=list)
    missing_list: List[str] = field(default_factory=list)
    datatype: PropertyStats = field(default_factory=PropertyStats)
    object: PropertyStats = field(default_factory=PropertyStats)


@dataclass
class GroundingResult:
    verified_triples: List[Dict] = field(default_factory=list)
    found_count: int = 0
    total_count: int = 0
    grounding_rate: float = 0.0


@dataclass
class PipelineResult:
    model_type: str
    model_repo: str
    id_ent: str
    raw_output: str
    triples: List[List[str]]
    parsed: bool
    rdf_turtle: Optional[str]
    shacl_valid: bool
    shacl_report: Optional[str]
    statistics: Statistics
    grounding: GroundingResult


# =============================================================================
# Shape & RDF Utilities
# =============================================================================

class ShapeHandler:
    """Handle SHACL shape loading and property extraction."""

    def __init__(self, model_type: str):
        self.model_type = model_type
        self.graph = self._load_shape()
        self.relations_map = self._extract_relations()
        self.dt_props, self.obj_props = self._categorize_properties()

    def _load_shape(self) -> Graph:
        shape_file = SHAPES_DIR / f"{self.model_type}ShapeTXT2KG_clean.ttl"
        g = Graph()
        g.parse(shape_file, format="turtle")
        return g

    def _extract_relations(self) -> Dict:
        query = """
        SELECT DISTINCT ?prop ?datatype ?class WHERE {
            ?a sh:path ?prop .
            OPTIONAL { ?a sh:datatype ?datatype }
            OPTIONAL { ?a sh:class ?class }
        }"""
        relations = {}
        for row in self.graph.query(query):
            prop_uri = str(row[0])
            prop_name = prop_uri.split("#")[-1] if "#" in prop_uri else prop_uri.split("/")[-1]
            relations[prop_name] = {"ns": URIRef(prop_uri), "dt": row[1] or row[2]}
        return relations

    def _categorize_properties(self) -> Tuple[set, set]:
        dt_props, obj_props = set(), set()
        for prop, info in self.relations_map.items():
            dt = str(info.get("dt", "")) if info.get("dt") else ""
            if "XMLSchema" in dt or "xsd:" in dt:
                dt_props.add(prop)
            elif "dbpedia.org" in dt or "dbo:" in dt:
                obj_props.add(prop)
            else:
                dt_props.add(prop)
        return dt_props, obj_props


# =============================================================================
# Parsing Utilities
# =============================================================================

def clean_entity(txt: str) -> str:
    """Clean entity name for URI."""
    clean = txt.strip().replace("<", "").replace(">", "").replace(" ", "_")
    clean = clean.replace("http://dbpedia.org/resource/", "").replace("dbr:", "")
    if "%" not in clean:
        clean = urllib.parse.quote(clean).replace(".", "%2E")
    return clean.strip()


def parse_turtle_light(txt: str) -> Tuple[List[List[str]], bool]:
    """Parse Turtle Light (1 line factorized) format to list of triples.

    Handles multiple formats:
    - :subject a:Type;:property "literal value".
    - :subject a:Type;:property :ObjectValue.
    - :subject a:Type;:property:ObjectValue.  (no space before object)
    - :subject a:Type;:property :Val1, :Val2.  (multiple values)
    """
    txt = txt.replace("<s>", "").replace("</s>", "").replace("<pad>", "").strip()
    if not txt or len(txt) < 3:
        return [], False

    try:
        triples = []
        parts = txt.split(";")

        # Extract subject from first part
        # Pattern: :Subject_Name a:Type or :Subject_Name a :Type
        first_part = parts[0].strip()

        # Try to extract subject - handle both ":Subject a:Type" and ":Subject a :Type"
        subj_match = re.match(r'^:([^\s]+)\s+a\s*:?', first_part)
        if not subj_match:
            # Fallback: try original pattern
            subj_match_list = re.findall(r"(?<=:).*?(?=\s)", first_part)
            if not subj_match_list:
                return [], False
            subj = clean_entity(subj_match_list[0])
        else:
            subj = clean_entity(subj_match.group(1))

        # Extract type
        for t in ["a", "type", "rdfs:type"]:
            pattern = f" {t} " if t == "a" else f" {t}:"
            if f" {t}:" in first_part or f" {t} " in first_part:
                # Split on the type keyword
                type_part = re.split(rf'\s+{t}\s*:?', first_part, maxsplit=1)
                if len(type_part) > 1:
                    type_val = type_part[1].replace(":", "").strip().rstrip(".")
                    triples.append([subj, "type", type_val.strip()])
                break

        # Extract properties from remaining parts
        for part in parts[1:]:
            part = part.strip().rstrip(".")
            if not part:
                continue

            # Handle literal values (quoted strings)
            if '"' in part:
                # Pattern: :property "value" or :property"value"
                lit_match = re.match(r'^:([a-zA-Z_][a-zA-Z0-9_]*)\s*"([^"]*)"', part)
                if lit_match:
                    rel = lit_match.group(1)
                    val = lit_match.group(2)
                    triples.append([subj, rel, val])
                continue

            # Handle object properties
            # Pattern 1: :property :Value (with space)
            # Pattern 2: :property:Value (no space - double colon)
            # Pattern 3: :property :Val1, :Val2 (multiple values)

            # First, try to extract the property name
            # Look for :propertyName followed by either space+colon or direct colon
            obj_match = re.match(r'^:([a-zA-Z_][a-zA-Z0-9_]*)(.*)$', part)
            if not obj_match:
                continue

            rel = obj_match.group(1)
            rest = obj_match.group(2).strip()

            if not rest:
                continue

            # Parse the value(s)
            # Could be: ":Value", " :Value", ":Value, :Value2", " :Value, :Value2"
            # Remove leading space or colon to get to values
            if rest.startswith(':'):
                values_str = rest[1:]  # Remove leading colon
            elif rest.startswith(' :'):
                values_str = rest[2:]  # Remove " :"
            elif rest.startswith(' '):
                values_str = rest[1:]  # Remove leading space
                if values_str.startswith(':'):
                    values_str = values_str[1:]
            else:
                values_str = rest

            # Split on comma for multiple values
            # Pattern: "Value1, :Value2" or "Value1,:Value2"
            value_parts = re.split(r',\s*:?', values_str)

            for val in value_parts:
                val = val.strip().rstrip(".").rstrip(";")
                if val:
                    # Clean up any remaining colons at the start
                    val = val.lstrip(':').strip()
                    if val:
                        triples.append([subj, rel, ":" + val])

        return triples, True
    except Exception as e:
        print(f"Parse error: {e}")
        return [], False


def triples_to_rdf(triples: List, relations_map: Dict, shape_graph: Graph, model_type: str) -> Optional[Graph]:
    """Convert list of triples to RDF Graph."""
    if not triples:
        return None

    g = Graph()
    for ns_prefix, namespace in shape_graph.namespaces():
        g.bind(ns_prefix, Namespace(str(namespace)))

    dbr = Namespace("http://dbpedia.org/resource/")
    dbo = Namespace("http://dbpedia.org/ontology/")
    g.bind("dbr", dbr)
    g.bind("dbo", dbo)

    entity_uri = URIRef(f"http://dbpedia.org/resource/{clean_entity(triples[0][0])}")
    type_uri = URIRef(f"http://dbpedia.org/ontology/{model_type}")
    g.add((entity_uri, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), type_uri))

    for subj, prop, val in triples:
        if prop in ["type", "a"] or prop not in relations_map:
            continue
        prop_info = relations_map[prop]
        dt = prop_info["dt"]

        if dt and "dbpedia.org" in str(dt):
            obj_uri = URIRef(f"http://dbpedia.org/resource/{clean_entity(val.replace(':', ''))}")
            g.add((entity_uri, prop_info["ns"], obj_uri))
        else:
            g.add((entity_uri, prop_info["ns"], Literal(val, datatype=dt)))

    return g


# =============================================================================
# Validation & Statistics
# =============================================================================

def validate_shacl(rdf_graph: Graph, shape_graph: Graph) -> Tuple[bool, str]:
    """Validate RDF graph against SHACL shape."""
    try:
        conforms, _, results_text = validate(rdf_graph, shacl_graph=shape_graph, inference="rdfs")
        return conforms, results_text
    except Exception as e:
        return False, str(e)


def compute_statistics(triples: List, shape: ShapeHandler) -> Statistics:
    """Compute extraction statistics."""
    shape_props = set(shape.relations_map.keys())
    extracted = set(t[1] for t in triples if t[1] not in ["type", "a"])

    matched = extracted & shape_props
    extra = extracted - shape_props
    missing = shape_props - extracted

    def calc_prop_stats(prop_set: set) -> PropertyStats:
        s = prop_set & shape_props
        m = matched & prop_set
        return PropertyStats(
            shape_count=len(s),
            extracted_count=len(extracted & prop_set),
            matched_count=len(m),
            missing_count=len(s - extracted),
            coverage=len(m) / len(s) * 100 if s else 0,
            matched_list=sorted(m),
            missing_list=sorted(s - extracted)
        )

    return Statistics(
        shape_properties=len(shape_props),
        extracted_triples=len(triples),
        extracted_properties=len(extracted),
        matched_properties=len(matched),
        extra_properties=len(extra),
        missing_properties=len(missing),
        coverage=len(matched) / len(shape_props) * 100 if shape_props else 0,
        precision=len(matched) / len(extracted) * 100 if extracted else 0,
        matched_list=sorted(matched),
        extra_list=sorted(extra),
        missing_list=sorted(missing),
        datatype=calc_prop_stats(shape.dt_props),
        object=calc_prop_stats(shape.obj_props)
    )


def find_in_text(text: str, value: str, datatype: Optional[str]) -> bool:
    """Check if value is expressed in text."""
    if not value or not text:
        return False

    dt_str = str(datatype) if datatype else ""
    value = str(value).strip()

    # Year
    if "Year" in dt_str or "gYear" in dt_str:
        return value in text

    # Date
    if "date" in dt_str.lower() and HAS_DATEFINDER:
        try:
            dates = [m.strftime('%Y-%m-%d') for m in datefinder.find_dates(text) if m]
            return value in dates
        except:
            return value in text

    # String
    if "string" in dt_str.lower():
        return value.lower() in text.lower() or unidecode(value.lower()) in unidecode(text.lower())

    # Object property
    if "dbpedia.org" in dt_str or value.startswith(":"):
        val_clean = value.replace(":", "").replace("_", " ").strip()
        return val_clean.lower() in text.lower() or unidecode(val_clean.lower()) in unidecode(text.lower())

    return value.lower() in text.lower()


def verify_grounding(triples: List, relations_map: Dict, text: str) -> GroundingResult:
    """Verify if extracted values are grounded in source text."""
    results = []
    for triple in triples:
        if len(triple) != 3 or triple[1] in ["type", "a"]:
            continue
        prop, val = triple[1], triple[2]
        dt = relations_map.get(prop, {}).get("dt")
        results.append({
            "property": prop,
            "value": val,
            "datatype": str(dt) if dt else "unknown",
            "found_in_text": find_in_text(text, val, dt)
        })

    found = sum(1 for r in results if r["found_in_text"])
    return GroundingResult(
        verified_triples=results,
        found_count=found,
        total_count=len(results),
        grounding_rate=found / len(results) * 100 if results else 0
    )


# =============================================================================
# Pipeline
# =============================================================================

class KastorPipeline:
    """Main pipeline for Kastor triple extraction."""

    def __init__(self, model_type: str = "Artist", verbose: bool = True):
        self.model_type = model_type
        self.verbose = verbose
        self.shape = ShapeHandler(model_type)
        self.model = None
        self.tokenizer = None

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def load_model(self):
        """Load the HuggingFace model."""
        model_key = f"Kastor{self.model_type}"
        self.model_repo = KASTOR_MODELS[model_key]["repo"]
        self.model, self.tokenizer = load_model_and_tokenizer(self.model_repo)

    def run(self, id_ent: str, text: str) -> PipelineResult:
        """Run the full pipeline."""
        self._log(f"\n{'='*60}\nKASTOR PIPELINE - {self.model_type}\n{'='*60}")

        # Load model if needed
        if self.model is None:
            self._log("\n[1] Loading model...")
            self.load_model()

        # Extract
        self._log("\n[2] Extracting triples...")
        raw_output = extract_triples(f"{id_ent} : {text}", self.model, self.tokenizer)[0]
        self._log(f"    Raw: {raw_output[:100]}..." if len(raw_output) > 100 else f"    Raw: {raw_output}")

        # Parse
        self._log("\n[3] Parsing...")
        triples, parsed = parse_turtle_light(raw_output)
        self._log(f"    Parsed: {parsed} | Triples: {len(triples)}")

        # Convert to RDF
        self._log("\n[4] Converting to RDF...")
        rdf_graph = triples_to_rdf(triples, self.shape.relations_map, self.shape.graph, self.model_type)
        turtle_output = rdf_graph.serialize(format="turtle") if rdf_graph else None

        # Validate
        self._log("\n[5] SHACL Validation...")
        shacl_valid, shacl_report = validate_shacl(rdf_graph, self.shape.graph) if rdf_graph else (False, "No graph")
        self._log(f"    Valid: {shacl_valid}")

        # Statistics
        self._log("\n[6] Statistics...")
        stats = compute_statistics(triples, self.shape)
        self._print_stats(stats)

        # Grounding
        self._log("\n[7] Grounding Verification...")
        grounding = verify_grounding(triples, self.shape.relations_map, text)
        self._print_grounding(grounding)

        # Summary
        self._print_summary(stats, grounding, shacl_valid, id_ent, len(triples), parsed)

        return PipelineResult(
            model_type=self.model_type,
            model_repo=self.model_repo,
            id_ent=id_ent,
            raw_output=raw_output,
            triples=triples,
            parsed=parsed,
            rdf_turtle=turtle_output,
            shacl_valid=shacl_valid,
            shacl_report=shacl_report if not shacl_valid else None,
            statistics=stats,
            grounding=grounding
        )

    def _print_stats(self, s: Statistics):
        self._log(f"    Coverage: {s.coverage:.1f}% | Precision: {s.precision:.1f}%")
        self._log(f"    Datatype: {s.datatype.matched_count}/{s.datatype.shape_count} ({s.datatype.coverage:.1f}%)")
        self._log(f"    Object:   {s.object.matched_count}/{s.object.shape_count} ({s.object.coverage:.1f}%)")

    def _print_grounding(self, g: GroundingResult):
        self._log(f"    Grounding: {g.grounding_rate:.1f}% ({g.found_count}/{g.total_count})")
        for v in g.verified_triples:
            status = "OK" if v['found_in_text'] else "NOT FOUND"
            val_display = v['value'][:40] + "..." if len(str(v['value'])) > 40 else v['value']
            self._log(f"      [{status}] {v['property']}: {val_display}")

    def _print_summary(self, s: Statistics, g: GroundingResult, valid: bool, ent: str, n: int, parsed: bool):
        self._log(f"\n{'='*60}\nSUMMARY\n{'='*60}")
        self._log(f"  Entity:       {ent}")
        self._log(f"  Parsed:       {parsed} | Triples: {n}")
        self._log(f"  SHACL Valid:  {valid}")
        self._log(f"  Coverage:     {s.coverage:.1f}% (DT: {s.datatype.coverage:.1f}% | OBJ: {s.object.coverage:.1f}%)")
        self._log(f"  Precision:    {s.precision:.1f}%")
        self._log(f"  Grounding:    {g.grounding_rate:.1f}%")
        self._log(f"{'='*60}\n")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kastor Pipeline")
    parser.add_argument("--model_type", type=str, default="Artist", choices=ENTITY_TYPES)
    parser.add_argument("--id_ent", type=str, default=None)
    parser.add_argument("--text", type=str, default=None)
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    args = parser.parse_args()

    # Use defaults if not provided
    model_key = f"Kastor{args.model_type}"
    id_ent = args.id_ent or KASTOR_MODELS[model_key]["id_ent"]
    text = args.text or KASTOR_MODELS[model_key]["abstract"]

    pipeline = KastorPipeline(model_type=args.model_type, verbose=not args.quiet)
    result = pipeline.run(id_ent, text)
