import logging
from typing import Any, Dict, Optional

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
        from services.provider_utils import resolve_provider_api_key
        from services.openrouter import OpenRouterProvider
        from services.gemini import GeminiProvider
        from services.litellm_provider import LiteLLMProvider
        from services.schema_service import SchemaService

        text_service = TextExtractionService()
        extracted_text = text_service.extract_text_from_pdf(file_path)

        if not extracted_text:
            return {
                "success": False,
                "error": "This PDF appears to be image-based. Please use the Vision Extraction tab instead.",
            }

        api_key = resolve_provider_api_key(provider_name)
        if not api_key:
            raise ValueError(f"No API key configured for {provider_name}")

        providers = {
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
            "litellm": LiteLLMProvider,
        }
        provider_class = providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        temperature = kwargs.get("temperature", 0.1)
        max_tokens = kwargs.get("max_tokens", 8192)

        async with provider_class(api_key) as provider:
            result = await provider.process_text(
                text=extracted_text,
                prompt=prompt,
                schema_definition=schema_definition,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if "error" in result:
            return {
                "success": False,
                "error": f"Provider error: {result['error']}",
                "raw_response": result,
            }

        content = result.get("content") or "{}"
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
