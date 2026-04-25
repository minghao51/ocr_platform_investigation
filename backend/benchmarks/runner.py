"""
Benchmark runner.
Executes benchmark runs against VLM providers and records results.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional
from PIL import Image
import psutil

from benchmarks.datasets import BenchmarkSample
from benchmarks import datasets_extended
from benchmarks.scoring import score_results, score_items_list
from services.pricing import calculate_cost
from database import crud


def load_dataset(*args, **kwargs):
    """Proxy dataset loading so tests can patch either runner or adapter module."""
    return datasets_extended.load_dataset(*args, **kwargs)


def _measure_memory():
    return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024


async def _process_vision_sample(
    idx: int,
    sample: BenchmarkSample,
    provider_name: str,
    model: str,
    api_key: str,
    prompt: str,
    semaphore: asyncio.Semaphore,
    processing_service: Any,
    **kwargs,
) -> Dict[str, Any]:
    mem_before = _measure_memory()
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
                    image,
                    prompt,
                    sample.schema,
                    model,
                    temperature=0.1,
                    max_tokens=4096,
                )

            latency = time.time() - sample_start
            usage = vlm_result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0) or usage.get(
                "promptTokenCount", 0
            )
            completion_tokens = usage.get("completion_tokens", 0) or usage.get(
                "candidatesTokenCount", 0
            )
            cost = calculate_cost(model, prompt_tokens, completion_tokens)

            if "error" in vlm_result:
                sample_result.update(
                    {
                        "accuracy_score": 0.0,
                        "latency": latency,
                        "cost": cost,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "error_message": f"Provider error: {vlm_result['error']}",
                    }
                )
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
                    scoring["overall_score"] = (
                        scoring["overall_score"] + items_score["score"]
                    ) / 2

                field_scores = scoring["field_scores"]
                mem_after = _measure_memory()
                field_scores["__meta"] = {
                    "peak_memory_mb": round(mem_after - mem_before, 2)
                }

                sample_result.update(
                    {
                        "accuracy_score": scoring["overall_score"],
                        "latency": latency,
                        "cost": cost,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "expected_json": json.dumps(sample.expected),
                        "actual_json": json.dumps(actual_data),
                        "field_scores": json.dumps(field_scores),
                    }
                )

        except Exception as e:
            latency = time.time() - sample_start
            sample_result.update(
                {
                    "accuracy_score": 0.0,
                    "latency": latency,
                    "cost": 0.0,
                    "error_message": f"{type(e).__name__}: {str(e)}",
                }
            )

        return sample_result


def _schema_to_nuextract_template(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON Schema to NuExtract-friendly template format.

    NuExtract echoes top-level JSON Schema keys (type, required, etc.).
    We extract just the properties and flatten them.
    """
    if "properties" in schema:
        template: Dict[str, Any] = {}
        for key, val in schema["properties"].items():
            if val.get("type") == "array" and "items" in val:
                item_props = val["items"].get("properties", {})
                inner = {k: v.get("type", "string") for k, v in item_props.items()}
                template[key] = [inner]
            else:
                desc = val.get("description", val.get("type", "string"))
                template[key] = desc
        return template
    return schema


def _unwrap_nuextract_output(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap NuExtract output if it nested data under schema keys.

    NuExtract may echo JSON Schema keys like 'type', 'required' and put
    actual data under 'type'. Detect and unwrap.
    """
    schema_echo_keys = {"type", "required", "properties", "additionalProperties"}
    if isinstance(extracted, dict) and "type" in extracted:
        candidate = extracted["type"]
        if isinstance(candidate, dict) and not schema_echo_keys.issuperset(
            candidate.keys()
        ):
            return candidate
    return extracted


async def _process_docling_extract_sample(
    idx: int,
    sample: BenchmarkSample,
    **kwargs,
) -> Dict[str, Any]:
    from docling.document_extractor import DocumentExtractor
    from docling.datamodel.base_models import InputFormat
    from pathlib import Path

    mem_before = _measure_memory()
    sample_start = time.time()
    sample_result: Dict[str, Any] = {
        "sample_index": idx,
        "file_path": sample.image_path,
    }

    try:
        file_ext = Path(sample.image_path).suffix.lower()
        if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            allowed_formats = [InputFormat.IMAGE]
        elif file_ext == ".pdf":
            allowed_formats = [InputFormat.PDF]
        else:
            allowed_formats = [InputFormat.IMAGE, InputFormat.PDF]

        extractor = DocumentExtractor(allowed_formats=allowed_formats)
        template = _schema_to_nuextract_template(sample.schema)

        def _extract():
            return extractor.extract(source=sample.image_path, template=template)

        result = await asyncio.to_thread(_extract)

        latency = time.time() - sample_start
        mem_after = _measure_memory()
        peak_memory_mb = round(mem_after - mem_before, 2)

        if result.pages and len(result.pages) > 0:
            page_data = result.pages[0]
            extracted = page_data.extracted_data

            if isinstance(extracted, str):
                try:
                    extracted = json.loads(extracted)
                except json.JSONDecodeError:
                    extracted = {}
            if isinstance(extracted, dict):
                extracted = _unwrap_nuextract_output(extracted)
            if not isinstance(extracted, dict):
                extracted = {"raw": str(extracted)}

            scoring = score_results(sample.expected, extracted)

            if "items" in sample.expected or "items" in extracted:
                items_score = score_items_list(
                    sample.expected.get("items", []),
                    extracted.get("items", []),
                )
                scoring["overall_score"] = (
                    scoring["overall_score"] + items_score["score"]
                ) / 2

            field_scores = scoring["field_scores"]
            field_scores["__meta"] = {"peak_memory_mb": peak_memory_mb}

            sample_result.update(
                {
                    "accuracy_score": scoring["overall_score"],
                    "latency": latency,
                    "cost": 0.0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "expected_json": json.dumps(sample.expected),
                    "actual_json": json.dumps(extracted),
                    "field_scores": json.dumps(field_scores),
                }
            )
        else:
            sample_result.update(
                {
                    "accuracy_score": 0.0,
                    "latency": latency,
                    "cost": 0.0,
                    "error_message": "No data extracted from document",
                }
            )

    except Exception as e:
        latency = time.time() - sample_start
        sample_result.update(
            {
                "accuracy_score": 0.0,
                "latency": latency,
                "cost": 0.0,
                "error_message": f"{type(e).__name__}: {str(e)}",
            }
        )

    return sample_result


async def _process_docling_parse_sample(
    idx: int,
    sample: BenchmarkSample,
    provider_name: str,
    model: str,
    api_key: str,
    prompt: str,
    semaphore: asyncio.Semaphore,
    processing_service: Any,
    **kwargs,
) -> Dict[str, Any]:
    mem_before = _measure_memory()
    async with semaphore:
        sample_start = time.time()
        sample_result: Dict[str, Any] = {
            "sample_index": idx,
            "file_path": sample.image_path,
        }

        try:
            markdown_content = processing_service.docling_service.parse_document(
                sample.image_path
            )

            provider = processing_service.get_provider(provider_name, api_key)

            async with provider as prov:
                vlm_result = await prov.process_text(
                    text=markdown_content,
                    prompt=prompt,
                    schema_definition=sample.schema,
                    model=model,
                    temperature=0.1,
                    max_tokens=4096,
                )

            latency = time.time() - sample_start
            mem_after = _measure_memory()
            peak_memory_mb = round(mem_after - mem_before, 2)

            usage = vlm_result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0) or usage.get(
                "promptTokenCount", 0
            )
            completion_tokens = usage.get("completion_tokens", 0) or usage.get(
                "candidatesTokenCount", 0
            )
            cost = calculate_cost(model, prompt_tokens, completion_tokens)

            if "error" in vlm_result:
                sample_result.update(
                    {
                        "accuracy_score": 0.0,
                        "latency": latency,
                        "cost": cost,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "error_message": f"Provider error: {vlm_result['error']}",
                    }
                )
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
                    scoring["overall_score"] = (
                        scoring["overall_score"] + items_score["score"]
                    ) / 2

                field_scores = scoring["field_scores"]
                field_scores["__meta"] = {"peak_memory_mb": peak_memory_mb}

                sample_result.update(
                    {
                        "accuracy_score": scoring["overall_score"],
                        "latency": latency,
                        "cost": cost,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "expected_json": json.dumps(sample.expected),
                        "actual_json": json.dumps(actual_data),
                        "field_scores": json.dumps(field_scores),
                    }
                )

        except Exception as e:
            latency = time.time() - sample_start
            sample_result.update(
                {
                    "accuracy_score": 0.0,
                    "latency": latency,
                    "cost": 0.0,
                    "error_message": f"{type(e).__name__}: {str(e)}",
                }
            )

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
    processing_method: str = "vision",
    structuring_provider: str = "gemini",
    structuring_model: str = "gemini-2.5-flash-lite",
    structuring_api_key: Optional[str] = None,
    split: str = "train",
) -> Dict[str, Any]:
    valid_methods = {"vision", "docling-extract", "docling-parse"}
    if processing_method not in valid_methods:
        raise ValueError(
            f"Invalid processing_method '{processing_method}'. Must be one of {valid_methods}"
        )

    try:
        samples = load_dataset(
            dataset_name=dataset,
            limit=limit,
            data_dir=data_dir,
            split=split,
        )
    except ValueError as e:
        raise ValueError(f"Failed to load dataset '{dataset}': {e}")

    if not samples:
        raise ValueError("No samples loaded. Check data_dir or dataset name.")

    from services.processing import ProcessingService

    processing_service = ProcessingService()

    if processing_method == "docling-extract":
        db_provider = "local"
        db_model = "docling-extract"
    elif processing_method == "docling-parse":
        effective_structuring_model = structuring_model
        db_provider = "hybrid"
        db_model = f"docling-parse+{effective_structuring_model}"
    else:
        db_provider = provider_name
        db_model = model

    run_id = await crud.create_benchmark_run(
        dataset=dataset,
        provider=db_provider,
        model=db_model,
        sample_count=len(samples),
        processing_method=processing_method,
    )

    results_summary: List[Dict[str, Any]] = []
    total_accuracy = 0.0
    total_latency = 0.0
    total_cost = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    success_count = 0

    if processing_method == "vision":
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [
            _process_vision_sample(
                idx,
                sample,
                provider_name,
                model,
                api_key,
                prompt,
                semaphore,
                processing_service,
            )
            for idx, sample in enumerate(samples)
        ]
        results = await asyncio.gather(*tasks)

    elif processing_method == "docling-extract":
        results = []
        for idx, sample in enumerate(samples):
            result = await _process_docling_extract_sample(
                idx,
                sample,
            )
            results.append(result)

    elif processing_method == "docling-parse":
        semaphore = asyncio.Semaphore(min(concurrency, 2))
        tasks = [
            _process_docling_parse_sample(
                idx,
                sample,
                structuring_provider if structuring_api_key else provider_name,
                structuring_model if structuring_api_key else model,
                structuring_api_key or api_key,
                prompt,
                semaphore,
                processing_service,
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
        print(
            f"  Sample {sample_result['sample_index'] + 1}/{len(samples)}: "
            f"accuracy={sample_result.get('accuracy_score', 0):.2f}, "
            f"latency={sample_result.get('latency', 0):.1f}s, "
            f"cost=${sample_result.get('cost', 0):.4f}"
        )

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
        "provider": db_provider,
        "model": db_model,
        "processing_method": processing_method,
        "sample_count": n,
        "overall_accuracy": round(avg_accuracy, 4),
        "avg_latency": round(avg_latency, 4),
        "total_cost": round(total_cost, 4),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "success_rate": (success_count / n) if n > 0 else 0,
    }
