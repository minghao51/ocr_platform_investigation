import asyncio
import logging
from typing import Any, Dict, Optional

from services.provider_catalog import create_provider
from services.processing_utils import parse_and_validate_response
from services.processors.base import Processor

logger = logging.getLogger(__name__)


class TextProcessor(Processor):
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
        from services.text_extraction import TextExtractionService
        from services.schema_service import SchemaService

        text_service = TextExtractionService()
        extracted_text = await asyncio.to_thread(
            text_service.extract_text_from_pdf, file_path
        )

        if not extracted_text:
            return {
                "success": False,
                "error": "This PDF appears to be image-based. Please use the Vision Extraction tab instead.",
            }

        temperature = kwargs.get("temperature", 0.1)
        max_tokens = kwargs.get("max_tokens", 8192)
        system_prompt = kwargs.pop("system_prompt", None)

        provider = create_provider(provider_name)

        async with provider:
            provider_kwargs: dict = {
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if system_prompt:
                provider_kwargs["system_prompt"] = system_prompt

            result = await provider.process_text(
                text=extracted_text,
                prompt=prompt,
                schema_definition=schema_definition,
                model=model,
                **provider_kwargs,
            )

        if result.error is not None:
            return {
                "success": False,
                "error": f"Provider error: {result.error}",
                "raw_response": result,
            }

        content = result.content or "{}"
        if schema_definition is None:
            return {
                "success": True,
                "data": {"text": content},
                "raw_response": result,
            }

        schema_service = SchemaService()
        validation_result = parse_and_validate_response(
            content, schema_definition, schema_service
        )

        if validation_result["success"]:
            return {
                "success": True,
                "data": validation_result["data"],
                "raw_response": result,
            }
        else:
            return {
                "success": False,
                "error": validation_result["error"],
                "raw_response": result,
            }
