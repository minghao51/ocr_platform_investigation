import time
import json
import logging
from typing import Dict, Any, Optional
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.litellm_provider import LiteLLMProvider
from services.image_service import ImageService
from services.schema_service import SchemaService
from services.quality_gate import QualityGate
from services.processing_utils import update_job_status_with_broadcast
from services.processors.factory import ProcessorFactory
from services.prompt_optimizer import PromptOptimizer
from services.document_classifier import DocumentClassifier
from config import get_settings
from database import crud

logger = logging.getLogger(__name__)


class ProcessingService:
    """Main processing pipeline with quality gate"""

    def __init__(self, quality_threshold: float = 40.0, auto_preprocess: bool = True, skip_quality: bool = False):
        self.providers = {
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
            "litellm": LiteLLMProvider,
        }
        self.docling_parse_timeout_seconds = max(
            1, int(get_settings().docling_parse_timeout_seconds)
        )
        self.quality_threshold = quality_threshold
        self.auto_preprocess = auto_preprocess
        self.skip_quality = skip_quality

        self._factory = ProcessorFactory(
            quality_threshold=quality_threshold,
            auto_preprocess=auto_preprocess,
            skip_quality=skip_quality,
            docling_parse_timeout_seconds=self.docling_parse_timeout_seconds,
        )

    def get_provider(self, provider_name: str, api_key: str):
        provider_class = self.providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class(api_key)

    async def process_file(
        self,
        file_id: str,
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition: Optional[Dict[str, Any]],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        extraction_method = kwargs.pop("extraction_method", "docling-parse")
        is_transcription = kwargs.pop("is_transcription", False)

        if extraction_method == "docling-extract":
            if schema_definition is None:
                return {
                    "success": False,
                    "error": "Raw output is not supported for docling-extract.",
                }
            processor = self._factory.get_processor(extraction_method, file_type)
            return await processor.process(
                None, file_path, file_type, provider_name, model,
                schema_definition, prompt, **kwargs,
            )

        if extraction_method == "docling-parse":
            processor = self._factory.get_processor(extraction_method, file_type)
            return await processor.process(
                None, file_path, file_type, provider_name, model,
                schema_definition, prompt, is_transcription=is_transcription,
                **kwargs,
            )

        if schema_definition is None:
            return {
                "success": False,
                "error": "Raw output is only supported for docling-parse.",
            }

        processor = self._factory.get_processor(extraction_method, file_type)
        return await processor.process(
            None, file_path, file_type, provider_name, model,
            schema_definition, prompt, **kwargs,
        )


async def _resolve_schema(job: dict, schema_definition_override: Optional[Dict] = None, raw_output: bool = False) -> Optional[Dict]:
    if raw_output:
        return None
    if schema_definition_override is not None:
        return schema_definition_override
    if job.get("schema_id"):
        schema_record = await crud.get_schema(job["schema_id"])
        if schema_record:
            return json.loads(schema_record["definition"])
    return SchemaService.get_builtin_templates()["Generic"]


async def _register_result(job_id: int, result: dict, start_time: float, metadata_from_result: bool = True) -> None:
    processing_time = time.time() - start_time
    raw_response = result.get("raw_response", {})
    usage = raw_response.get("usage") if isinstance(raw_response, dict) else None
    if metadata_from_result and result.get("metadata"):
        await crud.update_job_metadata(job_id, result["metadata"])

    if result["success"]:
        await update_job_status_with_broadcast(
            job_id, "success",
            result=result.get("data"),
            processing_time=processing_time,
            usage=usage,
        )
    else:
        await update_job_status_with_broadcast(
            job_id, "error",
            error_message=result.get("error"),
            processing_time=processing_time,
            usage=usage,
        )


async def _handle_processing_error(job_id: int, error: Exception, start_time: float) -> None:
    processing_time = time.time() - start_time
    error_details = f"{type(error).__name__}: {str(error)}"
    logger.error("Job %s failed: %s", job_id, error_details, exc_info=True)
    await update_job_status_with_broadcast(
        job_id, "error",
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
    schema_definition = await _resolve_schema(job, schema_definition_override, raw_output)

    prompt = prompt_override or "Extract all information from this document"
    temperature = 0.1 if temperature_override is None else temperature_override
    max_tokens = 8192 if max_tokens_override is None else max_tokens_override
    extraction_method = extraction_method_override or job.get("processing_method") or "vision"

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
            classifier = DocumentClassifier()
            analysis = classifier.analyze_document(file_path)
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
    optimized_schema = prompt_result.enriched_schema if prompt_result.enriched_schema else schema_definition
    system_prompt = prompt_result.system_prompt

    await crud.update_job_metadata(job_id, {
        "prompt_optimization": {
            "doc_type": prompt_result.doc_type_used,
            "cot_enabled": prompt_result.cot_enabled,
            "hints_injected": prompt_result.hints_injected,
            "quality_score": quality_score,
            "quality_assessment_failed": quality_assessment_failed,
            "document_classification_failed": document_classification_failed,
        },
    })

    start_time = time.time()

    try:
        result = await _process_document(
            job, file_path, file_type, extraction_method,
            optimized_schema, optimized_prompt, system_prompt,
            temperature, max_tokens, is_transcription,
            quality_threshold, auto_preprocess, skip_quality,
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
    service = ProcessingService(
        quality_threshold=quality_threshold if quality_threshold is not None else 40.0,
        auto_preprocess=auto_preprocess if auto_preprocess is not None else True,
        skip_quality=skip_quality if skip_quality is not None else False,
    )

    return await service.process_file(
        file_id=str(job["id"]),
        file_path=file_path,
        file_type=file_type,
        provider_name=job["provider"],
        model=job["model"],
        schema_definition=schema_definition,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        job_id=job["id"],
        extraction_method=extraction_method,
        is_transcription=is_transcription,
        system_prompt=system_prompt,
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
