import pytest

from services.prompt_optimizer import PromptOptimizer, PromptResult
from services.prompt_templates import (
    COT_INSTRUCTION,
    DOC_TYPE_TEMPLATES,
    RAW_OUTPUT_TEMPLATE,
    classify_doc_type_hint,
    get_doc_type_template,
)


@pytest.fixture
def optimizer():
    return PromptOptimizer()


class TestClassifyDocTypeHint:
    def test_invoice_from_schema_name(self):
        assert classify_doc_type_hint("Invoice Template", None) == "invoice"

    def test_receipt_from_schema_name(self):
        assert classify_doc_type_hint("Receipt Schema", None) == "receipt"

    def test_id_from_schema_name_identity(self):
        assert classify_doc_type_hint("Identity Document", None) == "id"

    def test_id_from_schema_name_passport(self):
        assert classify_doc_type_hint("Passport Reader", None) == "id"

    def test_id_from_schema_name_license(self):
        assert classify_doc_type_hint("Driver License", None) == "id"

    def test_table_heavy_from_schema_name(self):
        assert classify_doc_type_hint("Table Report", None) == "table_heavy"

    def test_handwritten_from_schema_name(self):
        assert classify_doc_type_hint("Handwritten Notes", None) == "handwritten"

    def test_generic_from_unknown_name(self):
        assert classify_doc_type_hint("Custom Form", None) == "generic"

    def test_valid_id_does_not_match_via_substring(self):
        assert classify_doc_type_hint("ValidDocument", None) != "id"

    def test_standalone_id_matches(self):
        assert classify_doc_type_hint("ID", None) == "id"

    def test_id_as_word_matches(self):
        assert classify_doc_type_hint("National ID Card", None) == "id"

    def test_none_name_invoice_schema_props(self):
        schema = {"type": "object", "properties": {"invoice_number": {"type": "string"}, "items": {"type": "array"}}}
        assert classify_doc_type_hint(None, schema) == "invoice"

    def test_none_name_receipt_schema_props(self):
        schema = {"type": "object", "properties": {"merchant": {"type": "string"}, "payment_method": {"type": "string"}}}
        assert classify_doc_type_hint(None, schema) == "receipt"

    def test_none_name_id_schema_props(self):
        schema = {"type": "object", "properties": {"document_number": {"type": "string"}, "full_name": {"type": "string"}}}
        assert classify_doc_type_hint(None, schema) == "id"

    def test_none_name_none_schema_returns_generic(self):
        assert classify_doc_type_hint(None, None) == "generic"

    def test_none_name_empty_schema_returns_generic(self):
        assert classify_doc_type_hint(None, {"type": "object", "properties": {}}) == "generic"


class TestGetDocTypeTemplate:
    def test_returns_invoice_template(self):
        t = get_doc_type_template("invoice")
        assert t["system_role"]
        assert "focus_areas" in t
        assert "extraction_hints" in t

    def test_returns_generic_for_unknown(self):
        t = get_doc_type_template("nonexistent_xyz")
        assert t is DOC_TYPE_TEMPLATES["generic"]

    def test_all_templates_have_required_fields(self):
        for name, template in DOC_TYPE_TEMPLATES.items():
            assert "system_role" in template, f"{name} missing system_role"
            assert "focus_areas" in template, f"{name} missing focus_areas"
            assert "extraction_hints" in template, f"{name} missing extraction_hints"


class TestEnrichSchemaDescriptions:
    @pytest.mark.asyncio
    async def test_adds_description_to_known_field(self, optimizer):
        schema = {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
            },
        }
        result = await optimizer.optimize_prompt(
            "Extract data", schema, schema_name="test"
        )
        assert result.enriched_schema is not None
        assert "description" in result.enriched_schema["properties"]["invoice_number"]

    @pytest.mark.asyncio
    async def test_preserves_existing_description(self, optimizer):
        schema = {
            "type": "object",
            "properties": {
                "custom_field": {"type": "string", "description": "My custom desc"},
            },
        }
        result = await optimizer.optimize_prompt(
            "Extract data", schema, schema_name="test"
        )
        assert result.enriched_schema["properties"]["custom_field"]["description"] == "My custom desc"

    @pytest.mark.asyncio
    async def test_unknown_field_gets_no_auto_description(self, optimizer):
        schema = {
            "type": "object",
            "properties": {
                "obscure_xyz_field": {"type": "string"},
            },
        }
        result = await optimizer.optimize_prompt(
            "Extract data", schema, schema_name="test"
        )
        assert "description" not in result.enriched_schema["properties"]["obscure_xyz_field"]

    @pytest.mark.asyncio
    async def test_none_schema_stays_none(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data", None, is_raw_output=True
        )
        assert result.enriched_schema is None


class TestBuildSystemPrompt:
    @pytest.mark.asyncio
    async def test_system_prompt_contains_role(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
            schema_name="invoice",
        )
        assert "invoice" in result.system_prompt.lower()
        assert "JSON" in result.system_prompt

    @pytest.mark.asyncio
    async def test_system_prompt_contains_rules(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
        )
        assert "null" in result.system_prompt
        assert "currency" in result.system_prompt.lower()


class TestXmlSandwich:
    @pytest.mark.asyncio
    async def test_contains_xml_tags(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
        )
        assert "<instructions>" in result.user_prompt
        assert "</instructions>" in result.user_prompt
        assert "<target_schema>" in result.user_prompt
        assert "</target_schema>" in result.user_prompt

    @pytest.mark.asyncio
    async def test_contains_extraction_guidance(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
        )
        assert "<extraction_guidance>" in result.user_prompt

    @pytest.mark.asyncio
    async def test_no_correction_hints_when_none(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
        )
        assert "<correction_hints>" not in result.user_prompt
        assert result.hints_injected is False


class TestChainOfThought:
    @pytest.mark.asyncio
    async def test_cot_triggered_for_handwritten(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
            doc_type="handwritten",
        )
        assert result.cot_enabled is True
        assert "<reasoning_instructions>" in result.user_prompt

    @pytest.mark.asyncio
    async def test_cot_triggered_for_low_quality(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
            quality_score=30.0,
        )
        assert result.cot_enabled is True

    @pytest.mark.asyncio
    async def test_cot_not_triggered_for_normal_quality(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
            quality_score=80.0,
        )
        assert result.cot_enabled is False


class TestRawOutputPrompt:
    @pytest.mark.asyncio
    async def test_raw_output_uses_transcription_role(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
            is_raw_output=True,
        )
        assert "transcription" in result.system_prompt.lower()
        assert result.enriched_schema is None

    @pytest.mark.asyncio
    async def test_raw_output_user_prompt_has_markdown_instruction(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            None,
            is_raw_output=True,
        )
        assert "Markdown" in result.user_prompt
        assert "JSON" not in result.user_prompt or "Do not wrap" in result.user_prompt

    @pytest.mark.asyncio
    async def test_raw_output_custom_prompt_preserved(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Custom user instruction here",
            None,
            is_raw_output=True,
        )
        assert "Custom user instruction here" in result.user_prompt

    @pytest.mark.asyncio
    async def test_raw_output_default_prompt_replaced(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract all information from this document",
            None,
            is_raw_output=True,
        )
        assert "high-fidelity Markdown" in result.user_prompt

    @pytest.mark.asyncio
    async def test_raw_output_cot_for_low_quality(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            None,
            is_raw_output=True,
            quality_score=25.0,
        )
        assert result.cot_enabled is True
        assert "document layout" in result.user_prompt.lower()

    @pytest.mark.asyncio
    async def test_transcription_mode_same_as_raw_output(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            None,
            is_transcription=True,
        )
        assert "transcription" in result.system_prompt.lower()


class TestPromptResultShape:
    @pytest.mark.asyncio
    async def test_structured_output_result(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"name": {"type": "string"}}},
            schema_name="test",
            provider="gemini",
            model="gemini-2.5-flash",
        )
        assert isinstance(result, PromptResult)
        assert isinstance(result.system_prompt, str)
        assert isinstance(result.user_prompt, str)
        assert isinstance(result.enriched_schema, dict)
        assert isinstance(result.doc_type_used, str)
        assert isinstance(result.cot_enabled, bool)
        assert isinstance(result.hints_injected, bool)

    @pytest.mark.asyncio
    async def test_doc_type_resolved_from_explicit_param(self, optimizer):
        result = await optimizer.optimize_prompt(
            "Extract data",
            {"type": "object", "properties": {"text": {"type": "string"}}},
            doc_type="receipt",
        )
        assert result.doc_type_used == "receipt"
        assert "retail" in result.system_prompt.lower() or "receipt" in result.system_prompt.lower()
