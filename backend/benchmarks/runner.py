"""
Benchmark runner.
Executes benchmark runs against VLM providers and records results.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from PIL import Image

from benchmarks.datasets import BenchmarkSample
from benchmarks import datasets_extended
from benchmarks.scoring import score_results, score_items_list
from services.pricing import calculate_cost
from database import crud


def load_dataset(*args, **kwargs):
    """Proxy dataset loading so tests can patch either runner or adapter module."""
    return datasets_extended.load_dataset(*args, **kwargs)


async def _process_single_sample(
    idx: int,
    sample: BenchmarkSample,
    provider_name: str,
    model: str,
    api_key: str,
    prompt: str,
    semaphore: asyncio.Semaphore,
    processing_service: Any,
) -> Dict[str, Any]:
    """Process a single benchmark sample. Must be called within a semaphore context."""
    async with semaphore:
        sample_start = time.time()
        sample_result: Dict[str, Any] = {
            "sample_index": idx,
            "file_path": sample.image_path,
        }

        try:
            image = Image.open(sample.image_path)
            if image.mode == "RGBA":
                image = image.convert("RGB")

            provider = processing_service.get_provider(provider_name, api_key)
            target_size = provider.get_default_image_size()
            image = processing_service.image_service.resize_image(image, target_size)

            async with provider as prov:
                vlm_result = await prov.process_image(
                    image, prompt, sample.schema, model, temperature=0.1, max_tokens=4096
                )

            latency = time.time() - sample_start
            usage = vlm_result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0) or usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("completion_tokens", 0) or usage.get("candidatesTokenCount", 0)
            cost = calculate_cost(model, prompt_tokens, completion_tokens)

            if "error" in vlm_result:
                sample_result.update({
                    "accuracy_score": 0.0,
                    "latency": latency,
                    "cost": cost,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "error_message": f"Provider error: {vlm_result['error']}",
                })
            else:
                content = vlm_result.get("content", "{}")
                try:
                    actual_data = json.loads(content)
                    if isinstance(actual_data, str):
                        actual_data = json.loads(actual_data)
                except json.JSONDecodeError:
                    actual_data = {}

                scoring = score_results(sample.expected, actual_data)

                if "items" in sample.expected or "items" in actual_data:
                    items_score = score_items_list(
                        sample.expected.get("items", []),
                        actual_data.get("items", []),
                    )
                    scoring["overall_score"] = (scoring["overall_score"] + items_score["score"]) / 2

                sample_result.update({
                    "accuracy_score": scoring["overall_score"],
                    "latency": latency,
                    "cost": cost,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "expected_json": json.dumps(sample.expected),
                    "actual_json": json.dumps(actual_data),
                    "field_scores": json.dumps(scoring["field_scores"]),
                })

        except Exception as e:
            latency = time.time() - sample_start
            sample_result.update({
                "accuracy_score": 0.0,
                "latency": latency,
                "cost": 0.0,
                "error_message": f"{type(e).__name__}: {str(e)}",
            })

        return sample_result


async def run_benchmark(
    provider_name: str,
    model: str,
    api_key: str,
    dataset: str = "cord",
    limit: int = 20,
    data_dir: Optional[str] = None,
    prompt: str = "Extract all information from this receipt as JSON.",
    concurrency: int = 5,
) -> Dict[str, Any]:
    """
    Run a benchmark against a provider/model combination.

    Args:
        provider_name: Name of the VLM provider
        model: Model identifier
        api_key: API key for the provider
        dataset: Dataset name ("cord", "funds", "synthetic_invoice")
        limit: Max samples to process
        data_dir: Path to dataset directory (for file-based datasets)
        prompt: Prompt to use for extraction
        concurrency: Max concurrent API calls

    Returns:
        Summary dict with run_id, metrics, and per-sample results.
    """
    # Use the unified dataset loader
    try:
        samples = load_dataset(
            dataset_name=dataset,
            limit=limit,
            data_dir=data_dir,
            split="train",
        )
    except ValueError as e:
        raise ValueError(f"Failed to load dataset '{dataset}': {e}")

    if not samples:
        raise ValueError("No samples loaded. Check data_dir or dataset name.")

    from services.processing import ProcessingService

    processing_service = ProcessingService()

    run_id = await crud.create_benchmark_run(
        dataset=dataset,
        provider=provider_name,
        model=model,
        sample_count=len(samples),
    )

    results_summary: List[Dict[str, Any]] = []
    total_accuracy = 0.0
    total_latency = 0.0
    total_cost = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    success_count = 0

    semaphore = asyncio.Semaphore(concurrency)

    tasks = [
        _process_single_sample(
            idx, sample, provider_name, model, api_key, prompt, semaphore, processing_service
        )
        for idx, sample in enumerate(samples)
    ]

    results = await asyncio.gather(*tasks)

    for sample_result in results:
        if not sample_result.get("error_message"):
            success_count += 1

        total_accuracy += sample_result["accuracy_score"]
        total_latency += sample_result["latency"]
        total_cost += sample_result["cost"]
        total_prompt_tokens += sample_result.get("prompt_tokens", 0)
        total_completion_tokens += sample_result.get("completion_tokens", 0)

        await crud.add_benchmark_result(run_id, **sample_result)
        results_summary.append(sample_result)
        print(f"  Sample {sample_result['sample_index'] + 1}/{len(samples)}: "
              f"accuracy={sample_result.get('accuracy_score', 0):.2f}, "
              f"latency={sample_result.get('latency', 0):.1f}s, "
              f"cost=${sample_result.get('cost', 0):.4f}")

    n = len(samples)
    avg_accuracy = total_accuracy / n if n > 0 else 0
    avg_latency = total_latency / n if n > 0 else 0
    if n > 0:
        avg_latency = max(avg_latency, 0.001)

    await crud.update_benchmark_run(
        run_id,
        overall_accuracy=round(avg_accuracy, 4),
        avg_latency=round(avg_latency, 2),
        total_cost=round(total_cost, 4),
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
    )

    return {
        "run_id": run_id,
        "dataset": dataset,
        "provider": provider_name,
        "model": model,
        "sample_count": n,
        "overall_accuracy": round(avg_accuracy, 4),
        "avg_latency": round(avg_latency, 4),
        "total_cost": round(total_cost, 4),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "success_rate": (success_count / n) if n > 0 else 0,
    }
