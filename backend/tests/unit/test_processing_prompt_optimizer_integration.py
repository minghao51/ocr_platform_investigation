from unittest.mock import AsyncMock

import pytest

from services.prompt_optimizer import PromptOptimizer, PromptResult
from services import processing


@pytest.mark.asyncio
async def test_optimizer_fetches_hints_with_processing_method(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    async def _fake_list_prompt_learning_entries(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        "database.crud.list_prompt_learning_entries",
        _fake_list_prompt_learning_entries,
    )

    optimizer = PromptOptimizer()
    await optimizer.optimize_prompt(
        prompt="Extract data",
        schema_definition={"type": "object", "properties": {"text": {"type": "string"}}},
        schema_name="Generic",
        provider="gemini",
        model="gemini-2.5-flash",
        processing_method="text",
    )

    assert captured["processing_method"] == "text"
    assert captured["schema_name"] == "Generic"


@pytest.mark.asyncio
async def test_run_processing_job_uses_optimized_prompt_and_records_failures(
    monkeypatch: pytest.MonkeyPatch,
):
    job = {
        "id": 1,
        "file_type": "image",
        "schema_id": None,
        "schema_name": "Generic",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "processing_method": "vision",
    }

    monkeypatch.setattr(processing.crud, "get_job", AsyncMock(return_value=job))
    update_status = AsyncMock()
    monkeypatch.setattr(processing, "update_job_status_with_broadcast", update_status)

    metadata_updates = []

    async def _fake_update_job_metadata(job_id, metadata):
        metadata_updates.append((job_id, metadata))

    monkeypatch.setattr(processing.crud, "update_job_metadata", _fake_update_job_metadata)

    def _fail_load_image(_path):
        raise RuntimeError("image load failed")

    monkeypatch.setattr(processing.ImageService, "load_image", staticmethod(_fail_load_image))

    class _FakeOptimizer:
        async def optimize_prompt(self, **kwargs):
            return PromptResult(
                system_prompt="SYSTEM",
                user_prompt="USER",
                enriched_schema={"type": "object", "properties": {"name": {"type": "string"}}},
                doc_type_used="generic",
                cot_enabled=False,
                hints_injected=False,
            )

    monkeypatch.setattr(processing, "PromptOptimizer", _FakeOptimizer)

    captured = {}

    class _FakeProcessingService:
        def __init__(self, **_kwargs):
            pass

        async def process_file(self, **kwargs):
            captured.update(kwargs)
            return {"success": True, "data": {"name": "ok"}, "raw_response": {"usage": {}}}

    monkeypatch.setattr(processing, "ProcessingService", _FakeProcessingService)

    await processing.run_processing_job(job_id=1, file_path="/tmp/fake.png")

    assert captured["prompt"] == "USER"
    assert captured["schema_definition"]["properties"]["name"]["type"] == "string"
    assert captured["system_prompt"] == "SYSTEM"

    first_metadata = metadata_updates[0][1]["prompt_optimization"]
    assert first_metadata["quality_assessment_failed"] is True
    assert first_metadata["document_classification_failed"] is False


@pytest.mark.asyncio
async def test_run_text_processing_job_passes_system_prompt(monkeypatch: pytest.MonkeyPatch):
    job = {
        "id": 2,
        "file_type": "pdf",
        "schema_id": None,
        "schema_name": "Generic",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
    }

    monkeypatch.setattr(processing.crud, "get_job", AsyncMock(return_value=job))
    monkeypatch.setattr(processing, "update_job_status_with_broadcast", AsyncMock())
    monkeypatch.setattr(processing, "resolve_provider_api_key", lambda _provider: "test-key")

    class _FakeOptimizer:
        async def optimize_prompt(self, **kwargs):
            return PromptResult(
                system_prompt="TEXT_SYSTEM",
                user_prompt="TEXT_USER",
                enriched_schema={"type": "object", "properties": {"value": {"type": "string"}}},
            )

    monkeypatch.setattr(processing, "PromptOptimizer", _FakeOptimizer)

    captured = {}

    class _FakeTextProcessor:
        async def process(self, **kwargs):
            captured.update(kwargs)
            return {"success": True, "data": {"value": "ok"}, "raw_response": {"usage": {}}}

    monkeypatch.setattr("services.processors.text.TextProcessor", _FakeTextProcessor)

    await processing.run_text_processing_job(job_id=2, file_path="/tmp/fake.pdf")

    assert captured["prompt"] == "TEXT_USER"
    assert captured["system_prompt"] == "TEXT_SYSTEM"
    assert captured["schema_definition"]["properties"]["value"]["type"] == "string"
