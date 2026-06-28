"""
Shared helper functions for benchmark modules.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict

from services.quality_gate import QualityGate
from services.image_service import ImageService
from services.document_classifier import DocumentClassifier

logger = logging.getLogger(__name__)


def count_tokens_approx(text: str) -> int:
    return len(text) // 4


def count_populated_fields(data: dict | None) -> Dict[str, Any]:
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
    stats["completeness"] = (
        round(stats["populated"] / stats["total"], 3) if stats["total"] > 0 else 0.0
    )
    return stats


def assess_file(file_path: str, file_type: str) -> Dict[str, Any]:
    quality_score = None
    doc_type = None

    if file_type == "image":
        try:
            img = ImageService.load_image(file_path)
            quality_score = QualityGate().assess(img).overall_score
        except Exception as exc:
            logger.warning("Quality assessment failed for %s: %s", file_path, exc)

    if file_path.lower().endswith(".pdf"):
        try:
            analysis = DocumentClassifier().analyze_document(file_path)
            if analysis.has_tables and analysis.complexity_score > 70:
                doc_type = "table_heavy"
            elif analysis.text_density < 50:
                doc_type = "handwritten"
        except Exception as exc:
            logger.warning("Document classification failed for %s: %s", file_path, exc)

    return {"quality_score": quality_score, "doc_type": doc_type}


async def run_single_extraction(
    file_path: str,
    schema_definition: dict | None,
    prompt: str,
    system_prompt: str | None,
    provider_name: str,
    model: str,
    extraction_method: str,
    temperature: float = 0.1,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    from services.processors.factory import ProcessorFactory

    factory = ProcessorFactory()
    file_type = "document" if Path(file_path).suffix.lower() == ".pdf" else "image"
    processor = factory.get_processor(extraction_method, file_type)

    kwargs: dict = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
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
