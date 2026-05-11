import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.prompt_templates import (
    COT_INSTRUCTION,
    RAW_OUTPUT_TEMPLATE,
    classify_doc_type_hint,
    get_doc_type_template,
)

logger = logging.getLogger(__name__)


@dataclass
class PromptResult:
    system_prompt: str
    user_prompt: str
    enriched_schema: Optional[Dict[str, Any]] = None
    doc_type_used: str = "generic"
    cot_enabled: bool = False
    hints_injected: bool = False


class PromptOptimizer:
    def __init__(self) -> None:
        pass

    async def optimize_prompt(
        self,
        prompt: str,
        schema_definition: Optional[Dict[str, Any]],
        *,
        doc_type: Optional[str] = None,
        quality_score: Optional[float] = None,
        processing_method: str = "vision",
        schema_name: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        is_raw_output: bool = False,
        is_transcription: bool = False,
        layout_context: Optional[Dict[str, Any]] = None,
    ) -> PromptResult:
        if is_raw_output or is_transcription:
            return self._build_raw_output_prompt(prompt, quality_score, layout_context)

        resolved_doc_type = doc_type or classify_doc_type_hint(schema_name, schema_definition)
        template = get_doc_type_template(resolved_doc_type)

        system_prompt = self._build_system_prompt(template, resolved_doc_type)

        enriched_schema = self._enrich_schema_descriptions(schema_definition)

        learning_hints = await self._fetch_learning_hints(
            schema_name, provider, model, processing_method
        )

        use_cot = self._should_use_cot(quality_score, resolved_doc_type)

        user_prompt = self._format_xml_sandwich(
            base_prompt=prompt,
            template=template,
            schema=enriched_schema,
            learning_hints=learning_hints,
            use_cot=use_cot,
            layout_context=layout_context,
        )

        logger.info(
            "Prompt optimized: doc_type=%s, cot=%s, hints=%s, quality_score=%s",
            resolved_doc_type, use_cot, bool(learning_hints), quality_score,
        )

        return PromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            enriched_schema=enriched_schema,
            doc_type_used=resolved_doc_type,
            cot_enabled=use_cot,
            hints_injected=bool(learning_hints),
        )

    def _build_system_prompt(self, template: Dict[str, Any], doc_type: str) -> str:
        role = template["system_role"]
        parts = [role]

        focus = template.get("focus_areas", [])
        if focus:
            focus_list = "\n".join(f"  - {area}" for area in focus)
            parts.append(f"\n\nKey areas to focus on:\n{focus_list}")

        parts.append(
            "\n\nRules:\n"
            "  - Return ONLY valid JSON matching the provided schema\n"
            "  - Do NOT include explanations, markdown formatting, or commentary\n"
            "  - If a field value is not visible or legible, use null\n"
            "  - Preserve exact values (do not normalize or reformat dates/numbers)\n"
            "  - For monetary amounts, use numbers without currency symbols"
        )

        return "".join(parts)

    def _enrich_schema_descriptions(
        self, schema: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if schema is None:
            return None

        enriched = json.loads(json.dumps(schema))

        if "properties" not in enriched:
            return enriched

        for prop_name, prop_def in enriched["properties"].items():
            if isinstance(prop_def, dict) and "description" not in prop_def:
                auto_desc = self._auto_describe_field(prop_name, prop_def)
                if auto_desc:
                    prop_def["description"] = auto_desc

        return enriched

    def _auto_describe_field(self, name: str, prop_def: Dict[str, Any]) -> Optional[str]:
        _field_hints: Dict[str, str] = {
            "invoice_number": "Unique invoice identifier",
            "invoice_no": "Unique invoice identifier",
            "date": "Document date in original format",
            "due_date": "Payment due date",
            "vendor": "Vendor or seller name",
            "merchant": "Merchant or business name",
            "total": "Final total amount",
            "subtotal": "Subtotal before tax",
            "tax": "Tax amount or rate",
            "amount": "Monetary amount",
            "quantity": "Item quantity",
            "unit_price": "Price per unit",
            "description": "Item or field description",
            "name": "Name or title",
            "address": "Full address",
            "phone": "Phone number",
            "email": "Email address",
            "document_type": "Type of identification document",
            "full_name": "Full legal name",
            "first_name": "Given name",
            "last_name": "Surname or family name",
            "date_of_birth": "Date of birth",
            "expiration_date": "Document expiration date",
            "document_number": "Government document or ID number",
            "items": "List of line items",
            "entities": "List of named entities found",
            "text": "Extracted text content",
            "payment_method": "Method of payment used",
            "price": "Item price",
        }

        return _field_hints.get(name.lower())

    async def _fetch_learning_hints(
        self,
        schema_name: Optional[str],
        provider: Optional[str],
        model: Optional[str],
        processing_method: str,
    ) -> Optional[str]:
        if not schema_name:
            return None

        try:
            from database import crud

            entries = await crud.list_prompt_learning_entries(
                schema_name=schema_name,
                provider=provider,
                model=model,
                processing_method=processing_method,
            )
        except Exception as e:
            logger.debug("Could not fetch learning hints: %s", e)
            return None

        prompt_hints = [e for e in entries if e.get("entry_type") == "prompt_hint"]
        if not prompt_hints:
            return None

        hint_parts = []
        for entry in prompt_hints[:3]:
            content = entry.get("content", "")
            count = entry.get("source_correction_count", 0)
            if content and count > 0:
                hint_parts.append(f"- {content} (from {count} corrections)")

        if not hint_parts:
            return None

        return (
            "Based on previous corrections for this schema type:\n"
            + "\n".join(hint_parts)
        )

    def _should_use_cot(
        self, quality_score: Optional[float], doc_type: str
    ) -> bool:
        if doc_type == "handwritten":
            return True
        if quality_score is not None and quality_score < 50.0:
            return True
        return False

    def _format_xml_sandwich(
        self,
        base_prompt: str,
        template: Dict[str, Any],
        schema: Optional[Dict[str, Any]],
        learning_hints: Optional[str],
        use_cot: bool,
        layout_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        parts: List[str] = []

        parts.append("<instructions>")
        parts.append(base_prompt)
        parts.append("</instructions>")

        if learning_hints:
            parts.append("\n\n<correction_hints>")
            parts.append(learning_hints)
            parts.append("</correction_hints>")

        extraction_hints = template.get("extraction_hints", [])
        if extraction_hints:
            parts.append("\n\n<extraction_guidance>")
            for hint in extraction_hints:
                parts.append(f"- {hint}")
            parts.append("</extraction_guidance>")

        if schema:
            parts.append("\n\n<target_schema>")
            parts.append(json.dumps(schema, indent=2))
            parts.append("</target_schema>")

        if layout_context:
            parts.append("\n\n<layout_context>")
            compact_pages = [
                {
                    "page_number": p.get("page_number"),
                    "text_preview": p.get("text_preview", "")[:600],
                    "block_count": p.get("block_count"),
                    "table_count": p.get("table_count"),
                    "image_count": p.get("image_count"),
                }
                for p in layout_context.get("pages", [])[:8]
            ]
            parts.append(json.dumps(compact_pages, indent=2))
            parts.append("</layout_context>")

        if use_cot:
            parts.append(COT_INSTRUCTION)

        parts.append(
            "\n\nRespond ONLY with valid JSON matching the target_schema. "
            "No explanations, no markdown, no commentary."
        )

        return "\n".join(parts)

    def _build_raw_output_prompt(
        self,
        base_prompt: str,
        quality_score: Optional[float],
        layout_context: Optional[Dict[str, Any]] = None,
    ) -> PromptResult:
        template = RAW_OUTPUT_TEMPLATE
        system_parts = [template["system_role"]]

        rules = template.get("formatting_rules", [])
        if rules:
            rule_list = "\n".join(f"  {i + 1}. {rule}" for i, rule in enumerate(rules))
            system_parts.append(f"\n\nFormatting rules:\n{rule_list}")

        system_prompt = "".join(system_parts)

        user_parts: List[str] = []
        if base_prompt and base_prompt != "Extract all information from this document":
            user_parts.append(base_prompt)
        else:
            user_parts.append(
                "Transcribe the entire document content as high-fidelity Markdown. "
                "Preserve all structural elements (headings, tables, lists, formatting)."
            )

        if layout_context:
            user_parts.append(
                "\n\nAdditional layout context for reference:\n"
                + json.dumps(
                    [
                        {
                            "page": p.get("page_number"),
                            "blocks": p.get("block_count"),
                            "tables": p.get("table_count"),
                        }
                        for p in layout_context.get("pages", [])[:8]
                    ],
                    indent=2,
                )
            )

        use_cot = quality_score is not None and quality_score < 50.0
        if use_cot:
            user_parts.append(
                "\n\nFirst, briefly describe the document layout you see. "
                "Then, provide the full transcription."
            )

        user_parts.append(
            "\n\nReturn ONLY clean Markdown. Do not wrap the response in JSON."
        )

        return PromptResult(
            system_prompt=system_prompt,
            user_prompt="\n".join(user_parts),
            enriched_schema=None,
            doc_type_used="generic",
            cot_enabled=use_cot,
            hints_injected=False,
        )
