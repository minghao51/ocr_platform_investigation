from fastapi import APIRouter
from typing import Any, Dict, List
from services.schema_service import SchemaService
from services.provider_catalog import list_provider_catalog

router = APIRouter(prefix="/api/extract", tags=["extract-settings"])

EXTRACTION_METHODS: List[Dict[str, Any]] = [
    {
        "id": "auto",
        "name": "Auto",
        "description": "Automatically selects the best extraction method.",
    },
    {
        "id": "text",
        "name": "Text",
        "description": "Fast text extraction from digital PDFs.",
    },
    {
        "id": "vision",
        "name": "Vision",
        "description": "Uses AI vision models for scanned documents and images.",
    },
    {
        "id": "hybrid",
        "name": "Hybrid",
        "description": "Combines text extraction and vision processing.",
    },
    {
        "id": "docling-parse",
        "name": "PyMuPDF Parse",
        "description": "PyMuPDF parsing then LLM structuring. Cost-sensitive.",
    },
    {
        "id": "docling-extract",
        "name": "Docling Extract",
        "description": "Best accuracy (86%). Local VLM, free, private.",
    },
    {
        "id": "transcription",
        "name": "Transcription",
        "description": "Full document transcription to Markdown.",
    },
]

PROCESSING_DEFAULTS: Dict[str, Any] = {
    "temperature": {"default": 0.1, "min": 0.0, "max": 2.0, "step": 0.1},
    "max_tokens": {"default": 8192, "min": 256, "max": 65536, "step": 1},
    "quality_threshold": {"default": 40, "min": 0, "max": 80, "step": 5},
    "auto_preprocess": {"default": True},
    "skip_quality": {"default": False},
    "prompt_max_length": 2000,
}

FILE_TYPE_METHODS: Dict[str, str] = {
    "application/pdf": "docling-extract",
    "image/*": "docling-extract",
    "audio/*": "transcription",
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
        "extraction_methods": EXTRACTION_METHODS,
        "schema_modes": SCHEMA_MODES,
        "schema_templates": {name: tpl for name, tpl in templates.items()},
        "defaults": PROCESSING_DEFAULTS,
        "file_type_methods": FILE_TYPE_METHODS,
    }
