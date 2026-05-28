from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
import os
from models.schemas import ProcessRequest, ProcessResponse, EXTRACTION_METHODS
from database import crud
from services.document_classifier import DocumentClassifier
from services.job_queue import enqueue_processing_task
from dependencies import (
    check_and_increment_daily_limit,
    get_optional_user,
)
from limiter import limiter, get_rate_limit_value
from routers.job_serialization import serialize_job
from routers.shared import ensure_file_access, ensure_job_access
from services.provider_utils import has_provider_api_key
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/process", tags=["processing"])

LOCAL_PROVIDER = "docling-local"


def _requires_provider_model(processing_method: str) -> bool:
    return processing_method != "docling-extract"


def _supports_raw_output(processing_method: str) -> bool:
    return processing_method == "docling-parse"


def _should_execute_inline_for_tests(
    processing_method: str, provider: str | None
) -> bool:
    if not os.getenv("PYTEST_CURRENT_TEST"):
        return False
    if not _requires_provider_model(processing_method):
        return True
    return bool(provider) and has_provider_api_key(provider)


@router.post("/", response_model=ProcessResponse)
@limiter.limit(get_rate_limit_value)
async def process_document(
    request: Request,
    payload: ProcessRequest,
    extraction_method: Optional[
        str
    ] = None,  # NEW: "auto", "text", "vision", or None (auto)
    current_user: dict | None = Depends(get_optional_user),
):
    """
    Process a document with intelligent routing

    extraction_method options:
    - None or "auto": Automatically detect best pipeline (recommended)
    - "text": Force text extraction (pdfplumber + LLM) - fast & cheap
    - "vision": Force vision extraction (VLM) - accurate & expensive
    - "hybrid": Combined text + vision approach
    - "docling-parse": PyMuPDF text parsing (PDF) / Docling parsing (DOCX/PPTX) → LLM structures it
      * Fast local parsing + provider-backed structuring
      * Use for: Cost-sensitive structured extraction with provider/model control
    - "docling-extract": Docling DocumentExtractor (local VLM) → Structured JSON
      * Direct schema extraction, no cloud API needed
      * Best accuracy (86%), free, private
      * Use for: Accuracy-critical, privacy-sensitive, high-volume
    - "transcription": Force audio transcription mode (schema optional)
    """
    if current_user is not None:
        current_user = await check_and_increment_daily_limit(current_user)

    # Get file metadata from database
    file_record = await crud.get_uploaded_file(payload.file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    guest_token = request.headers.get("X-Guest-Token")
    ensure_file_access(file_record, current_user, guest_token)

    # Verify file still exists on disk
    from pathlib import Path

    file_path = Path(file_record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File has been deleted or moved")

    # Determine file type
    file_extension = (file_record["file_extension"] or "").lower()
    if file_extension in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        file_type = "image"
    elif file_extension == ".pdf":
        file_type = "pdf"
    elif file_extension in {".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
        file_type = "audio"
    else:
        file_type = "document"

    effective_extraction_method = extraction_method or payload.extraction_method

    # NEW: Intelligent routing logic
    processing_method = effective_extraction_method
    classification_info = None
    document_type = None
    is_transcription = effective_extraction_method == "transcription"

    # Auto-detect if not specified or set to "auto"
    if not effective_extraction_method or effective_extraction_method == "auto":
        if file_type == "pdf":
            # Use DocumentClassifier for PDFs
            try:
                classifier = DocumentClassifier()
                analysis = classifier.analyze_document(str(file_path))

                processing_method = analysis.recommended_pipeline
                classification_info = {
                    "type": analysis.type,
                    "complexity_score": analysis.complexity_score,
                    "confidence": analysis.confidence,
                    "reasoning": analysis.reasoning,
                }
                document_type = analysis.type

                logger.info(
                    f"Auto-detected pipeline: {processing_method} for {file_record['original_filename']}"
                )
                logger.info(
                    f"  Classification: {analysis.type} (confidence: {analysis.confidence:.2f})"
                )
                logger.info(f"  Reasoning: {analysis.reasoning}")

            except Exception as e:
                logger.warning(
                    f"Classification failed, falling back to vision: {str(e)}"
                )
                processing_method = "vision"
        elif file_type == "image":
            processing_method = "vision"
            classification_info = {"reasoning": "Image file, using vision processing"}
            document_type = "image"
        elif file_type == "audio":
            processing_method = "transcription"
            classification_info = {"reasoning": "Audio file, using transcription"}
            document_type = "audio"
        else:
            processing_method = "docling-parse"
            classification_info = {
                "reasoning": "Document format detected, using docling-parse",
            }
            document_type = file_extension.lstrip(".") or "document"

    # Validate extraction method
    if processing_method not in EXTRACTION_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extraction_method: {processing_method}. Must be 'text', 'vision', 'hybrid', 'docling-parse', 'docling-extract', or 'transcription'",
        )

    # For images, force vision processing
    if file_type == "image" and processing_method not in {"vision", "docling-extract"}:
        logger.info("Overriding extraction_method to 'docling-extract' for image file")
        processing_method = "docling-extract"

    # For audio, force transcription
    if file_type == "audio" and processing_method != "transcription":
        logger.info("Overriding extraction_method to 'transcription' for audio file")
        processing_method = "transcription"

    if file_type == "document" and processing_method in {"text", "vision", "hybrid"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "This document type supports 'docling-parse' or 'transcription'. "
                "Use a PDF if you want text, vision, or hybrid processing."
            ),
        )
    if file_type == "document" and processing_method == "docling-extract":
        raise HTTPException(
            status_code=400,
            detail="docling-extract currently supports PDFs and images only.",
        )

    schema_mode = payload.schema_mode or "auto-detect"
    if schema_mode == "raw" and not _supports_raw_output(processing_method):
        raise HTTPException(
            status_code=400,
            detail=(
                "Raw output is currently supported with the 'docling-parse' "
                "method. Choose 'PyMuPDF + LLM' to get raw Markdown output."
            ),
        )

    requires_provider_model = _requires_provider_model(processing_method)
    if requires_provider_model and (not payload.provider or not payload.model):
        raise HTTPException(
            status_code=400,
            detail=(
                "This extraction method requires a provider and model. "
                "Choose a provider-backed method configuration before processing."
            ),
        )

    is_transcription = processing_method == "transcription"

    if payload.schema_id:
        schema_record = await crud.get_schema(payload.schema_id)
        if not schema_record:
            raise HTTPException(status_code=404, detail="Schema not found")

        _schema_definition = json.loads(schema_record["definition"])
        schema_name = schema_record["name"]
    elif payload.schema_definition:
        _schema_definition = payload.schema_definition
        schema_name = "Custom"
    elif is_transcription:
        _schema_definition = None
        schema_name = "Transcription"
    elif schema_mode == "raw":
        _schema_definition = None
        schema_name = "Raw"
    else:
        raise HTTPException(
            status_code=400,
            detail="Either schema_id or schema_definition must be provided, or use schema_mode='raw' for raw output",
        )

    # Create job
    user_id = current_user.get("user_id") if current_user else None
    job_guest_token = guest_token if user_id is None else None
    job_provider = payload.provider if requires_provider_model else LOCAL_PROVIDER
    job_model = payload.model if requires_provider_model else processing_method
    job_id = await crud.create_job(
        file_name=file_record["original_filename"],
        file_type=file_type,
        provider=job_provider,
        model=job_model,
        schema_id=payload.schema_id,
        schema_name=schema_name,
        processing_method=processing_method,
        document_type=document_type,
        user_id=user_id,
        guest_token=job_guest_token,
    )

    # Store classification info in job metadata (optional, for debugging)
    if classification_info:
        try:
            await crud.update_job_metadata(job_id, classification_info)
        except Exception as exc:
            logger.warning(
                "Failed to store classification metadata for job %s: %s",
                job_id,
                exc,
            )

    # Queue background processing with appropriate method
    if processing_method == "text":
        worker_kwargs = {
            "schema_definition_override": _schema_definition,
            "prompt_override": payload.prompt,
            "temperature_override": payload.temperature,
            "max_tokens_override": payload.max_tokens,
            "raw_output": schema_mode == "raw",
        }
        await enqueue_processing_task(
            job_id,
            str(file_path),
            worker_kwargs,
            task_type="text",
        )
        if _should_execute_inline_for_tests(processing_method, payload.provider):
            from services.processing import run_text_processing_job

            await run_text_processing_job(job_id, str(file_path), **worker_kwargs)
    else:  # "vision", "hybrid", "docling", or "transcription"
        worker_kwargs = {
            "schema_definition_override": _schema_definition,
            "prompt_override": payload.prompt,
            "temperature_override": payload.temperature,
            "max_tokens_override": payload.max_tokens,
            "quality_threshold": payload.quality_threshold,
            "auto_preprocess": payload.auto_preprocess,
            "skip_quality": payload.skip_quality,
            "raw_output": schema_mode == "raw",
            "extraction_method_override": processing_method,
            "is_transcription": is_transcription,
        }
        await enqueue_processing_task(
            job_id,
            str(file_path),
            worker_kwargs,
            task_type="processing",
        )
        if _should_execute_inline_for_tests(processing_method, payload.provider):
            from services.processing import run_processing_job

            await run_processing_job(job_id, str(file_path), **worker_kwargs)

    response_payload = {"job_id": job_id, "status": "pending"}
    if job_guest_token:
        response_payload["guest_token"] = job_guest_token
    return ProcessResponse(**response_payload)


@router.get("/status/{job_id}")
async def get_job_status(
    job_id: int,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
):
    """Get processing job status"""

    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user, request.headers.get("X-Guest-Token"))

    return serialize_job(job)
