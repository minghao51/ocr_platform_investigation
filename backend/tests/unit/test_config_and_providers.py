import pytest
import yaml
from pathlib import Path
import time

from config import Settings, get_settings
from services.gemini import GeminiProvider
from services.litellm_provider import LiteLLMProvider
from services.openrouter import OpenRouterProvider
from services.processing import ProcessingService
from services.provider_utils import resolve_provider_api_key


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
    service = ProcessingService()
    sample_file = tmp_path / "sample.docx"
    sample_file.write_bytes(b"PK\x03\x04minimal-docx")
    monkeypatch.setattr(
        service.docling_service,
        "parse_document",
        lambda _file_path: "# Invoice\n\nTotal: 10.00",
    )

    result = await service._process_via_docling_parse(
        file_path=str(sample_file),
        provider=None,
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
    service = ProcessingService()
    service.docling_parse_timeout_seconds = 1
    sample_file = tmp_path / "slow.docx"
    sample_file.write_bytes(b"PK\x03\x04slow-docx")

    def _slow_parse(_file_path):
        time.sleep(2)
        return "# Slow"

    service.docling_service.parse_document = _slow_parse

    result = await service._process_via_docling_parse(
        file_path=str(sample_file),
        provider=None,
        model="gemini-2.5-flash",
        schema_definition={},
        prompt="ignored",
        is_transcription=True,
    )

    assert result["success"] is False
    assert "timed out after 1s" in result["error"]


def test_provider_yaml_models_are_subset_of_runtime_models():
    config_path = Path(__file__).resolve().parents[2] / "config" / "providers.yaml"
    config = yaml.safe_load(config_path.read_text())

    runtime_model_ids = {
        "openrouter": {
            model["id"] for model in OpenRouterProvider("test-key").get_models()
        },
        "gemini": {model["id"] for model in GeminiProvider("test-key").get_models()},
        "litellm": {
            model["id"] for model in LiteLLMProvider("test-key").get_models()
        },
    }

    for provider in config.get("providers", []):
        provider_name = provider["name"]
        if provider_name == "docling":
            continue
        configured_model_ids = {model["id"] for model in provider.get("models", [])}
        assert configured_model_ids <= runtime_model_ids[provider_name]


def test_pymupdf_extractor_reads_pdf_text(tmp_path):
    import fitz

    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PyMuPDF parse route check")
    doc.save(str(pdf_path))
    doc.close()

    service = ProcessingService()
    content = service._extract_markdown_with_pymupdf(str(pdf_path))

    assert "PyMuPDF parse route check" in content
