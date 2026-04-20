import pytest

from config import Settings, get_settings
from services.processing import ProcessingService
from services.provider_utils import resolve_provider_api_key


def test_settings_ignore_encrypted_values():
    settings = Settings(
        openrouter_api_key="encrypted:abc123",
        max_file_size="encrypted:abc123",
        rate_limit_per_minute="encrypted:abc123",
    )

    assert settings.openrouter_api_key == ""
    assert settings.max_file_size == 10 * 1024 * 1024
    assert settings.rate_limit_per_minute == 10


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
    sample_file = tmp_path / "sample.pdf"
    sample_file.write_bytes(b"%PDF-1.4 test")
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
