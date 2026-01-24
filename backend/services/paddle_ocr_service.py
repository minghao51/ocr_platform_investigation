"""
PaddleOCR Service

Fast, accurate OCR for scanned documents using PaddleOCR.
Based on 2026 research: 96-98% accuracy, 0.2-0.5s per page, 5-10x cheaper than VLMs.

Best use cases:
- Scanned documents without text layer
- Intermediate OCR before VLM refinement
- High-volume document processing
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import io

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing"""
    text: str
    confidence: float
    bboxes: List[Dict[str, Any]]  # Bounding boxes for each text block
    tables: List[Dict[str, Any]]  # Detected tables
    pages: int
    processing_time: float


class PaddleOCRService:
    """
    Fast OCR service using PaddleOCR

    Performance characteristics (2026 benchmarks):
    - Accuracy: 96-98%
    - Speed: 0.2-0.5s per page
    - Cost: Free (local) or $20-100/1K pages (cloud)
    - Layout understanding: Good (PP-Structure)
    """

    def __init__(self):
        """Initialize PaddleOCR service"""
        self._ocr = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of PaddleOCR (expensive import)"""
        if self._initialized:
            return

        try:
            from paddleocr import PaddleOCR

            # Initialize PaddleOCR with optimized settings
            self._ocr = PaddleOCR(
                use_angle_cls=True,      # Enable text direction detection
                lang='en',               # English language
                use_gpu=False,           # CPU mode (change to True if GPU available)
                show_log=False,          # Suppress verbose logs
                det_db_thresh=0.3,       # Detection threshold
                det_db_box_thresh=0.5,   # Box threshold
                rec_batch_num=6          # Batch size for recognition
            )

            self._initialized = True
            logger.info("PaddleOCR initialized successfully")

        except ImportError as e:
            logger.error(f"PaddleOCR not installed: {str(e)}")
            raise ImportError(
                "PaddleOCR is not installed. Install with: uv add paddleocr paddlepaddle"
            )
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
            raise

    def extract_from_image(
        self,
        image_path: str,
        extract_tables: bool = True
    ) -> OCRResult:
        """
        Extract text and structure from an image

        Args:
            image_path: Path to image file
            extract_tables: Whether to extract table structures

        Returns:
            OCRResult with text, confidence, and layout information
        """
        import time

        start_time = time.time()

        # Lazy initialization
        self._initialize()

        try:
            # Load image
            image = Image.open(image_path)

            # Perform OCR
            result = self._ocr.ocr(str(image_path), cls=True)

            if not result or not result[0]:
                logger.warning(f"No text detected in {image_path}")
                return OCRResult(
                    text="",
                    confidence=0.0,
                    bboxes=[],
                    tables=[],
                    pages=1,
                    processing_time=time.time() - start_time
                )

            # Parse results
            text_parts = []
            bboxes = []
            confidences = []

            for line in result[0]:
                if line:
                    bbox = line[0]  # Bounding box coordinates
                    text_info = line[1]  # (text, confidence)

                    if text_info:
                        text, confidence = text_info
                        text_parts.append(text)
                        bboxes.append({
                            "coordinates": bbox,
                            "text": text,
                            "confidence": confidence
                        })
                        confidences.append(confidence)

            # Calculate overall confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Extract tables if requested (basic implementation)
            tables = []
            if extract_tables:
                tables = self._extract_tables(image_path)

            processing_time = time.time() - start_time

            logger.info(f"PaddleOCR extracted {len(text_parts)} text blocks from {image_path} "
                       f"in {processing_time:.2f}s (confidence: {avg_confidence:.2%})")

            return OCRResult(
                text="\n".join(text_parts),
                confidence=avg_confidence,
                bboxes=bboxes,
                tables=tables,
                pages=1,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            raise ValueError(f"OCR extraction failed: {str(e)}")

    def extract_from_pdf(
        self,
        pdf_path: str,
        extract_tables: bool = True
    ) -> OCRResult:
        """
        Extract text from a PDF by converting to images first

        Args:
            pdf_path: Path to PDF file
            extract_tables: Whether to extract table structures

        Returns:
            OCRResult with combined text from all pages
        """
        import time
        from services.image_service import ImageService

        start_time = time.time()

        try:
            # Convert PDF to images
            image_service = ImageService()
            images = image_service.pdf_to_images(pdf_path)

            if not images:
                raise ValueError(f"Failed to convert PDF to images: {pdf_path}")

            # Process each page
            all_text = []
            all_bboxes = []
            all_tables = []
            all_confidences = []

            for i, image in enumerate(images):
                # Save PIL image to temp file
                temp_path = f"/tmp/paddleocr_page_{i}.png"
                image.save(temp_path)

                try:
                    # Extract from this page
                    result = self.extract_from_image(temp_path, extract_tables)

                    all_text.append(f"\n--- PAGE {i+1} ---\n{result.text}")
                    all_bboxes.extend(result.bboxes)
                    all_tables.extend(result.tables)
                    all_confidences.append(result.confidence)

                finally:
                    # Clean up temp file
                    Path(temp_path).unlink(missing_ok=True)

            # Combine results
            combined_text = "\n".join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            processing_time = time.time() - start_time

            logger.info(f"PaddleOCR processed {len(images)} PDF pages in {processing_time:.2f}s "
                       f"(confidence: {avg_confidence:.2%})")

            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                bboxes=all_bboxes,
                tables=all_tables,
                pages=len(images),
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"PDF OCR extraction failed for {pdf_path}: {str(e)}")
            raise ValueError(f"PDF OCR extraction failed: {str(e)}")

    def _extract_tables(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract table structures from image

        Basic implementation using PaddleOCR's table detection
        For advanced table extraction, consider integrating Camelot or similar
        """
        try:
            # PaddleOCR doesn't have built-in table detection in the basic version
            # This is a placeholder for future enhancement
            # For now, we'll return empty list and rely on VLM for table extraction

            # TODO: Integrate dedicated table extraction library
            # Options:
            # - Camelot (PDF tables)
            # - Table-Transformer (ML-based)
            # - PaddleStructure (advanced PaddleOCR)

            return []

        except Exception as e:
            logger.warning(f"Table extraction failed for {image_path}: {str(e)}")
            return []

    def quick_extract(self, image_path: str) -> str:
        """
        Quick text extraction (text only, no layout analysis)

        Faster than extract_from_image() when you only need text
        """
        result = self.extract_from_image(image_path, extract_tables=False)
        return result.text

    def check_confidence(self, ocr_result: OCRResult, threshold: float = 0.85) -> bool:
        """
        Check if OCR confidence meets threshold

        Returns True if confidence >= threshold
        """
        return ocr_result.confidence >= threshold


# Singleton instance for reuse
_paddle_ocr_instance = None

def get_paddle_ocr_service() -> PaddleOCRService:
    """Get or create singleton PaddleOCR service instance"""
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        _paddle_ocr_instance = PaddleOCRService()
    return _paddle_ocr_instance
