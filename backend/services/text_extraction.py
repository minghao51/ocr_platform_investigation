import pdfplumber
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TextExtractionService:
    """Extract text from PDFs using pdfplumber"""

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from all pages of a PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            Concatenated text with page markers, or None if no text found

        Raises:
            ValueError: If PDF cannot be read
        """
        try:
            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()

                    if page_text and page_text.strip():
                        text_parts.append(f"\n\n--- PAGE {i} ---\n\n")
                        text_parts.append(page_text)

            if not text_parts:
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                return None

            return "".join(text_parts)

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
