from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from models.schemas import ProcessRequest, ProcessResponse
from database import crud
from services.processing import run_processing_job, run_text_processing_job
from services.document_classifier import DocumentClassifier
from dependencies import check_daily_limit, increment_daily_limit, get_current_user
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/process", tags=["processing"])

@router.post("/", response_model=ProcessResponse)
async def process_document(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    extraction_method: str = None,  # NEW: "auto", "text", "vision", or None (auto)
    current_user: dict = Depends(check_daily_limit)
):
    """
    Process a document with intelligent routing

    extraction_method options:
    - None or "auto": Automatically detect best pipeline (recommended)
    - "text": Force text extraction (pdfplumber + LLM) - fast & cheap
    - "vision": Force vision extraction (VLM) - accurate & expensive
    """

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

    # Get file metadata from database
    file_record = await crud.get_uploaded_file(request.file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Verify file still exists on disk
    from pathlib import Path
    file_path = Path(file_record["file_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File has been deleted or moved"
        )

    # Determine file type
    file_type = "pdf" if file_record["file_extension"] == ".pdf" else "image"

    # NEW: Intelligent routing logic
    processing_method = extraction_method
    classification_info = None

    # Auto-detect if not specified or set to "auto"
    if not extraction_method or extraction_method == "auto":
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
                    "reasoning": analysis.reasoning
                }

                logger.info(f"Auto-detected pipeline: {processing_method} for {file_record['original_filename']}")
                logger.info(f"  Classification: {analysis.type} (confidence: {analysis.confidence:.2f})")
                logger.info(f"  Reasoning: {analysis.reasoning}")

            except Exception as e:
                logger.warning(f"Classification failed, falling back to vision: {str(e)}")
                processing_method = "vision"
        else:
            # Images always use vision processing
            processing_method = "vision"
            classification_info = {"reasoning": "Image file, using vision processing"}

    # Validate extraction method
    if processing_method not in ["text", "vision", "hybrid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extraction_method: {processing_method}. Must be 'text', 'vision', or 'hybrid'"
        )

    # For images, force vision processing
    if file_type == "image" and processing_method != "vision":
        logger.info(f"Overriding extraction_method to 'vision' for image file")
        processing_method = "vision"

    # Create job
    user_id = current_user.get("user_id")
    job_id = await crud.create_job(
        file_name=file_record["original_filename"],
        file_type=file_type,
        provider=request.provider,
        model=request.model,
        schema_id=request.schema_id,
        schema_name=schema_name,
        processing_method=processing_method,
        user_id=user_id
    )

    # Increment daily request counter (non-blocking)
    if user_id:
        background_tasks.add_task(increment_daily_limit, user_id)

    # Store classification info in job metadata (optional, for debugging)
    if classification_info:
        try:
            await crud.update_job_metadata(job_id, classification_info)
        except:
            pass  # Metadata update is optional

    # Queue background processing with appropriate method
    if processing_method == "text":
        background_tasks.add_task(run_text_processing_job, job_id, str(file_path))
    else:  # "vision" or "hybrid"
        background_tasks.add_task(run_processing_job, job_id, str(file_path))

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


    
    result = job.get("result")
    if result and isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            pass  # Keep as string if parsing fails

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
