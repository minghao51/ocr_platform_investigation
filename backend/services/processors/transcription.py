from typing import Any, Dict, Optional

from services.processors.base import Processor
from services.processors.docling_parse import DoclingParseProcessor
from services.provider_catalog import create_provider


class TranscriptionProcessor(Processor):
    def __init__(self, docling_parse_timeout_seconds: int = 30):
        self.docling_parse_processor = DoclingParseProcessor(
            docling_parse_timeout_seconds=docling_parse_timeout_seconds
        )

    async def process(
        self,
        job_id: Optional[int],
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition: Optional[Dict[str, Any]],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        _ = schema_definition
        kwargs.pop("is_transcription", None)

        provider = create_provider(provider_name)
        async with provider:
            return await self.docling_parse_processor._run(
                file_path=file_path,
                provider=provider,
                model=model,
                schema_definition=None,
                prompt=prompt,
                is_transcription=True,
                job_id=job_id,
                **kwargs,
            )
