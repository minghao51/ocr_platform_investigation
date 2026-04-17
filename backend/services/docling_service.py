"""
Docling Service - CPU-optimized document parsing service.

This service provides intelligent document parsing using Docling with:
- Smart OCR detection (only OCR when needed)
- CPU-optimized configuration
- Format-specific pipelines
- Batch processing support
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    TableFormerMode,
    TableStructureOptions,
    ThreadedPdfPipelineOptions,
)
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
    PowerpointFormatOption,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
import pypdfium2

logger = logging.getLogger(__name__)


class DoclingError(Exception):
    """Raised when Docling fails to parse a document"""

    pass


class DoclingService:
    """
    CPU-optimized document parsing service using Docling.

    Features:
    - Smart OCR detection (only OCR non-searchable PDFs)
    - Format-specific pipelines (StandardPdfPipeline for PDF, SimplePipeline for Office docs)
    - CPU-optimized settings (PyPdfium backend, appropriate batch sizes)
    - Page range support for chunking
    - Batch processing helper
    """

    def __init__(self, disable_ocr: bool = False):
        """
        Initialize DoclingService with CPU-optimized configuration.

        Args:
            disable_ocr: If True, disable OCR (useful for testing without OCR dependencies)
        """
        self.disable_ocr = disable_ocr
        self.converter = self._create_converter()

    def _create_converter(self) -> DocumentConverter:
        """
        Create a DocumentConverter with CPU-optimized settings.

        Returns:
            DocumentConverter: Configured converter instance
        """
        # Threaded pipeline with CPU batch sizes
        pipeline_options = ThreadedPdfPipelineOptions()
        pipeline_options.ocr_batch_size = 16  # CPU: 16-32, GPU: 64+
        pipeline_options.layout_batch_size = 16  # CPU: 16-32, GPU: 64+
        pipeline_options.table_batch_size = 2  # CPU: 2-4, GPU: 4-8
        pipeline_options.images_scale = 1.0  # 72 DPI, prevent memory growth

        # Table structure: use FAST mode for CPU
        pipeline_options.table_structure_options = TableStructureOptions(
            do_cell_matching=True,
            mode=TableFormerMode.FAST,  # FAST for CPU, ACCURATE for GPU
        )

        # EasyOCR configuration (CPU mode)
        if not self.disable_ocr:
            pipeline_options.ocr_options = EasyOcrOptions(
                lang=["en"],
                use_gpu=False,  # CPU mode
                confidence_threshold=0.5,
            )

        # Create converter with format-specific pipelines
        converter = DocumentConverter(
            format_options={
                # PDF: Use PyPdfium backend with Standard pipeline
                InputFormat.PDF: PdfFormatOption(
                    backend=PyPdfiumDocumentBackend,
                    pipeline_cls=StandardPdfPipeline,
                    pipeline_options=pipeline_options,
                ),
                # DOCX/PPTX: Use Simple pipeline (no OCR needed)
                InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
                InputFormat.PPTX: PowerpointFormatOption(pipeline_cls=SimplePipeline),
            }
        )

        return converter

    def _is_text_searchable(self, file_path: str) -> bool:
        """
        Detect if a PDF is text-searchable.

        Args:
            file_path: Path to the PDF file

        Returns:
            bool: True if PDF has extractable text, False otherwise
        """
        try:
            doc = pypdfium2.PdfDocument(file_path)
            if len(doc) == 0:
                return False

            # Check first page for text
            page = doc[0]
            text_page = page.get_textpage()
            text = text_page.get_text_range().strip()
            return bool(text)
        except Exception as e:
            logger.warning(f"Error checking if PDF is text-searchable: {e}")
            return False

    def parse_document(
        self,
        file_path: str,
        page_range: Optional[Tuple[int, int]] = None,
        force_ocr: bool = False,
    ) -> str:
        """
        Parse a document and return its content as markdown.

        Args:
            file_path: Path to the document file
            page_range: Optional tuple (start, end) for page range (0-indexed, exclusive)
            force_ocr: Force OCR even for text-searchable PDFs

        Returns:
            str: Document content in markdown format

        Raises:
            Exception: If document parsing fails
        """
        try:
            # Determine if OCR is needed
            is_searchable = self._is_text_searchable(file_path)
            do_ocr = (force_ocr or not is_searchable) and not self.disable_ocr

            logger.info(f"Parsing document: {file_path} (OCR: {do_ocr})")

            # Configure pipeline options based on OCR detection
            if hasattr(self.converter, "format_options"):
                pdf_options = self.converter.format_options.get(InputFormat.PDF)
                if pdf_options and hasattr(pdf_options, "pipeline_options"):
                    pdf_options.pipeline_options.do_ocr = do_ocr

            # Parse document with optional page range
            if page_range:
                start, end = page_range
                doc = self.converter.convert(file_path, page_range=(start, end))
            else:
                doc = self.converter.convert(file_path)

            # Export to markdown
            markdown_content = doc.document.export_to_markdown()

            logger.info(f"Successfully parsed document: {file_path}")
            return markdown_content

        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            raise

    def parse_documents_batch(
        self,
        file_paths: List[str],
        max_file_size: int = 50 * 1024 * 1024,  # 50MB default
    ) -> List[str]:
        """
        Parse multiple documents in batch.

        Args:
            file_paths: List of document file paths
            max_file_size: Maximum file size in bytes (default 50MB)

        Returns:
            List[str]: List of markdown contents (None for failed documents)
        """
        results: list[Optional[str]] = []

        for file_path in file_paths:
            try:
                # Check file size
                file_size = Path(file_path).stat().st_size
                if file_size > max_file_size:
                    logger.warning(f"File too large: {file_path} ({file_size} bytes)")
                    results.append(None)
                    continue

                result = self.parse_document(file_path)
                results.append(result)

            except Exception as e:
                logger.error(f"Error parsing document {file_path}: {e}")
                results.append(None)

        return results  # type: ignore[return-value]
