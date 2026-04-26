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
from services.image_preprocessor import ImagePreprocessor
from services.hybrid_processing import HybridProcessingService
from services.docling_service import DoclingService
from services.chunking_service import MarkdownSplitter
from services.transcription_service import TranscriptionService
from services.provider_utils import resolve_provider_api_key
from services.processing_utils import update_job_status_with_broadcast
from services.processors.factory import ProcessorFactory
from config import get_settings
from database import crud

logger = logging.getLogger(__name__)


def _get_max_file_size() -> int:
    return get_settings().max_file_size


class ProcessingService:
    """Main processing pipeline with quality gate"""

    def __init__(self, quality_threshold: float = 40.0, auto_preprocess: bool = True, skip_quality: bool = False):
        self.providers = {
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
            "litellm": LiteLLMProvider,
        }
        self.image_service = ImageService()
        self.schema_service = SchemaService()
        self.quality_gate = QualityGate()
        self.preprocessor = ImagePreprocessor()
        self.hybrid_service = HybridProcessingService()
        self.docling_service = DoclingService()
        self.chunking_service = MarkdownSplitter()
        self.transcription_service = TranscriptionService()
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
        """Get provider instance"""
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
        """Process a file (image or PDF)"""
        extraction_method = kwargs.pop(
            "extraction_method", "docling-parse"
        )
        is_transcription = kwargs.pop("is_transcription", False)

        # Handle docling-extract (local VLM, no API key needed)
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

        # Handle docling-parse (Docling + VLM)
        if extraction_method == "docling-parse":
            processor = self._factory.get_processor(extraction_method, file_type)
            return await processor.process(
                None, file_path, file_type, provider_name, model,
                schema_definition, prompt, is_transcription=is_transcription,
                **kwargs,
            )

        # Get API key for other methods
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
    """
    Run vision extraction job (processes images/PDFs as images using VLMs).
    Best for: Scanned documents, images, PDFs with visual elements.

    Optional overrides preserve request-time settings when the job is queued in-memory.
    """
    start_time = time.time()

    try:
        # Get job details
        job = await crud.get_job(job_id)
        if not job:
            return

        # Update status to processing
        await update_job_status_with_broadcast(job_id, "processing")

    except Exception as e:
        processing_time = time.time() - start_time
        error_details = f"{type(e).__name__}: {str(e)}"
        logger.error("Job %s failed during startup: %s", job_id, error_details, exc_info=True)
        await update_job_status_with_broadcast(
            job_id,
            "error",
            error_message=error_details,
            processing_time=processing_time,
        )
        return
    # Determine file type from job record
    file_type = job["file_type"]

    # Get schema
    if raw_output:
        schema_definition = None
    elif schema_definition_override is not None:
        schema_definition = schema_definition_override
    elif job["schema_id"]:
        schema_record = await crud.get_schema(job["schema_id"])
        if schema_record:
            import json

            schema_definition = json.loads(schema_record["definition"])
        else:
            schema_definition = SchemaService.get_builtin_templates()["Generic"]
    else:
        schema_definition = SchemaService.get_builtin_templates()["Generic"]

    prompt = prompt_override or "Extract all information from this document"
    temperature = 0.1 if temperature_override is None else temperature_override
    max_tokens = 8192 if max_tokens_override is None else max_tokens_override

    # Process
    service = ProcessingService(
        quality_threshold=quality_threshold if quality_threshold is not None else 40.0,
        auto_preprocess=auto_preprocess if auto_preprocess is not None else True,
        skip_quality=skip_quality if skip_quality is not None else False,
    )
    start_time = time.time()

    try:
        result = await service.process_file(
            file_id=str(job_id),
            file_path=file_path,
            file_type=file_type,
            provider_name=job["provider"],
            model=job["model"],
            schema_definition=schema_definition,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            job_id=job_id,
            extraction_method=extraction_method_override
            or job.get("processing_method")
            or "vision",
            is_transcription=is_transcription,
        )

        logger.info("Processing completed for job %s Result: %s", job_id, result.get('success'))

        processing_time = time.time() - start_time

        if result["success"]:
            raw_response = result.get("raw_response", {})
            usage = (
                raw_response.get("usage") if isinstance(raw_response, dict) else None
            )
            if result.get("metadata"):
                await crud.update_job_metadata(job_id, result["metadata"])
            await update_job_status_with_broadcast(
                job_id,
                "success",
                result=result.get("data"),
                processing_time=processing_time,
                usage=usage,
            )
        else:
            raw_response = result.get("raw_response", {})
            usage = (
                raw_response.get("usage") if isinstance(raw_response, dict) else None
            )
            if result.get("metadata"):
                await crud.update_job_metadata(job_id, result["metadata"])
            await update_job_status_with_broadcast(
                job_id,
                "error",
                error_message=result.get("error"),
                processing_time=processing_time,
                usage=usage,
            )

    except Exception as e:
        processing_time = time.time() - start_time
        error_details = f"{type(e).__name__}: {str(e)}"
        logger.error("Job %s failed: %s", job_id, error_details, exc_info=True)
        await update_job_status_with_broadcast(
            job_id,
            "error",
            error_message=error_details,
            processing_time=processing_time,
        )


async def run_text_processing_job(
    job_id: int,
    file_path: str,
    schema_definition_override: Optional[Dict[str, Any]] = None,
    prompt_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    max_tokens_override: Optional[int] = None,
    raw_output: bool = False,
) -> None:
    """
    Run text extraction job (extracts text from PDFs using pdfplumber, then processes with LLM).
    Best for: Digital PDFs with extractable text (faster & more cost-effective).
    """

    from database import crud
    from services.schema_service import SchemaService

    # Get job details
    job = await crud.get_job(job_id)
    if not job:
        return

    # Update status to processing
    await update_job_status_with_broadcast(job_id, "processing")

    # Get schema
    if raw_output:
        schema_definition = None
    elif schema_definition_override is not None:
        schema_definition = schema_definition_override
    elif job["schema_id"]:
        schema_record = await crud.get_schema(job["schema_id"])
        if schema_record:
            schema_definition = json.loads(schema_record["definition"])
        else:
            schema_definition = SchemaService.get_builtin_templates()["Generic"]
    else:
        schema_definition = SchemaService.get_builtin_templates()["Generic"]

    prompt = prompt_override or "Extract all information from this document"
    temperature = 0.1 if temperature_override is None else temperature_override
    max_tokens = 8192 if max_tokens_override is None else max_tokens_override

    # Get API key
    provider_name = job["provider"]
    api_key = resolve_provider_api_key(provider_name)
    if not api_key:
        await update_job_status_with_broadcast(
            job_id, "error", error_message=f"No API key configured for {provider_name}"
        )
        return

    # Process
    start_time = time.time()

    try:
        logger.info("Starting TEXT processing for job %s", job_id)

        from services.processors.text import TextProcessor

        processor = TextProcessor()
        result = await processor.process(
            job_id=job_id,
            file_path=file_path,
            file_type="pdf",
            provider_name=provider_name,
            model=job["model"],
            schema_definition=schema_definition,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        processing_time = time.time() - start_time

        if result["success"]:
            raw_response = result.get("raw_response", {})
            usage = raw_response.get("usage") if isinstance(raw_response, dict) else None
            await update_job_status_with_broadcast(
                job_id,
                "success",
                result=result.get("data"),
                processing_time=processing_time,
                usage=usage,
            )
            logger.info("Processing completed for job %s", job_id)
        else:
            raw_response = result.get("raw_response", {})
            usage = raw_response.get("usage") if isinstance(raw_response, dict) else None
            await update_job_status_with_broadcast(
                job_id,
                "error",
                error_message=result.get("error"),
                processing_time=processing_time,
                usage=usage,
            )

    except Exception as e:
        processing_time = time.time() - start_time
        error_details = f"{type(e).__name__}: {str(e)}"
        logger.error("Text job %s failed: %s", job_id, error_details, exc_info=True)
        await update_job_status_with_broadcast(
            job_id,
            "error",
            error_message=error_details,
            processing_time=processing_time,
        )
