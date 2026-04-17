import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Service for faithful text transcription.
    Produces clean Markdown instead of JSON extraction.
    """

    # Default prompt for transcription
    DEFAULT_PROMPT = """Convert this document to clean, well-structured Markdown.

Requirements:
- Preserve all headings and hierarchy
- Maintain table structure using Markdown tables
- Keep lists and formatting intact
- Preserve footnotes and references
- Do NOT add or remove information
- Do NOT convert to JSON

Return ONLY the Markdown, no additional commentary."""

    def __init__(self, prompt: Optional[str] = None):
        self.prompt = prompt or self.DEFAULT_PROMPT

    async def transcribe(
        self,
        markdown: str,
        provider,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 16384,
    ) -> str:
        """
        Transcribe document to clean Markdown.

        Args:
            markdown: Raw markdown from Docling
            provider: VLM provider instance
            model: Model name
            temperature: Generation temperature
            max_tokens: Max tokens to generate

        Returns:
            Cleaned Markdown text

        Raises:
            Exception: If provider call fails
        """
        try:
            result = await provider.process_text(
                text=markdown,
                prompt=self.prompt,
                schema_definition=None,  # No schema for transcription
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if "error" in result:
                raise Exception(f"Provider error: {result['error']}")

            content = result.get("content", "")

            if not content:
                raise Exception("Empty transcription result")

            return content

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
