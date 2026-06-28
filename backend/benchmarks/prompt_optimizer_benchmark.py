"""
Prompt Optimizer Benchmark

Measures the impact of prompt optimization on VLM extraction quality.
Runs extraction with baseline vs optimized prompts and compares results.

Usage:
    uv run python -m benchmarks.prompt_optimizer_benchmark \
        --provider gemini --model gemini-2.5-flash \
        --method docling-parse --iterations 1

    # With ground truth for accuracy scoring:
    uv run python -m benchmarks.prompt_optimizer_benchmark \
        --provider gemini --model gemini-2.5-flash \
        --expected '{"invoice_number":"INV-123","total":150.00}'

    # Full A/B with CORD dataset:
    uv run python -m benchmarks.prompt_optimizer_benchmark \
        --provider gemini --model gemini-2.5-flash \
        --dataset cord --max-samples 5
"""

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

from benchmarks.scoring import score_results
from benchmarks._helpers import (
    count_tokens_approx,
    count_populated_fields,
    assess_file,
    run_single_extraction,
)
from services.prompt_optimizer import PromptOptimizer
from services.schema_service import SchemaService

logger = logging.getLogger(__name__)


async def run_ab_comparison(
    file_path: str,
    schema_definition: dict,
    schema_name: str,
    provider_name: str,
    model: str,
    extraction_method: str,
    expected: dict | None = None,
    iterations: int = 1,
) -> Dict[str, Any]:
    optimizer = PromptOptimizer()

    baseline_prompt = "Extract all information from this document"
    baseline_system = None

    file_type = "document" if Path(file_path).suffix.lower() == ".pdf" else "image"
    file_assessment = assess_file(file_path, file_type)

    prompt_result = await optimizer.optimize_prompt(
        prompt=baseline_prompt,
        schema_definition=schema_definition,
        schema_name=schema_name,
        provider=provider_name,
        model=model,
        processing_method=extraction_method,
        quality_score=file_assessment["quality_score"],
        doc_type=file_assessment["doc_type"],
    )

    optimized_prompt = prompt_result.user_prompt
    optimized_schema = prompt_result.enriched_schema or schema_definition
    optimized_system = prompt_result.system_prompt

    baseline_runs: List[Dict[str, Any]] = []
    optimized_runs: List[Dict[str, Any]] = []

    for _ in range(iterations):
        b = await run_single_extraction(
            file_path,
            schema_definition,
            baseline_prompt,
            baseline_system,
            provider_name,
            model,
            extraction_method,
        )
        baseline_runs.append(b)

        o = await run_single_extraction(
            file_path,
            optimized_schema,
            optimized_prompt,
            optimized_system,
            provider_name,
            model,
            extraction_method,
        )
        optimized_runs.append(o)

    def _aggregate(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        successes = sum(1 for r in runs if r["success"])
        avg_time = sum(r["elapsed_seconds"] for r in runs) / len(runs)
        all_data = [r.get("data") for r in runs if r["data"]]
        merged = all_data[0] if all_data else None
        return {
            "total_runs": len(runs),
            "successes": successes,
            "success_rate": round(successes / len(runs), 3),
            "avg_time_seconds": round(avg_time, 3),
            "data": merged,
            "field_stats": count_populated_fields(merged),
        }

    baseline_agg = _aggregate(baseline_runs)
    optimized_agg = _aggregate(optimized_runs)

    accuracy = {}
    if expected:
        if baseline_agg["data"]:
            accuracy["baseline"] = score_results(expected, baseline_agg["data"])
        if optimized_agg["data"]:
            accuracy["optimized"] = score_results(expected, optimized_agg["data"])

    prompt_sizes = {
        "baseline_user_tokens": count_tokens_approx(baseline_prompt),
        "optimized_user_tokens": count_tokens_approx(optimized_prompt),
        "optimized_system_tokens": count_tokens_approx(optimized_system or ""),
        "optimized_schema_fields": len(optimized_schema.get("properties", {})),
    }

    return {
        "config": {
            "file": file_path,
            "schema": schema_name,
            "provider": provider_name,
            "model": model,
            "method": extraction_method,
            "iterations": iterations,
        },
        "optimization_meta": {
            "doc_type_detected": prompt_result.doc_type_used,
            "cot_enabled": prompt_result.cot_enabled,
            "hints_injected": prompt_result.hints_injected,
            "quality_score": file_assessment["quality_score"],
            "classifier_doc_type": file_assessment["doc_type"],
        },
        "prompt_sizes": prompt_sizes,
        "baseline": baseline_agg,
        "optimized": optimized_agg,
        "accuracy": accuracy,
        "comparison": {
            "completeness_delta": round(
                optimized_agg["field_stats"]["completeness"]
                - baseline_agg["field_stats"]["completeness"],
                3,
            ),
            "time_delta_seconds": round(
                optimized_agg["avg_time_seconds"] - baseline_agg["avg_time_seconds"], 3
            ),
        },
    }


def _print_report(report: Dict[str, Any]) -> None:
    meta = report["optimization_meta"]
    b = report["baseline"]
    o = report["optimized"]
    c = report["comparison"]
    acc = report.get("accuracy", {})

    print(f"\n{'=' * 70}")
    print("  PROMPT OPTIMIZER BENCHMARK REPORT")
    print(f"{'=' * 70}")
    print(f"  File:     {report['config']['file']}")
    print(f"  Schema:   {report['config']['schema']}")
    print(f"  Provider: {report['config']['provider']} / {report['config']['model']}")
    print(f"  Method:   {report['config']['method']}")
    print(f"  Doc type: {meta['doc_type_detected']}")
    print(f"  CoT:      {meta['cot_enabled']}  |  Hints: {meta['hints_injected']}")
    if meta.get("quality_score") is not None:
        print(f"  Quality:  {meta['quality_score']:.1f}/100")
    if meta.get("classifier_doc_type"):
        print(f"  Classifier doc type: {meta['classifier_doc_type']}")
    print(f"{'─' * 70}")
    print(f"  {'Metric':<28} {'Baseline':>14} {'Optimized':>14} {'Delta':>14}")
    print(f"{'─' * 70}")
    print(
        f"  {'Success rate':<28} {b['success_rate']:>14.1%} {o['success_rate']:>14.1%}"
    )
    print(
        f"  {'Avg time (s)':<28} {b['avg_time_seconds']:>14.3f} {o['avg_time_seconds']:>14.3f} {c['time_delta_seconds']:>+14.3f}"
    )
    print(
        f"  {'Field completeness':<28} {b['field_stats']['completeness']:>14.1%} {o['field_stats']['completeness']:>14.1%} {c['completeness_delta']:>+14.1%}"
    )
    print(
        f"  {'Populated fields':<28} {b['field_stats']['populated']:>14} {o['field_stats']['populated']:>14} {o['field_stats']['populated'] - b['field_stats']['populated']:>+14}"
    )

    if acc:
        print(f"{'─' * 70}")
        if "baseline" in acc:
            print(
                f"  {'Accuracy (overall)':<28} {acc['baseline']['overall_score']:>14.1%}",
                end="",
            )
        if "optimized" in acc:
            delta = acc["optimized"]["overall_score"] - acc.get("baseline", {}).get(
                "overall_score", 0
            )
            print(f" {acc['optimized']['overall_score']:>14.1%} {delta:>+14.1%}")
        else:
            print()
        if "baseline" in acc:
            print(
                f"  {'Fields matched (≥0.85)':<28} {acc['baseline']['matched_fields']:>14}/{acc['baseline']['total_fields']}",
                end="",
            )
        if "optimized" in acc:
            print(
                f" {acc['optimized']['matched_fields']:>14}/{acc['optimized']['total_fields']}"
            )
        else:
            print()

    sizes = report["prompt_sizes"]
    print(f"{'─' * 70}")
    print(
        f"  {'Prompt tokens (user)':<28} {sizes['baseline_user_tokens']:>14} {sizes['optimized_user_tokens']:>14}"
    )
    print(
        f"  {'System prompt tokens':<28} {'N/A':>14} {sizes['optimized_system_tokens']:>14}"
    )
    print(f"  {'Schema fields':<28} {sizes['optimized_schema_fields']:>14}")
    print(f"{'=' * 70}\n")


async def run_dataset_benchmark(
    provider_name: str,
    model: str,
    extraction_method: str,
    max_samples: int = 5,
) -> List[Dict[str, Any]]:
    from benchmarks.datasets import BenchmarkSample, load_dataset

    samples: List[BenchmarkSample] = load_dataset("cord", limit=max_samples)

    results = []
    for i, sample in enumerate(samples):
        print(
            f"\n--- Sample {i + 1}/{len(samples)}: {Path(sample.image_path).name} ---"
        )
        report = await run_ab_comparison(
            file_path=sample.image_path,
            schema_definition=sample.schema,
            schema_name="receipt",
            provider_name=provider_name,
            model=model,
            extraction_method=extraction_method,
            expected=sample.expected,
        )
        results.append(report)
        _print_report(report)

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Optimizer Benchmark")
    parser.add_argument("--file", default=None, help="Single file to benchmark")
    parser.add_argument(
        "--schema",
        default="Generic",
        help="Schema name (Invoice, Receipt, ID, Generic)",
    )
    parser.add_argument(
        "--expected",
        default=None,
        help="JSON file or inline JSON with expected results",
    )
    parser.add_argument("--provider", default="gemini", help="VLM provider")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model name")
    parser.add_argument("--method", default="docling-parse", help="Extraction method")
    parser.add_argument(
        "--iterations", type=int, default=1, help="Number of iterations per variant"
    )
    parser.add_argument("--dataset", default=None, help="Dataset name (e.g., 'cord')")
    parser.add_argument(
        "--max-samples", type=int, default=5, help="Max samples from dataset"
    )
    parser.add_argument("--output", default=None, help="Output JSON file path")
    args = parser.parse_args()

    from services.provider_utils import resolve_provider_api_key

    api_key = resolve_provider_api_key(args.provider)
    if not api_key:
        print(f"ERROR: No API key for {args.provider}")
        return

    if args.dataset:
        results = await run_dataset_benchmark(
            args.provider,
            args.model,
            args.method,
            args.max_samples,
        )
        output_path = (
            args.output
            or f"benchmark_prompt_optimizer_{args.dataset}_{int(time.time())}.json"
        )
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")
        return

    if not args.file:
        print("ERROR: Provide --file or --dataset")
        return

    templates = SchemaService.get_builtin_templates()
    schema_definition = templates.get(args.schema, templates["Generic"])

    expected = None
    if args.expected:
        p = Path(args.expected)
        if p.exists():
            with open(p) as f:
                expected = json.load(f)
        else:
            expected = json.loads(args.expected)

    report = await run_ab_comparison(
        file_path=args.file,
        schema_definition=schema_definition,
        schema_name=args.schema,
        provider_name=args.provider,
        model=args.model,
        extraction_method=args.method,
        expected=expected,
        iterations=args.iterations,
    )

    _print_report(report)

    output_path = (
        args.output or f"benchmark_prompt_{args.schema.lower()}_{int(time.time())}.json"
    )
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Full report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
