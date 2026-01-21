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
    """
    # Import here to avoid circular dependency
    from services.processing import run_text_processing_job

    # Get file info
    file_info = await crud.get_uploaded_file(request.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

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
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
