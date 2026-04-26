from typing import Optional

from fastapi import APIRouter, Depends

from database import crud
from dependencies import require_admin

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/usage")
async def get_usage_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    schema_name: Optional[str] = None,
    processing_method: Optional[str] = None,
    document_type: Optional[str] = None,
    current_user: dict = Depends(require_admin),
):
    _ = current_user
    return await crud.get_job_analytics(
        date_from=date_from,
        date_to=date_to,
        provider=provider,
        model=model,
        schema_name=schema_name,
        processing_method=processing_method,
        document_type=document_type,
    )
