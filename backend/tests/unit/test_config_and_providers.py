import pytest
import yaml
from pathlib import Path
import time
from unittest.mock import AsyncMock, MagicMock

from config import Settings, get_settings
from services.processors.docling_parse import DoclingParseProcessor
from services.provider_utils import resolve_provider_api_key
from services import pricing


@pytest.fixture(autouse=True)
def _clear_pricing_cache():
    pricing.clear_cache()
    yield
    pricing.clear_cache()


def test_settings_ignore_encrypted_values():
    settings = Settings(
        openrouter_api_key="encrypted:abc123",
        max_file_size="encrypted:abc123",
        rate_limit_per_minute="encrypted:abc123",
        docling_parse_timeout_seconds="encrypted:abc123",
    )

    assert settings.openrouter_api_key == ""
    assert settings.max_file_size == 10 * 1024 * 1024
    assert settings.rate_limit_per_minute == 10
    assert settings.docling_parse_timeout_seconds == 60


def test_resolve_litellm_api_key_prefers_available_provider_key(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        assert resolve_provider_api_key("litellm") == "gemini-test-key"
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_docling_parse_transcription_returns_markdown_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    processor = DoclingParseProcessor()
    sample_file = tmp_path / "sample.docx"
    sample_file.write_bytes(b"PK\x03\x04minimal-docx")
    monkeypatch.setattr(
        processor.docling_service,
        "parse_document",
        lambda _file_path: "# Invoice\n\nTotal: 10.00",
    )
    mock_provider = MagicMock()
    mock_provider.process_text = AsyncMock(
        return_value={"content": "# Invoice\n\nTotal: 10.00"}
    )

    result = await processor._run(
        file_path=str(sample_file),
        provider=mock_provider,
        model="gemini-2.5-flash",
        schema_definition={},
        prompt="ignored",
        is_transcription=True,
    )

    assert result["success"] is True
    assert result["data"] == {"text": "# Invoice\n\nTotal: 10.00"}
    assert result["metadata"]["extraction_method"] == "transcription"


@pytest.mark.asyncio
async def test_docling_parse_returns_timeout_error_for_slow_parse(tmp_path):
    processor = DoclingParseProcessor(docling_parse_timeout_seconds=1)
    sample_file = tmp_path / "slow.docx"
    sample_file.write_bytes(b"PK\x03\x04slow-docx")

    def _slow_parse(_file_path):
        time.sleep(2)
        return "# Slow"

    processor.docling_service.parse_document = _slow_parse
    mock_provider = MagicMock()
    mock_provider.process_text = AsyncMock(return_value={"content": "# Slow"})

    result = await processor._run(
        file_path=str(sample_file),
        provider=mock_provider,
        model="gemini-2.5-flash",
        schema_definition={},
        prompt="ignored",
        is_transcription=True,
    )

    assert result["success"] is False
    assert "timed out after 1s" in result["error"]


def test_provider_yaml_models_have_required_fields():
    config_path = Path(__file__).resolve().parents[2] / "config" / "providers.yaml"
    config = yaml.safe_load(config_path.read_text())

    for provider in config.get("providers", []):
        for model in provider.get("models", []):
            assert "id" in model, f"Missing 'id' in {provider['name']}"
            assert "name" in model, (
                f"Missing 'name' in {provider['name']}/{model.get('id')}"
            )
            assert "tier" in model, (
                f"Missing 'tier' in {provider['name']}/{model.get('id')}"
            )
            if model.get("pricing") is not None:
                assert "input_per_1m" in model["pricing"], (
                    f"Missing pricing.input_per_1m in {model['id']}"
                )
                assert "output_per_1m" in model["pricing"], (
                    f"Missing pricing.output_per_1m in {model['id']}"
                )


def test_pymupdf_extractor_reads_pdf_text(tmp_path):
    import fitz

    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PyMuPDF parse route check")
    doc.save(str(pdf_path))
    doc.close()

    processor = DoclingParseProcessor()
    content = processor._extract_markdown_with_pymupdf(str(pdf_path))

    assert "PyMuPDF parse route check" in content
