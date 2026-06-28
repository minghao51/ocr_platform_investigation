import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.provider_catalog import create_provider
from services.provider_utils import choose_default_provider_model
from services.text_extraction import TextExtractionService


class SchemaSuggestionService:
    def __init__(self) -> None:
        self.text_extraction = TextExtractionService()

    def _build_response_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_type": {"type": "string"},
                "draft_name": {"type": "string"},
                "confidence": {"type": "number"},
                "rationale": {"type": "string"},
                "field_descriptions": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "schema_definition": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "properties": {"type": "object"},
                        "required": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["type", "properties"],
                },
            },
            "required": [
                "document_type",
                "draft_name",
                "confidence",
                "rationale",
                "field_descriptions",
                "schema_definition",
            ],
        }

    def _build_prompt(self, file_descriptions: List[Dict[str, Any]]) -> str:
        return (
            "Infer a compact but useful JSON schema for structured extraction from these documents. "
            "Use zero-shot reasoning based on file names, extracted text, and layout cues. "
            "Prefer practical business fields, keep types simple, and include only fields that are likely to recur. "
            "Return a draft name, a document type label, field descriptions, rationale, confidence, and a JSON schema."
            f"\n\nDocuments:\n{json.dumps(file_descriptions, indent=2)}"
        )

    def _collect_file_descriptions(
        self, file_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        descriptions: List[Dict[str, Any]] = []
        for record in file_records:
            file_path = Path(record["file_path"])
            description: Dict[str, Any] = {
                "file_id": record["file_id"],
                "file_name": record["original_filename"],
                "content_type": record["content_type"],
                "file_extension": record["file_extension"],
            }
            if record["file_extension"] == ".pdf":
                extracted_text = self.text_extraction.extract_text_from_pdf(
                    str(file_path)
                )
                description["text_preview"] = (extracted_text or "")[:4000]
            descriptions.append(description)
        return descriptions

    async def suggest_schema(
        self,
        file_records: List[Dict[str, Any]],
        provider_name: Optional[str],
        model: Optional[str],
        api_key: str,
    ) -> Dict[str, Any]:
        if not provider_name or not model:
            provider_name, model = choose_default_provider_model()

        response_schema = self._build_response_schema()
        prompt = self._build_prompt(self._collect_file_descriptions(file_records))

        async with create_provider(provider_name, api_key=api_key) as provider:
            result = await provider.process_text(
                text=prompt,
                prompt=(
                    "Generate a schema suggestion for OCR extraction from the provided document summaries. "
                    "Return only valid JSON."
                ),
                schema_definition=response_schema,
                model=model,
            )

        if result.error:
            raise ValueError(result.error)

        payload = json.loads(result.content)
        schema_definition = payload.get("schema_definition") or {}
        if schema_definition.get("type") != "object":
            schema_definition["type"] = "object"
        schema_definition.setdefault("properties", {})
        schema_definition.setdefault(
            "required", list(schema_definition["properties"].keys())
        )

        return {
            "provider": provider_name,
            "model": model,
            "document_type": payload.get("document_type", "document"),
            "draft_name": payload.get("draft_name", "Suggested Schema"),
            "confidence": payload.get("confidence", 0.0),
            "rationale": payload.get("rationale", ""),
            "field_descriptions": payload.get("field_descriptions", {}),
            "schema_definition": schema_definition,
        }
