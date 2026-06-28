from fastapi import APIRouter
from typing import Any, Dict, List
from extraction_methods import (
    AVAILABLE_METHODS_BY_FILE_TYPE,
    DEFAULT_METHOD_BY_FILE_TYPE,
    PROVIDER_REQUIRED_METHODS,
    list_extraction_methods,
)
from models.schemas import (
    MAX_PROMPT_LENGTH,
    MAX_TOKENS_LIMIT,
    PROCESSING_DEFAULT_MAX_TOKENS,
    PROCESSING_DEFAULT_QUALITY_THRESHOLD,
    PROCESSING_DEFAULT_TEMPERATURE,
)
from services.schema_service import SchemaService
from services.provider_catalog import list_provider_catalog

router = APIRouter(prefix="/api/extract", tags=["extract-settings"])

PROCESSING_DEFAULTS: Dict[str, Any] = {
    "temperature": {
        "default": PROCESSING_DEFAULT_TEMPERATURE,
        "min": 0.0,
        "max": 2.0,
        "step": 0.1,
    },
    "max_tokens": {
        "default": PROCESSING_DEFAULT_MAX_TOKENS,
        "min": 256,
        "max": MAX_TOKENS_LIMIT,
        "step": 1,
    },
    "quality_threshold": {
        "default": PROCESSING_DEFAULT_QUALITY_THRESHOLD,
        "min": 0,
        "max": 80,
        "step": 5,
    },
    "auto_preprocess": {"default": True},
    "skip_quality": {"default": False},
    "prompt_max_length": MAX_PROMPT_LENGTH,
}

SCHEMA_MODES: List[Dict[str, Any]] = [
    {"id": "raw", "label": "Raw", "available_for": ["docling-parse"]},
    {"id": "auto-detect", "label": "Auto-detect", "available_for": None},
    {"id": "manual", "label": "Manual", "available_for": None},
]


@router.get("/settings")
async def get_extract_settings():
    providers = list_provider_catalog()
    templates = SchemaService.get_builtin_templates()

    return {
        "providers": providers,
        "extraction_methods": list_extraction_methods(),
        "provider_required_methods": list(PROVIDER_REQUIRED_METHODS),
        "schema_modes": SCHEMA_MODES,
        "schema_templates": {name: tpl for name, tpl in templates.items()},
        "defaults": PROCESSING_DEFAULTS,
        "file_type_methods": DEFAULT_METHOD_BY_FILE_TYPE,
        "available_methods_by_file_type": AVAILABLE_METHODS_BY_FILE_TYPE,
    }
