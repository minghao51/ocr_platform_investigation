import logging
from typing import Any, Dict, Optional

from services.processors.base import Processor
from services.processors.docling_parse import DoclingParseProcessor
from services.processors.docling_extract import DoclingExtractProcessor
from services.processors.vision import VisionProcessor
from services.processors.text import TextProcessor

logger = logging.getLogger(__name__)


class ProcessorFactory:
    def __init__(
        self,
        quality_threshold: float = 40.0,
        auto_preprocess: bool = True,
        skip_quality: bool = False,
        docling_parse_timeout_seconds: int = 30,
    ):
        self.quality_threshold = quality_threshold
        self.auto_preprocess = auto_preprocess
        self.skip_quality = skip_quality
        self.docling_parse_timeout_seconds = docling_parse_timeout_seconds

    def get_processor(self, extraction_method: str, file_type: str) -> Processor:
        if extraction_method == "docling-parse":
            return DoclingParseProcessor(
                docling_parse_timeout_seconds=self.docling_parse_timeout_seconds
            )
        elif extraction_method == "docling-extract":
            return DoclingExtractProcessor()
        elif extraction_method == "hybrid" and file_type == "pdf":
            return _HybridProcessor()
        elif extraction_method == "text":
            return TextProcessor()
        else:
            return VisionProcessor(
                quality_threshold=self.quality_threshold,
                auto_preprocess=self.auto_preprocess,
                skip_quality=self.skip_quality,
            )


class _HybridProcessor(Processor):
    def __init__(self):
        from services.hybrid_processing import HybridProcessingService

        self.hybrid_service = HybridProcessingService()

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
        from services.provider_utils import resolve_provider_api_key
        from services.openrouter import OpenRouterProvider
        from services.gemini import GeminiProvider
        from services.litellm_provider import LiteLLMProvider

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

        async with provider_class(api_key) as provider:
            return await self.hybrid_service.process_pdf(
                file_path, provider, model, schema_definition, prompt, **kwargs
            )
