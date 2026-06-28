"""Shared extraction-method metadata and capability rules."""

from typing import Any

EXTRACTION_METHODS = (
    "text",
    "vision",
    "hybrid",
    "docling-parse",
    "docling-extract",
    "transcription",
)
EXTRACTION_METHODS_WITH_AUTO = ("auto",) + EXTRACTION_METHODS

PROVIDER_REQUIRED_METHODS = (
    "auto",
    "text",
    "vision",
    "hybrid",
    "docling-parse",
    "transcription",
)
RAW_OUTPUT_METHODS = ("docling-parse",)

EXTRACTION_METHOD_METADATA: dict[str, dict[str, str]] = {
    "auto": {
        "name": "Auto",
        "description": "Automatically selects the best extraction method.",
    },
    "text": {
        "name": "Text",
        "description": "Fast text extraction from digital PDFs.",
    },
    "vision": {
        "name": "Vision",
        "description": "Uses AI vision models for scanned documents and images.",
    },
    "hybrid": {
        "name": "Hybrid",
        "description": "Combines text extraction and vision processing.",
    },
    "docling-parse": {
        "name": "PyMuPDF + LLM",
        "description": "PyMuPDF parsing then LLM structuring. Cost-sensitive.",
    },
    "docling-extract": {
        "name": "Docling Extract",
        "description": "Best accuracy (86%). Local VLM, free, private.",
    },
    "transcription": {
        "name": "Transcription",
        "description": "Full document transcription to Markdown.",
    },
}

DEFAULT_METHOD_BY_FILE_TYPE: dict[str, str] = {
    "application/pdf": "docling-extract",
    "image/*": "docling-extract",
    "document/*": "docling-parse",
}

AVAILABLE_METHODS_BY_FILE_TYPE: dict[str, list[str]] = {
    "application/pdf": list(EXTRACTION_METHODS),
    "image/*": ["docling-extract", "vision"],
    "document/*": ["docling-parse", "transcription"],
}


def list_extraction_methods() -> list[dict[str, Any]]:
    return [
        {
            "id": method_id,
            "name": EXTRACTION_METHOD_METADATA[method_id]["name"],
            "description": EXTRACTION_METHOD_METADATA[method_id]["description"],
        }
        for method_id in EXTRACTION_METHODS_WITH_AUTO
    ]


def requires_provider_model(processing_method: str) -> bool:
    return processing_method in PROVIDER_REQUIRED_METHODS


def supports_raw_output(processing_method: str) -> bool:
    return processing_method in RAW_OUTPUT_METHODS
