"""
Run Kastor pipeline on all models and save results.
Usage: python run_all_models.py [--output results.json]
"""

import argparse
import json
from datetime import datetime
from dataclasses import asdict
from pathlib import Path

from kastor_pipeline import (
    KastorPipeline, ShapeHandler, ENTITY_TYPES,
    parse_turtle_light, triples_to_rdf, validate_shacl,
    compute_statistics, verify_grounding
)
from load_kastor_models import load_model_and_tokenizer, extract_triples, KASTOR_MODELS


def run_single_model(entity_type: str, verbose: bool = True):
    """Run pipeline for a single model with proper shape loading."""

    # 1. Get model config
    model_key = f"Kastor{entity_type}"
    if model_key not in KASTOR_MODELS:
        raise ValueError(f"Unknown model: {model_key}")

    config = KASTOR_MODELS[model_key]
    model_repo = config["repo"]
    id_ent = config["id_ent"]
    text = config["abstract"]

    if verbose:
        print(f"\n  Model:  {model_repo}")
        print(f"  Entity: {id_ent}")
        print(f"  Shape:  {entity_type}ShapeTXT2KG_clean.ttl")

    # 2. Load shape
    shape = ShapeHandler(entity_type)
    shape_props = list(shape.relations_map.keys())

    if verbose:
        print(f"  Shape properties: {len(shape_props)}")
        print(f"    Datatype: {len(shape.dt_props)} | Object: {len(shape.obj_props)}")

    # 3. Load model
    if verbose:
        print(f"  Loading model...")
    model, tokenizer = load_model_and_tokenizer(model_repo)

    # 4. Extract triples
    if verbose:
        print(f"  Extracting triples...")
    input_text = f"{id_ent} : {text}"
    predictions = extract_triples(input_text, model, tokenizer)
    raw_output = predictions[0] if predictions else ""

    if verbose:
        print(f"  Raw output: {raw_output[:80]}..." if len(raw_output) > 80 else f"  Raw output: {raw_output}")

    # 5. Parse
    triples, parsed = parse_turtle_light(raw_output)

    if verbose:
        print(f"  Parsed: {parsed} | Triples: {len(triples)}")

    # 6. Convert to RDF
    rdf_graph = triples_to_rdf(triples, shape.relations_map, shape.graph, entity_type)
    rdf_turtle = rdf_graph.serialize(format="turtle") if rdf_graph else None

    # 7. SHACL validation
    if rdf_graph:
        shacl_valid, shacl_report = validate_shacl(rdf_graph, shape.graph)
    else:
        shacl_valid, shacl_report = False, "No RDF graph"

    if verbose:
        print(f"  SHACL Valid: {shacl_valid}")

    # 8. Statistics
    stats = compute_statistics(triples, shape)

    if verbose:
        print(f"  Coverage: {stats.coverage:.1f}% (DT: {stats.datatype.coverage:.1f}% | OBJ: {stats.object.coverage:.1f}%)")
        print(f"  Precision: {stats.precision:.1f}%")

    # 9. Grounding
    grounding = verify_grounding(triples, shape.relations_map, text)

    if verbose:
        print(f"  Grounding: {grounding.grounding_rate:.1f}% ({grounding.found_count}/{grounding.total_count})")

    # Build result
    result = {
        "model_type": entity_type,
        "model_repo": model_repo,
        "shape_file": f"{entity_type}ShapeTXT2KG_clean.ttl",
        "id_ent": id_ent,
        "abstract": text,
        "input_text": input_text,
        "raw_output": raw_output,
        "triples": triples,
        "parsed": parsed,
        "rdf_turtle": rdf_turtle,
        "shacl_valid": shacl_valid,
        "shacl_report": shacl_report if not shacl_valid else None,
        "shape_info": {
            "total_properties": len(shape_props),
            "datatype_properties": len(shape.dt_props),
            "object_properties": len(shape.obj_props),
            "property_list": shape_props,
            "datatype_list": sorted(shape.dt_props),
            "object_list": sorted(shape.obj_props)
        },
        "statistics": {
            "shape_properties": stats.shape_properties,
            "extracted_triples": stats.extracted_triples,
            "extracted_properties": stats.extracted_properties,
            "matched_properties": stats.matched_properties,
            "extra_properties": stats.extra_properties,
            "missing_properties": stats.missing_properties,
            "coverage": round(stats.coverage, 2),
            "precision": round(stats.precision, 2),
            "matched_list": stats.matched_list,
            "extra_list": stats.extra_list,
            "missing_list": stats.missing_list,
            "datatype": {
                "shape_count": stats.datatype.shape_count,
                "extracted_count": stats.datatype.extracted_count,
                "matched_count": stats.datatype.matched_count,
                "missing_count": stats.datatype.missing_count,
                "coverage": round(stats.datatype.coverage, 2),
                "matched_list": stats.datatype.matched_list,
                "missing_list": stats.datatype.missing_list
            },
            "object": {
                "shape_count": stats.object.shape_count,
                "extracted_count": stats.object.extracted_count,
                "matched_count": stats.object.matched_count,
                "missing_count": stats.object.missing_count,
                "coverage": round(stats.object.coverage, 2),
                "matched_list": stats.object.matched_list,
                "missing_list": stats.object.missing_list
            }
        },
        "grounding": {
            "found_count": grounding.found_count,
            "total_count": grounding.total_count,
            "grounding_rate": round(grounding.grounding_rate, 2),
            "verified_triples": grounding.verified_triples
        }
    }

    # Clean up GPU memory
    del model, tokenizer
    try:
        import torch
        torch.cuda.empty_cache()
    except:
        pass

    return result


def run_all(output_file: str = "all_results.json"):
    """Run pipeline on all models."""
    print(f"\n{'#'*70}")
    print(f"# KASTOR BENCHMARK - Running all {len(ENTITY_TYPES)} models")
    print(f"{'#'*70}")

    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "num_models": len(ENTITY_TYPES),
            "entity_types": ENTITY_TYPES
        },
        "models": []
    }

    successful_results = []

    for i, entity_type in enumerate(ENTITY_TYPES, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(ENTITY_TYPES)}] {entity_type}")
        print(f"{'='*70}")

        try:
            result = run_single_model(entity_type, verbose=True)
            result["status"] = "success"
            successful_results.append(result)

        except Exception as e:
            print(f"  ERROR: {e}")
            result = {
                "model_type": entity_type,
                "status": "error",
                "error": str(e)
            }

        results["models"].append(result)

    # Compute aggregate statistics
    if successful_results:
        agg = {
            "models_total": len(ENTITY_TYPES),
            "models_success": len(successful_results),
            "models_failed": len(ENTITY_TYPES) - len(successful_results),
            "shacl_valid_count": sum(1 for r in successful_results if r["shacl_valid"]),
            "parsed_count": sum(1 for r in successful_results if r["parsed"]),
            # Overall
            "avg_coverage": round(sum(r["statistics"]["coverage"] for r in successful_results) / len(successful_results), 2),
            "avg_precision": round(sum(r["statistics"]["precision"] for r in successful_results) / len(successful_results), 2),
            "avg_grounding": round(sum(r["grounding"]["grounding_rate"] for r in successful_results) / len(successful_results), 2),
            "avg_triples": round(sum(r["statistics"]["extracted_triples"] for r in successful_results) / len(successful_results), 2),
            # By category
            "avg_coverage_datatype": round(sum(r["statistics"]["datatype"]["coverage"] for r in successful_results) / len(successful_results), 2),
            "avg_coverage_object": round(sum(r["statistics"]["object"]["coverage"] for r in successful_results) / len(successful_results), 2),
            # Totals
            "total_triples_extracted": sum(r["statistics"]["extracted_triples"] for r in successful_results),
            "total_properties_matched": sum(r["statistics"]["matched_properties"] for r in successful_results),
            "total_grounding_found": sum(r["grounding"]["found_count"] for r in successful_results),
            "total_grounding_total": sum(r["grounding"]["total_count"] for r in successful_results),
        }

        # Per-model summary table
        summary_table = []
        for r in successful_results:
            summary_table.append({
                "model": r["model_type"],
                "entity": r["id_ent"],
                "triples": r["statistics"]["extracted_triples"],
                "parsed": r["parsed"],
                "shacl_valid": r["shacl_valid"],
                "coverage": r["statistics"]["coverage"],
                "coverage_dt": r["statistics"]["datatype"]["coverage"],
                "coverage_obj": r["statistics"]["object"]["coverage"],
                "precision": r["statistics"]["precision"],
                "grounding": r["grounding"]["grounding_rate"]
            })

        results["aggregate"] = agg
        results["summary_table"] = summary_table

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print final summary
    print(f"\n{'#'*70}")
    print("# FINAL SUMMARY")
    print(f"{'#'*70}")

    if successful_results:
        agg = results["aggregate"]
        print(f"\n  Models:        {agg['models_success']}/{agg['models_total']} successful")
        print(f"  Parsed:        {agg['parsed_count']}/{agg['models_success']}")
        print(f"  SHACL Valid:   {agg['shacl_valid_count']}/{agg['models_success']}")
        print(f"\n  --- Averages ---")
        print(f"  Triples:       {agg['avg_triples']}")
        print(f"  Coverage:      {agg['avg_coverage']}%")
        print(f"    - Datatype:  {agg['avg_coverage_datatype']}%")
        print(f"    - Object:    {agg['avg_coverage_object']}%")
        print(f"  Precision:     {agg['avg_precision']}%")
        print(f"  Grounding:     {agg['avg_grounding']}%")

        print(f"\n  --- Per Model ---")
        print(f"  {'Model':<25} {'Triples':>8} {'Coverage':>10} {'DT':>8} {'OBJ':>8} {'Ground':>8} {'SHACL':>6}")
        print(f"  {'-'*23}  {'-'*6}   {'-'*8}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*5}")
        for row in results["summary_table"]:
            shacl = "Yes" if row["shacl_valid"] else "No"
            print(f"  {row['model']:<25} {row['triples']:>8} {row['coverage']:>9.1f}% {row['coverage_dt']:>7.1f}% {row['coverage_obj']:>7.1f}% {row['grounding']:>7.1f}% {shacl:>6}")

    print(f"\n  Results saved to: {output_file}")
    print(f"{'#'*70}\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Kastor on all models")
    parser.add_argument("--output", type=str, default="all_results.json", help="Output JSON file")
    args = parser.parse_args()

    run_all(args.output)
