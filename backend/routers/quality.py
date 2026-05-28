"""
Quality Check API Endpoint

Allows users to check image quality before submitting for OCR processing.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from typing import Optional
from pydantic import BaseModel
from pathlib import Path
from paths import UPLOAD_DIR
from services.quality_gate import QualityGate
from services.image_service import ImageService
from database import crud
from dependencies import get_optional_user
from config import get_settings
from routers.shared import ensure_file_access
from limiter import limiter
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quality", tags=["quality"])


class QualityCheckRequest(BaseModel):
    """Request body for quality check by file_id."""

    file_id: str
    estimated_dpi: Optional[int] = 200


class QualityCheckResponse(BaseModel):
    """Response from quality check."""

    passed: bool
    overall_score: float
    level: str
    checks: dict
    recommendations: list[str]
    auto_fixable_issues: list[str]
    should_reject: bool
    rejection_reason: str


@router.post("/check", response_model=QualityCheckResponse)
@limiter.limit("5/minute")
async def check_file_quality(
    payload: QualityCheckRequest,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
):
    """
    Check the quality of an uploaded file before processing.

    This runs the quality gate assessment without spending VLM API credits.
    Useful for previewing image quality and deciding whether to preprocess.
    """
    # Get file metadata
    file_record = await crud.get_uploaded_file(payload.file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    ensure_file_access(file_record, current_user, request.headers.get("X-Guest-Token"))

    file_path = Path(file_record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File has been deleted or moved")

    file_type = file_record["file_extension"]

    if file_type not in (".jpg", ".jpeg", ".png"):
        raise HTTPException(
            status_code=400,
            detail="Quality check is only supported for image files (JPG, PNG)",
        )

    # Run quality assessment
    gate = QualityGate()
    image_service = ImageService()

    try:
        image = image_service.load_image(str(file_path))
        report = gate.assess(image, estimated_dpi=payload.estimated_dpi)
    except Exception as e:
        logger.error("Quality check failed for file %s: %s", payload.file_id, e)
        raise HTTPException(status_code=500, detail="Quality check error")

    return QualityCheckResponse(**gate.to_dict(report))


@router.post("/check-upload", response_model=QualityCheckResponse)
async def check_uploaded_file_quality(
    request: Request,
    file: UploadFile = File(...),
    estimated_dpi: Optional[int] = Form(200),
    current_user: dict | None = Depends(get_optional_user),
):
    """
    Upload and check image quality in one step.

    Useful for quick quality previews without permanently storing the file.
    The uploaded file is temporarily stored and cleaned up after assessment.
    """
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    settings = get_settings()
    # Save temporarily
    temp_id = str(uuid.uuid4())
    temp_path = Path(UPLOAD_DIR) / f"{temp_id}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    try:
        total_size = 0
        chunk_size = 8192
        with open(temp_path, "wb") as temp_file:
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)
                if total_size > settings.max_file_size:
                    max_size_mb = settings.max_file_size / (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size is {max_size_mb:.0f}MB",
                    )
                temp_file.write(chunk)

        gate = QualityGate()
        image_service = ImageService()

        image = image_service.load_image(str(temp_path))
        report = gate.assess(image, estimated_dpi=estimated_dpi)

        return QualityCheckResponse(**gate.to_dict(report))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Quality check failed for uploaded file: %s", e)
        raise HTTPException(status_code=500, detail="Quality check error")
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()
