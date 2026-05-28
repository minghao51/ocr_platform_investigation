import pytest
from services.processing import ProcessingOrchestrator


class TestProcessingOrchestratorInit:
    def test_defaults(self):
        orch = ProcessingOrchestrator()
        assert orch.quality_threshold == 40.0
        assert orch.auto_preprocess is True

    def test_custom_values(self):
        orch = ProcessingOrchestrator(
            quality_threshold=80.0, auto_preprocess=False, skip_quality=True
        )
        assert orch.quality_threshold == 80.0
        assert orch.auto_preprocess is False
        assert orch.skip_quality is True


class TestProcessingOrchestratorValidateFileSize:
    def test_raises_on_large_file(self, tmp_path):
        orch = ProcessingOrchestrator()
        large = tmp_path / "big.pdf"
        large.write_bytes(b"x" * (11 * 1024 * 1024))
        with pytest.raises(ValueError, match="File size|exceeds"):
            orch._validate_file_size(str(large))

    def test_passes_on_small_file(self, tmp_path):
        orch = ProcessingOrchestrator()
        small = tmp_path / "small.pdf"
        small.write_bytes(b"small")
        orch._validate_file_size(str(small))


class TestProcessingOrchestratorShouldChunk:
    def test_short_text_does_not_chunk(self):
        orch = ProcessingOrchestrator()
        assert orch._should_chunk("short", "gpt-4o") is False

    def test_long_text_does_chunk(self):
        orch = ProcessingOrchestrator()
        long_text = "word " * 200000
        assert orch._should_chunk(long_text, "gpt-4o") is True


class TestProcessingOrchestratorResolveSchema:
    @pytest.mark.asyncio
    async def test_raw_output_returns_none(self):
        orch = ProcessingOrchestrator()
        result = await orch.resolve_schema({}, raw_output=True)
        assert result is None

    @pytest.mark.asyncio
    async def test_schema_override(self):
        orch = ProcessingOrchestrator()
        override = {"type": "object", "properties": {"x": {"type": "string"}}}
        result = await orch.resolve_schema({}, schema_definition_override=override)
        assert result == override

    @pytest.mark.asyncio
    async def test_returns_generic_when_no_schema(self):
        orch = ProcessingOrchestrator()
        result = await orch.resolve_schema({})
        assert result is not None
        assert result["type"] == "object"
