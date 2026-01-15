from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import ProcessRequest, ProcessResponse
from database import crud
from services.processing import run_processing_job
import json

router = APIRouter(prefix="/api/process", tags=["processing"])

@router.post("/", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Process a document with VLM"""

    # Get schema definition
    if request.schema_id:
        schema_record = await crud.get_schema(request.schema_id)
        if not schema_record:
            raise HTTPException(status_code=404, detail="Schema not found")

        schema_definition = json.loads(schema_record["definition"])
        schema_name = schema_record["name"]
    elif request.schema_definition:
        schema_definition = request.schema_definition
        schema_name = "Custom"
    else:
        raise HTTPException(
            status_code=400,
            detail="Either schema_id or schema_definition must be provided"
        )

    # Create job record
    from pathlib import Path
    file_path = Path(f"./data/uploads/{request.file_id}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine file type
    file_ext = file_path.suffix.lower()
    file_type = "pdf" if file_ext == ".pdf" else "image"

    # Create job
    job_id = await crud.create_job(
        file_name=file_path.name,
        file_type=file_type,
        provider=request.provider,
        model=request.model,
        schema_id=request.schema_id,
        schema_name=schema_name
    )

    # Queue background processing
    background_tasks.add_task(run_processing_job, job_id)

    return ProcessResponse(
        job_id=job_id,
        status="pending"
    )

@router.get("/status/{job_id}")
async def get_job_status(job_id: int):
    """Get processing job status"""

    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job["id"],
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error_message"),
        "processing_time": job.get("processing_time_seconds")
    }
