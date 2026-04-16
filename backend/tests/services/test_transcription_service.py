import pytest
from unittest.mock import MagicMock, AsyncMock
from services.transcription_service import TranscriptionService

@pytest.mark.asyncio
async def test_transcribe_basic():
    # Mock provider
    mock_provider = MagicMock()
    mock_provider.process_text = AsyncMock(return_value={
        "content": "Cleaned markdown text",
        "usage": {"total_tokens": 100}
    })

    service = TranscriptionService()
    result = await service.transcribe("Raw markdown", mock_provider, "gpt-4o")

    assert "Cleaned markdown text" in result
    mock_provider.process_text.assert_called_once()

@pytest.mark.asyncio
async def test_transcription_prompt_format():
    mock_provider = MagicMock()
    mock_provider.process_text = AsyncMock(return_value={"content": "# Result"})

    service = TranscriptionService()
    await service.transcribe("Input", mock_provider, "gpt-4o")

    # Verify prompt was passed correctly
    call_args = mock_provider.process_text.call_args
    prompt = call_args.kwargs.get("prompt") or call_args[1].get("prompt")
    assert "faithful" in prompt.lower() or "preserve" in prompt.lower()
