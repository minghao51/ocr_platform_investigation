import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from services.schema_service import SchemaService
from services.processors.base import Processor

logger = logging.getLogger(__name__)

_docling_extractors: dict[frozenset, Any] = {}


def _get_docling_extractor(allowed_formats: list) -> Any:
    key = frozenset(allowed_formats)
    extractor = _docling_extractors.get(key)
    if extractor is None:
        from docling.document_extractor import DocumentExtractor

        extractor = DocumentExtractor(allowed_formats=list(key))
        _docling_extractors[key] = extractor
    return extractor


class DoclingExtractProcessor(Processor):
    def _validate_file_size(self, file_path: str) -> None:
        from config import get_settings

        max_size = get_settings().max_file_size
        size = Path(file_path).stat().st_size
        if size > max_size:
            raise ValueError(
                f"File too large ({size / 1024 / 1024:.1f}MB). Max: {max_size / 1024 / 1024}MB"
            )

    async def process(
        self,
        job_id: Optional[int],
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition: Optional[Dict[str, Any]],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        from docling.datamodel.base_models import InputFormat

        try:
            self._validate_file_size(file_path)

            start_time = time.time()

            file_ext = Path(file_path).suffix.lower()

            if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
                allowed_formats = [InputFormat.IMAGE]
            elif file_ext == ".pdf":
                allowed_formats = [InputFormat.PDF]
            else:
                allowed_formats = [InputFormat.IMAGE, InputFormat.PDF]

            extractor = _get_docling_extractor(allowed_formats)

            result = extractor.extract(source=file_path, template=schema_definition)

            processing_time = time.time() - start_time

            if result.pages and len(result.pages) > 0:
                page_data = result.pages[0]
                extracted = page_data.extracted_data

                schema_service = SchemaService()
                is_valid, validated_data, error = schema_service.validate_data(
                    extracted, schema_definition
                )

                if is_valid:
                    return {
                        "success": True,
                        "data": validated_data,
                        "raw_response": extracted,
                        "metadata": {
                            "extraction_method": "docling-extract",
                            "processing_time": processing_time,
                            "pages_processed": len(result.pages),
                        },
                        "usage": {},
                        "cost": 0.0,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Schema validation failed: {error}",
                        "raw_response": extracted,
                        "metadata": {
                            "extraction_method": "docling-extract",
                            "processing_time": processing_time,
                        },
                    }
            else:
                return {
                    "success": False,
                    "error": "No data extracted from document",
                    "metadata": {
                        "extraction_method": "docling-extract",
                        "processing_time": processing_time,
                    },
                }

        except Exception as e:
            logger.error("Docling extract error: %s", e, exc_info=True)
            error_type = type(e).__name__
            if "docling" in str(e).lower() or "Docling" in error_type:
                return {
                    "success": False,
                    "error": f"Docling extractor error: {str(e)}",
                    "metadata": {"extraction_method": "docling-extract"},
                }
            else:
                return {
                    "success": False,
                    "error": f"Unexpected error: {type(e).__name__}: {str(e)}",
                    "metadata": {"extraction_method": "docling-extract"},
                }
