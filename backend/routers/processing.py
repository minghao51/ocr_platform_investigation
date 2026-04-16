from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from typing import Optional
from models.schemas import ProcessRequest, ProcessResponse
from database import crud
from services.processing import run_processing_job, run_text_processing_job
from services.document_classifier import DocumentClassifier
from dependencies import (
    check_and_increment_daily_limit,
    get_optional_user,
)
from limiter import limiter, get_rate_limit_value
from routers.job_serialization import serialize_job
from routers.shared import ensure_file_access, ensure_job_access
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/process", tags=["processing"])


@router.post("/", response_model=ProcessResponse)
@limiter.limit(get_rate_limit_value)
async def process_document(
    request: Request,
    payload: ProcessRequest,
    background_tasks: BackgroundTasks,
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
    - "docling": Force Docling-based extraction with markdown parsing
    - "transcription": Force audio transcription mode (schema optional)
    """
    if current_user is not None:
        current_user = await check_and_increment_daily_limit(current_user)

    # Get schema definition (optional for transcription mode)
    is_transcription = extraction_method == "transcription" or payload.extraction_method == "transcription"

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
        # Schema is optional for transcription mode
        _schema_definition = None
        schema_name = "Transcription"
    else:
        raise HTTPException(
            status_code=400,
            detail="Either schema_id or schema_definition must be provided",
        )

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
    file_type = "pdf" if file_record["file_extension"] == ".pdf" else "image"

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
        else:
            # Images always use vision processing
            processing_method = "vision"
            classification_info = {"reasoning": "Image file, using vision processing"}
            document_type = "image"

    # Validate extraction method
    if processing_method not in ["text", "vision", "hybrid", "docling", "transcription"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extraction_method: {processing_method}. Must be 'text', 'vision', 'hybrid', 'docling', or 'transcription'",
        )

    # For images, force vision processing
    if file_type == "image" and processing_method != "vision":
        logger.info("Overriding extraction_method to 'vision' for image file")
        processing_method = "vision"

    # Create job
    user_id = current_user.get("user_id") if current_user else None
    job_guest_token = guest_token if user_id is None else None
    job_id = await crud.create_job(
        file_name=file_record["original_filename"],
        file_type=file_type,
        provider=payload.provider,
        model=payload.model,
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
        except Exception:
            pass  # Metadata update is optional

    # Queue background processing with appropriate method
    worker_kwargs = {
        "schema_definition_override": _schema_definition,
        "prompt_override": payload.prompt,
        "temperature_override": payload.temperature,
        "max_tokens_override": payload.max_tokens,
        "quality_threshold": payload.quality_threshold,
        "auto_preprocess": payload.auto_preprocess,
        "extraction_method_override": processing_method,
        "is_transcription": is_transcription,
    }
    if processing_method == "text":
        background_tasks.add_task(
            run_text_processing_job, job_id, str(file_path), **worker_kwargs
        )
    else:  # "vision", "hybrid", "docling", or "transcription"
        background_tasks.add_task(
            run_processing_job, job_id, str(file_path), **worker_kwargs
        )

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
