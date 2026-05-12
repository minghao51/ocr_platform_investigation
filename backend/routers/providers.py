from fastapi import APIRouter
from services.provider_catalog import list_provider_catalog

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/")
async def list_providers():
    """List all VLM providers and their models from config."""
    return list_provider_catalog()
