from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from database import crud
from dependencies import require_admin

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _validate_date(date_str: str, field_name: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format. Expected YYYY-MM-DD",
        )


@router.get("/usage")
async def get_usage_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    schema_name: Optional[str] = None,
    processing_method: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = 1000,
    current_user: dict = Depends(require_admin),
):
    _ = current_user
    if date_from:
        date_from = _validate_date(date_from, "date_from")
    if date_to:
        date_to = _validate_date(date_to, "date_to")
    limit = max(1, min(limit, 1000))
    return await crud.get_job_analytics(
        date_from=date_from,
        date_to=date_to,
        provider=provider,
        model=model,
        schema_name=schema_name,
        processing_method=processing_method,
        document_type=document_type,
    )
