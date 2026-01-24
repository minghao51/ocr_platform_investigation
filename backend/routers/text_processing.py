from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import crud

router = APIRouter(prefix="/api/text", tags=["text-processing"])

class TextProcessRequest(BaseModel):
    file_id: str
    provider: str
    model: str
    schema_id: Optional[int] = None

@router.post("/process")
async def process_text_document(
    request: TextProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Start text extraction job

    Processes PDF using pdfplumber text extraction + text-only LLM
    Note: Only supports PDF files. For images and scanned documents, use Vision Extraction.
    """
    # Import here to avoid circular dependency
    from services.processing import run_text_processing_job

    # Get file info
    file_info = await crud.get_uploaded_file(request.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    # Validate file type - text extraction only supports PDFs
    file_type = file_info.get("file_type", "").lower()
    if file_type != "pdf":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Text Extraction only supports PDF files",
                "message": f"File type '{file_type}' is not supported by Text Extraction. "
                          f"Please use Vision Extraction for images and scanned documents.",
                "file_type": file_type,
                "suggestion": "Try using the Smart Extraction (auto-detection) or Vision Extraction tab instead."
            }
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
        processing_method='text'
    )

    # Get file path
    file_path = file_info["file_path"]

    # Queue background processing
    background_tasks.add_task(
        run_text_processing_job,
        job_id,
        file_path
    )

    return {"job_id": job_id}

@router.get("/status/{job_id}")
async def get_text_job_status(job_id: int):
    """Get job status (reuses existing jobs table)"""
    import json
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = job.get("result")
    if result and isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            pass

    return {
        "job_id": job["id"],
        "file_name": job["file_name"],
        "file_type": job["file_type"],
        "status": job["status"],
        "provider": job["provider"],
        "model": job["model"],
        "schema_name": job["schema_name"],
        "created_at": job["created_at"],
        "updated_at": job.get("completed_at") or job.get("updated_at") or job["created_at"],
        "result": result,
        "error": job.get("error_message"),
        "processing_time": job.get("processing_time_seconds"),
        "processing_method": job.get("processing_method")
    }
