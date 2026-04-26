from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from database import crud
from dependencies import check_and_increment_daily_limit, get_current_user
from limiter import limiter, get_rate_limit_value
from routers.job_serialization import serialize_job
from routers.shared import ensure_file_access, ensure_job_access
from services.job_queue import enqueue_processing_task

router = APIRouter(prefix="/api/text", tags=["text-processing"])


class TextProcessRequest(BaseModel):
    file_id: str
    provider: str
    model: str
    schema_id: Optional[int] = None


@router.post("/process")
@limiter.limit(get_rate_limit_value)
async def process_text_document(
    http_request: Request,
    request: TextProcessRequest,
    current_user: dict = Depends(check_and_increment_daily_limit),
):
    """
    Start text extraction job

    Processes PDF using pdfplumber text extraction + text-only LLM
    Note: Only supports PDF files. For images and scanned documents, use Vision Extraction.
    """
    _ = http_request

    # Get file info
    file_info = await crud.get_uploaded_file(request.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    ensure_file_access(file_info, current_user)

    # Validate file type - text extraction only supports PDFs
    file_extension = (file_info.get("file_extension") or "").lower()
    content_type = (file_info.get("content_type") or "").lower()
    is_pdf = file_extension == ".pdf" or content_type == "application/pdf"
    if not is_pdf:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Text Extraction only supports PDF files",
                "message": f"File type '{file_extension or content_type or 'unknown'}' is not supported by Text Extraction. "
                f"Please use Vision Extraction for images and scanned documents.",
                "file_type": file_extension or content_type or "unknown",
                "suggestion": "Try using the Smart Extraction (auto-detection) or Vision Extraction tab instead.",
            },
        )

    # Get schema info if provided
    schema_name = None
    if request.schema_id:
        schema = await crud.get_schema(request.schema_id)
        if schema:
            schema_name = schema["name"]

    # Create job record with processing_method='text'
    job_id = await crud.create_job(
        file_name=file_info["original_filename"],
        file_type="pdf",  # Text extraction only supports PDFs
        provider=request.provider,
        model=request.model,
        schema_id=request.schema_id,
        schema_name=schema_name,
        processing_method="text",
        user_id=current_user.get("user_id"),
    )

    # Get file path
    file_path = file_info["file_path"]

    # Queue durable background processing
    await enqueue_processing_task(
        job_id,
        file_path,
        payload={},
        task_type="text",
    )

    return {"job_id": job_id}


@router.get("/status/{job_id}")
async def get_text_job_status(
    job_id: int, current_user: dict = Depends(get_current_user)
):
    """Get job status (reuses existing jobs table)"""
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user)
    return serialize_job(job)
