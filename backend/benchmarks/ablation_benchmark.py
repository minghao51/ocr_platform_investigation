"""
Prompt Optimizer Ablation Benchmark

Systematically tests each optimizer technique independently to measure
its individual contribution to extraction quality. Results are persisted
to the database (benchmark_runs / benchmark_results) for historical comparison.

Ablation conditions:
  0. baseline       — bare prompt, no system prompt, no schema enrichment
  1. system_prompt  — doc-type-aware system role + rules only
  2. schema_enrich  — auto-describe fields in schema JSON
  3. xml_sandwich   — wrap prompt in XML tags with extraction guidance
  4. cot            — chain-of-thought reasoning instructions
  5. full           — all techniques combined (production optimizer)

Usage:
    # Run on CORD dataset (10 samples, 2 providers)
    dotenvx run -- uv run python -m benchmarks.ablation_benchmark \
        --providers gemini openrouter --max-samples 10

    # Single file ablation
    dotenvx run -- uv run python -m benchmarks.ablation_benchmark \
        --file tests/fixtures/invoice.pdf --schema Invoice \
        --providers gemini

    # Custom ground truth
    dotenvx run -- uv run python -m benchmarks.ablation_benchmark \
        --file tests/fixtures/receipt.jpg --schema Receipt \
        --expected '{"merchant":"MARTHA'"'"'S CAFE","total":38.95}'
"""

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from benchmarks.scoring import score_results
from services.prompt_optimizer import PromptOptimizer, PromptResult
from services.prompt_templates import (
    COT_INSTRUCTION,
    classify_doc_type_hint,
    get_doc_type_template,
)
from services.schema_service import SchemaService
from services.quality_gate import QualityGate
from services.image_service import ImageService
from services.document_classifier import DocumentClassifier

logger = logging.getLogger(__name__)

ABLATION_CONDITIONS = [
    "baseline",
    "system_prompt",
    "schema_enrich",
    "xml_sandwich",
    "cot",
    "full",
]


def _count_tokens_approx(text: str) -> int:
    return len(text) // 4


def _count_populated(data: dict | None) -> Dict[str, Any]:
    if not data:
        return {"total": 0, "populated": 0, "null": 0, "completeness": 0.0}

    def _walk(obj, stats):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if v is None:
                    stats["null"] += 1
                elif isinstance(v, (dict, list)):
                    _walk(v, stats)
                elif str(v).strip() == "":
                    stats["null"] += 1
                else:
                    stats["populated"] += 1
                stats["total"] += 1
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, stats)

    stats = {"total": 0, "populated": 0, "null": 0}
    _walk(data, stats)
    stats["completeness"] = round(stats["populated"] / stats["total"], 3) if stats["total"] > 0 else 0.0
    return stats


def _assess_file(file_path: str) -> Dict[str, Any]:
    quality_score = None
    doc_type = None
    file_type = "document" if file_path.lower().endswith(".pdf") else "image"

    if file_type == "image":
        try:
            img = ImageService.load_image(file_path)
            quality_score = QualityGate().assess(img).overall_score
        except Exception:
            pass

    if file_path.lower().endswith(".pdf"):
        try:
            analysis = DocumentClassifier().analyze_document(file_path)
            if analysis.has_tables and analysis.complexity_score > 70:
                doc_type = "table_heavy"
            elif analysis.text_density < 50:
                doc_type = "handwritten"
        except Exception:
            pass

    return {"quality_score": quality_score, "doc_type": doc_type}


def _build_ablation_prompt(
    condition: str,
    base_prompt: str,
    schema_definition: dict | None,
    schema_name: str | None,
    doc_type: str | None,
    quality_score: float | None,
) -> PromptResult:
    """
    Build prompt for a single ablation condition.
    Each condition enables exactly one optimizer technique.
    """
    resolved_doc_type = doc_type or classify_doc_type_hint(schema_name, schema_definition)

    if condition == "baseline":
        return PromptResult(
            system_prompt="",
            user_prompt=base_prompt,
            enriched_schema=None,
            doc_type_used="generic",
            cot_enabled=False,
            hints_injected=False,
        )

    template = get_doc_type_template(resolved_doc_type)

    if condition == "system_prompt":
        role = template["system_role"]
        system_prompt = (
            role
            + "\n\nRules:\n"
            "  - Return ONLY valid JSON matching the provided schema\n"
            "  - Do NOT include explanations, markdown formatting, or commentary\n"
            "  - If a field value is not visible or legible, use null\n"
            "  - Preserve exact values (do not normalize or reformat dates/numbers)\n"
            "  - For monetary amounts, use numbers without currency symbols"
        )
        return PromptResult(
            system_prompt=system_prompt,
            user_prompt=base_prompt + "\n\nRespond ONLY with valid JSON. No explanations, no markdown.",
            enriched_schema=None,
            doc_type_used=resolved_doc_type,
            cot_enabled=False,
            hints_injected=False,
        )

    if condition == "schema_enrich":
        optimizer = PromptOptimizer()
        enriched = optimizer._enrich_schema_descriptions(schema_definition)
        user_parts = [base_prompt]
        if enriched:
            user_parts.append("\n\nSchema:\n" + json.dumps(enriched, indent=2))
        user_parts.append("\n\nRespond ONLY with valid JSON. No explanations, no markdown.")
        return PromptResult(
            system_prompt="",
            user_prompt="\n".join(user_parts),
            enriched_schema=enriched,
            doc_type_used="generic",
            cot_enabled=False,
            hints_injected=False,
        )

    if condition == "xml_sandwich":
        extraction_hints = template.get("extraction_hints", [])
        parts = ["<instructions>", base_prompt, "</instructions>"]
        if extraction_hints:
            parts.append("\n\n<extraction_guidance>")
            for hint in extraction_hints:
                parts.append(f"- {hint}")
            parts.append("</extraction_guidance>")
        if schema_definition:
            parts.append("\n\n<target_schema>")
            parts.append(json.dumps(schema_definition, indent=2))
            parts.append("</target_schema>")
        parts.append(
            "\n\nRespond ONLY with valid JSON matching the target_schema. "
            "No explanations, no markdown, no commentary."
        )
        return PromptResult(
            system_prompt="",
            user_prompt="\n".join(parts),
            enriched_schema=None,
            doc_type_used=resolved_doc_type,
            cot_enabled=False,
            hints_injected=False,
        )

    if condition == "cot":
        use_cot = resolved_doc_type == "handwritten" or (quality_score is not None and quality_score < 50.0)
        user_parts = [base_prompt]
        if use_cot:
            user_parts.append(COT_INSTRUCTION)
        user_parts.append("\n\nRespond ONLY with valid JSON. No explanations, no markdown.")
        return PromptResult(
            system_prompt="",
            user_prompt="\n".join(user_parts),
            enriched_schema=None,
            doc_type_used=resolved_doc_type,
            cot_enabled=use_cot,
            hints_injected=False,
        )

    raise ValueError(f"Unknown condition: {condition}")


async def _run_extraction(
    file_path: str,
    schema_definition: dict | None,
    prompt: str,
    system_prompt: str | None,
    provider_name: str,
    model: str,
    extraction_method: str,
) -> Dict[str, Any]:
    from services.processors.factory import ProcessorFactory

    factory = ProcessorFactory()
    file_type = "document" if Path(file_path).suffix.lower() == ".pdf" else "image"
    processor = factory.get_processor(extraction_method, file_type)

    kwargs: dict = {"temperature": 0.1, "max_tokens": 8192}
    if system_prompt:
        kwargs["system_prompt"] = system_prompt

    start = time.time()
    result = await processor.process(
        job_id=None,
        file_path=file_path,
        file_type=file_type,
        provider_name=provider_name,
        model=model,
        schema_definition=schema_definition,
        prompt=prompt,
        **kwargs,
    )
    elapsed = round(time.time() - start, 3)

    return {
        "success": result.get("success", False),
        "data": result.get("data"),
        "error": result.get("error"),
        "elapsed_seconds": elapsed,
        "raw_response": result.get("raw_response"),
    }


async def run_ablation(
    file_path: str,
    schema_definition: dict,
    schema_name: str,
    provider_name: str,
    model: str,
    extraction_method: str,
    expected: dict | None = None,
) -> Dict[str, Any]:
    file_assessment = _assess_file(file_path)
    base_prompt = "Extract all information from this document"

    optimizer = PromptOptimizer()
    full_result = await optimizer.optimize_prompt(
        prompt=base_prompt,
        schema_definition=schema_definition,
        schema_name=schema_name,
        provider=provider_name,
        model=model,
        processing_method=extraction_method,
        quality_score=file_assessment["quality_score"],
        doc_type=file_assessment["doc_type"],
    )

    condition_results: Dict[str, Dict[str, Any]] = {}

    for condition in ABLATION_CONDITIONS:
        if condition == "full":
            pr = full_result
            schema_to_use = pr.enriched_schema or schema_definition
        else:
            pr = _build_ablation_prompt(
                condition, base_prompt, schema_definition, schema_name,
                file_assessment.get("doc_type"), file_assessment.get("quality_score"),
            )
            schema_to_use = pr.enriched_schema if pr.enriched_schema else schema_definition

        sys_prompt = pr.system_prompt if pr.system_prompt else None
        ext = await _run_extraction(
            file_path, schema_to_use, pr.user_prompt, sys_prompt,
            provider_name, model, extraction_method,
        )

        stats = _count_populated(ext.get("data"))
        accuracy = None
        if expected and ext.get("data"):
            scoring = score_results(expected, ext["data"])
            accuracy = scoring["overall_score"]

        condition_results[condition] = {
            "success": ext["success"],
            "elapsed_seconds": ext["elapsed_seconds"],
            "field_stats": stats,
            "accuracy": accuracy,
            "data": ext.get("data"),
            "error": ext.get("error"),
            "cot_enabled": pr.cot_enabled,
            "user_tokens": _count_tokens_approx(pr.user_prompt),
            "system_tokens": _count_tokens_approx(pr.system_prompt),
        }

    return {
        "config": {
            "file": file_path,
            "schema": schema_name,
            "provider": provider_name,
            "model": model,
            "method": extraction_method,
        },
        "file_assessment": file_assessment,
        "conditions": condition_results,
    }


async def persist_to_db(
    provider: str,
    model: str,
    extraction_method: str,
    reports: List[Dict[str, Any]],
    dataset_name: str,
) -> int:
    from database import crud

    run_id = await crud.create_benchmark_run(
        dataset=f"ablation_{dataset_name}",
        provider=provider,
        model=model,
        sample_count=len(reports),
        processing_method=extraction_method,
    )

    for i, report in enumerate(reports):
        conditions = report["conditions"]
        for cond_name, cond in conditions.items():
            await crud.add_benchmark_result(
                run_id=run_id,
                sample_index=i,
                file_path=report["config"]["file"],
                accuracy_score=cond.get("accuracy"),
                latency=cond["elapsed_seconds"],
                cost=None,
                prompt_tokens=cond["user_tokens"] + cond["system_tokens"],
                completion_tokens=None,
                expected_json=json.dumps(cond.get("data"))[:4000] if cond.get("data") else None,
                actual_json=None,
                field_scores=json.dumps({
                    "condition": cond_name,
                    "success": bool(cond["success"]),
                    "field_stats": cond["field_stats"],
                    "cot_enabled": bool(cond["cot_enabled"]),
                    "accuracy": float(cond["accuracy"]) if cond.get("accuracy") is not None else None,
                }, default=str),
                error_message=cond.get("error"),
            )

    accuracies = []
    latencies = []
    for report in reports:
        full_cond = report["conditions"].get("full", {})
        if full_cond.get("accuracy") is not None:
            accuracies.append(full_cond["accuracy"])
        latencies.append(full_cond["elapsed_seconds"])

    await crud.update_benchmark_run(
        run_id=run_id,
        overall_accuracy=sum(accuracies) / len(accuracies) if accuracies else None,
        avg_latency=sum(latencies) / len(latencies) if latencies else None,
        total_prompt_tokens=sum(
            c["user_tokens"] + c["system_tokens"]
            for r in reports
            for c in r["conditions"].values()
        ),
    )

    return run_id


def _print_ablation_report(report: Dict[str, Any]) -> None:
    cfg = report["config"]
    fa = report["file_assessment"]

    print(f"\n{'='*80}")
    print(f"  ABLATION REPORT")
    print(f"{'='*80}")
    print(f"  File:     {cfg['file']}")
    print(f"  Schema:   {cfg['schema']}")
    print(f"  Provider: {cfg['provider']} / {cfg['model']}")
    print(f"  Method:   {cfg['method']}")
    if fa.get("quality_score") is not None:
        print(f"  Quality:  {fa['quality_score']:.1f}/100")
    if fa.get("doc_type"):
        print(f"  Doc type: {fa['doc_type']}")
    print(f"{'─'*80}")
    print(f"  {'Condition':<18} {'Success':>8} {'Time':>8} {'Complete':>10} {'Accuracy':>10} {'Tokens':>8}")
    print(f"{'─'*80}")

    for cond in ABLATION_CONDITIONS:
        c = report["conditions"][cond]
        acc_str = f"{c['accuracy']:.1%}" if c.get("accuracy") is not None else "N/A"
        print(
            f"  {cond:<18} {str(c['success']):>8} {c['elapsed_seconds']:>7.2f}s "
            f"{c['field_stats']['completeness']:>9.1%} {acc_str:>10} "
            f"{c['user_tokens'] + c['system_tokens']:>8}"
        )

    print(f"{'='*80}\n")


def _print_summary_matrix(all_reports: List[Dict[str, Any]], providers: List[str]) -> None:
    print(f"\n{'='*90}")
    print(f"  ABLATION SUMMARY — ALL SAMPLES")
    print(f"{'='*90}")

    for provider in providers:
        provider_reports = [r for r in all_reports if r["config"]["provider"] == provider]
        if not provider_reports:
            continue

        print(f"\n  Provider: {provider}")
        print(f"  {'Condition':<18} {'Avg Acc':>10} {'Avg Time':>10} {'Avg Compl':>10} {'Success%':>10} {'Samples':>8}")
        print(f"  {'─'*76}")

        for cond in ABLATION_CONDITIONS:
            accs = [r["conditions"][cond].get("accuracy") for r in provider_reports if r["conditions"][cond].get("accuracy") is not None]
            times = [r["conditions"][cond]["elapsed_seconds"] for r in provider_reports]
            compls = [r["conditions"][cond]["field_stats"]["completeness"] for r in provider_reports]
            succs = sum(1 for r in provider_reports if r["conditions"][cond]["success"])

            avg_acc = f"{sum(accs)/len(accs):.1%}" if accs else "N/A"
            avg_time = f"{sum(times)/len(times):.2f}s"
            avg_compl = f"{sum(compls)/len(compls):.1%}"
            succ_pct = f"{succs/len(provider_reports):.0%}"

            print(f"  {cond:<18} {avg_acc:>10} {avg_time:>10} {avg_compl:>10} {succ_pct:>10} {len(provider_reports):>8}")

    print(f"{'='*90}\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Optimizer Ablation Benchmark")
    parser.add_argument("--file", default=None, help="Single file to benchmark")
    parser.add_argument("--schema", default="Generic", help="Schema name")
    parser.add_argument("--expected", default=None, help="Ground truth JSON or @file.json")
    parser.add_argument("--providers", nargs="+", default=["gemini"], help="Providers to test")
    parser.add_argument("--model", default=None, help="Model name (auto-detected per provider if omitted)")
    parser.add_argument("--method", default="docling-parse", help="Extraction method")
    parser.add_argument("--dataset", default=None, help="Dataset: 'cord' or 'invoices'")
    parser.add_argument("--max-samples", type=int, default=5, help="Max samples from dataset")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    parser.add_argument("--no-db", action="store_true", help="Skip database persistence")
    args = parser.parse_args()

    from services.provider_utils import resolve_provider_api_key

    provider_models = {
        "gemini": "gemini-2.5-flash",
        "openrouter": "google/gemini-2.5-flash",
    }

    templates = SchemaService.get_builtin_templates()
    all_reports: List[Dict[str, Any]] = []

    samples: List[Dict[str, Any]] = []

    if args.dataset:
        if args.dataset == "cord":
            from benchmarks.datasets import load_cord_samples
            cord_samples = load_cord_samples(args.max_samples)
            for s in cord_samples:
                samples.append({
                    "file": s.image_path,
                    "schema": s.schema,
                    "schema_name": "Receipt",
                    "expected": s.expected,
                })
        else:
            print(f"Unknown dataset: {args.dataset}")
            return
    elif args.file:
        schema_def = templates.get(args.schema, templates["Generic"])
        expected = None
        if args.expected:
            p = Path(args.expected)
            if p.exists():
                expected = json.load(open(p))
            else:
                expected = json.loads(args.expected)
        samples.append({
            "file": args.file,
            "schema": schema_def,
            "schema_name": args.schema,
            "expected": expected,
        })
    else:
        print("ERROR: Provide --file or --dataset")
        return

    if not samples:
        print("ERROR: No samples to benchmark")
        return

    for provider in args.providers:
        model = args.model or provider_models.get(provider, "gemini-2.5-flash")
        api_key = resolve_provider_api_key(provider)
        if not api_key:
            print(f"WARNING: No API key for {provider}, skipping")
            continue

        for si, sample in enumerate(samples):
            print(f"\n--- {provider}/{model} Sample {si+1}/{len(samples)}: {Path(sample['file']).name} ---")

            report = await run_ablation(
                file_path=sample["file"],
                schema_definition=sample["schema"],
                schema_name=sample["schema_name"],
                provider_name=provider,
                model=model,
                extraction_method=args.method,
                expected=sample.get("expected"),
            )
            all_reports.append(report)
            _print_ablation_report(report)

    _print_summary_matrix(all_reports, args.providers)

    if not args.no_db:
        for provider in args.providers:
            provider_reports = [r for r in all_reports if r["config"]["provider"] == provider]
            if provider_reports:
                model = args.model or provider_models.get(provider, "gemini-2.5-flash")
                dataset_label = args.dataset or Path(samples[0]["file"]).stem
                run_id = await persist_to_db(
                    provider, model, args.method, provider_reports, dataset_label,
                )
                print(f"Persisted {len(provider_reports)} results to benchmark_runs.id={run_id}")

    output_path = args.output or f"ablation_{args.dataset or 'single'}_{int(time.time())}.json"
    with open(output_path, "w") as f:
        json.dump(all_reports, f, indent=2, default=str)
    print(f"Full report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
