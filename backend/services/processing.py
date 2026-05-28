import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from services.image_service import ImageService
from services.schema_service import SchemaService
from services.quality_gate import QualityGate
from services.processing_utils import (
    update_job_status_with_broadcast,
    parse_and_validate_response as _parse_and_validate_response,
)
from services.processors.factory import ProcessorFactory
from services.prompt_optimizer import PromptOptimizer
from services.document_classifier import DocumentClassifier
from services.docling_service import DoclingService
from services.chunking_service import MarkdownSplitter
from services.transcription_service import TranscriptionService
from services.provider_utils import (
    resolve_provider_api_key as _resolve_provider_api_key,
)
from config import get_settings
from database import crud

logger = logging.getLogger(__name__)

# Backward-compatible exports used by legacy tests.
parse_and_validate_response = _parse_and_validate_response
resolve_provider_api_key = _resolve_provider_api_key

_document_classifier = DocumentClassifier()


class ProcessingOrchestrator:
    def __init__(
        self, quality_threshold=40.0, auto_preprocess=True, skip_quality=False
    ):
        self.docling_parse_timeout_seconds = max(
            1, int(get_settings().docling_parse_timeout_seconds)
        )
        self.quality_threshold = quality_threshold
        self.auto_preprocess = auto_preprocess
        self.skip_quality = skip_quality
        self.schema_service = SchemaService()
        self.docling_service = DoclingService()
        self.chunking_service = MarkdownSplitter()
        self.transcription_service = TranscriptionService()
        self._factory = ProcessorFactory(
            quality_threshold=quality_threshold,
            auto_preprocess=auto_preprocess,
            skip_quality=skip_quality,
            docling_parse_timeout_seconds=self.docling_parse_timeout_seconds,
        )

    def _should_chunk(self, text: str, model: str) -> bool:
        """Backward-compatible helper retained for legacy tests."""
        splitter = self.chunking_service
        threshold = int(splitter.default_max_tokens * 0.75)
        return splitter.count_tokens(text) > threshold

    def _validate_file_size(self, file_path: str) -> None:
        """Backward-compatible helper retained for legacy tests."""
        max_file_size = int(get_settings().max_file_size)
        file_size = Path(file_path).stat().st_size
        if file_size > max_file_size:
            raise ValueError(
                f"File size {file_size} exceeds maximum allowed size {max_file_size}"
            )

    async def run_job(
        self,
        job: dict,
        file_path: str,
        file_type: str,
        extraction_method: str,
        schema_definition,
        prompt: str,
        system_prompt=None,
        temperature=0.1,
        max_tokens=8192,
        is_transcription=False,
        **kwargs,
    ) -> Dict[str, Any]:
        processor = self._factory.get_processor(extraction_method, file_type)
        return await processor.process(
            job["id"] if job else None,
            file_path,
            file_type,
            job["provider"],
            job["model"],
            schema_definition,
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            is_transcription=is_transcription,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def resolve_schema(
        self, job, schema_definition_override=None, raw_output=False
    ):
        if raw_output:
            return None
        if schema_definition_override is not None:
            return schema_definition_override
        if job.get("schema_id"):
            schema_record = await crud.get_schema(job["schema_id"])
            if schema_record:
                return json.loads(schema_record["definition"])
        return SchemaService.get_builtin_templates()["Generic"]


ProcessingService = ProcessingOrchestrator


async def _resolve_schema(
    job: dict,
    schema_definition_override: Optional[Dict] = None,
    raw_output: bool = False,
) -> Optional[Dict]:
    if raw_output:
        return None
    if schema_definition_override is not None:
        return schema_definition_override
    if job.get("schema_id"):
        schema_record = await crud.get_schema(job["schema_id"])
        if schema_record:
            return json.loads(schema_record["definition"])
    return SchemaService.get_builtin_templates()["Generic"]


async def _register_result(
    job_id: int, result: dict, start_time: float, metadata_from_result: bool = True
) -> None:
    processing_time = time.time() - start_time
    raw_response = result.get("raw_response")
    if raw_response is not None:
        usage = raw_response.usage.model_dump() if raw_response.usage else None
    else:
        usage = None
    if metadata_from_result and result.get("metadata"):
        await crud.update_job_metadata(job_id, result["metadata"])

    if result["success"]:
        await update_job_status_with_broadcast(
            job_id,
            "success",
            result=result.get("data"),
            processing_time=processing_time,
            usage=usage,
        )
    else:
        await update_job_status_with_broadcast(
            job_id,
            "error",
            error_message=result.get("error"),
            processing_time=processing_time,
            usage=usage,
        )


async def _handle_processing_error(
    job_id: int, error: Exception, start_time: float
) -> None:
    processing_time = time.time() - start_time
    error_details = f"{type(error).__name__}: {str(error)}"
    logger.error("Job %s failed: %s", job_id, error_details, exc_info=True)
    await update_job_status_with_broadcast(
        job_id,
        "error",
        error_message=error_details,
        processing_time=processing_time,
    )


async def run_processing_job(
    job_id: int,
    file_path: str,
    schema_definition_override: Optional[Dict[str, Any]] = None,
    prompt_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    max_tokens_override: Optional[int] = None,
    quality_threshold: Optional[float] = None,
    auto_preprocess: Optional[bool] = None,
    skip_quality: Optional[bool] = None,
    raw_output: bool = False,
    extraction_method_override: Optional[str] = None,
    is_transcription: bool = False,
) -> None:
    init_time = time.time()

    try:
        job = await crud.get_job(job_id)
        if not job:
            return
        await update_job_status_with_broadcast(job_id, "processing")
    except Exception as e:
        await _handle_processing_error(job_id, e, init_time)
        return

    file_type = job["file_type"]
    schema_definition = await _resolve_schema(
        job, schema_definition_override, raw_output
    )

    prompt = prompt_override or "Extract all information from this document"
    temperature = 0.1 if temperature_override is None else temperature_override
    max_tokens = 8192 if max_tokens_override is None else max_tokens_override
    extraction_method = (
        extraction_method_override or job.get("processing_method") or "vision"
    )

    quality_score = None
    quality_assessment_failed = False
    if file_type == "image" and extraction_method in ("vision", "hybrid"):
        try:
            img = ImageService.load_image(file_path)
            quality_score = QualityGate().assess(img).overall_score
        except Exception as exc:
            quality_assessment_failed = True
            logger.warning("Quality assessment failed for job %s: %s", job_id, exc)

    doc_type_override = None
    document_classification_failed = False
    if file_path.lower().endswith(".pdf"):
        try:
            analysis = await asyncio.to_thread(
                _document_classifier.analyze_document, file_path
            )
            if analysis.has_tables and analysis.complexity_score > 70:
                doc_type_override = "table_heavy"
            elif analysis.text_density < 50:
                doc_type_override = "handwritten"
        except Exception as exc:
            document_classification_failed = True
            logger.warning("Document classification failed for job %s: %s", job_id, exc)

    optimizer = PromptOptimizer()
    prompt_result = await optimizer.optimize_prompt(
        prompt=prompt,
        schema_definition=schema_definition,
        schema_name=job.get("schema_name"),
        provider=job["provider"],
        model=job["model"],
        processing_method=extraction_method,
        is_raw_output=raw_output,
        is_transcription=is_transcription,
        quality_score=quality_score,
        doc_type=doc_type_override,
    )

    optimized_prompt = prompt_result.user_prompt
    optimized_schema = (
        prompt_result.enriched_schema
        if prompt_result.enriched_schema
        else schema_definition
    )
    system_prompt = prompt_result.system_prompt

    try:
        await crud.update_job_metadata(
            job_id,
            {
                "prompt_optimization": {
                    "doc_type": prompt_result.doc_type_used,
                    "cot_enabled": prompt_result.cot_enabled,
                    "hints_injected": prompt_result.hints_injected,
                    "quality_score": quality_score,
                    "quality_assessment_failed": quality_assessment_failed,
                    "document_classification_failed": document_classification_failed,
                },
            },
        )
    except Exception as exc:
        logger.warning(
            "Failed to persist prompt optimization metadata for job %s: %s", job_id, exc
        )

    start_time = time.time()

    try:
        result = await _process_document(
            job,
            file_path,
            file_type,
            extraction_method,
            optimized_schema,
            optimized_prompt,
            system_prompt,
            temperature,
            max_tokens,
            is_transcription,
            quality_threshold,
            auto_preprocess,
            skip_quality,
        )
        await _register_result(job_id, result, start_time)
    except Exception as e:
        await _handle_processing_error(job_id, e, start_time)


async def _process_document(
    job: dict,
    file_path: str,
    file_type: str,
    extraction_method: str,
    schema_definition: Optional[Dict],
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: int,
    is_transcription: bool,
    quality_threshold: Optional[float],
    auto_preprocess: Optional[bool],
    skip_quality: Optional[bool],
) -> Dict[str, Any]:
    orchestrator = ProcessingOrchestrator(
        quality_threshold=quality_threshold if quality_threshold is not None else 40.0,
        auto_preprocess=auto_preprocess if auto_preprocess is not None else True,
        skip_quality=skip_quality if skip_quality is not None else False,
    )

    return await orchestrator.run_job(
        job=job,
        file_path=file_path,
        file_type=file_type,
        extraction_method=extraction_method,
        schema_definition=schema_definition,
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        is_transcription=is_transcription,
    )


async def run_text_processing_job(
    job_id: int,
    file_path: str,
    **kwargs: Any,
) -> None:
    await run_processing_job(
        job_id=job_id,
        file_path=file_path,
        extraction_method_override="text",
        **kwargs,
    )
