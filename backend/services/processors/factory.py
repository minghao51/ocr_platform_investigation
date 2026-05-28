import logging

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
            from services.processors.hybrid import HybridProcessor

            return HybridProcessor()
        elif extraction_method == "text":
            return TextProcessor()
        else:
            return VisionProcessor(
                quality_threshold=self.quality_threshold,
                auto_preprocess=self.auto_preprocess,
                skip_quality=self.skip_quality,
            )
