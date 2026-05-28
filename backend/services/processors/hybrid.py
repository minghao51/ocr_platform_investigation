import asyncio
import json
import time
from typing import Any, Dict, List
import logging

import fitz
from PIL import Image, ImageOps

from services.image_service import ImageService
from services.processing_utils import parse_and_validate_response
from services.processors.base import Processor

logger = logging.getLogger(__name__)


class HybridProcessor(Processor):
    """Hybrid extraction using text/layout context plus a visual contact sheet."""

    def __init__(self) -> None:
        self.image_service = ImageService()

    def _extract_layout_context(self, pdf_path: str) -> Dict[str, Any]:
        start = time.time()
        doc = fitz.open(pdf_path)
        pages: List[Dict[str, Any]] = []
        complex_pages: List[int] = []

        try:
            for page_index, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                text_blocks = []
                block_dict = page.get_text("dict")
                for block in block_dict.get("blocks", [])[:25]:
                    if block.get("type") != 0:
                        continue
                    block_text_parts = []
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("text"):
                                block_text_parts.append(span["text"])
                    block_text = " ".join(block_text_parts).strip()
                    if not block_text:
                        continue
                    text_blocks.append(
                        {
                            "bbox": [
                                round(value, 1) for value in block.get("bbox", [])
                            ],
                            "text": block_text[:400],
                        }
                    )

                images = page.get_images()
                tables = list(page.find_tables())
                is_complex = len(text_blocks) > 8 or len(images) > 0 or len(tables) > 0
                if is_complex:
                    complex_pages.append(page_index)

                pages.append(
                    {
                        "page_number": page_index,
                        "text_length": len(text),
                        "text_preview": text[:1200],
                        "block_count": len(text_blocks),
                        "blocks": text_blocks,
                        "image_count": len(images),
                        "table_count": len(tables),
                        "is_complex": is_complex,
                    }
                )
        finally:
            doc.close()

        return {
            "pages": pages,
            "complex_pages": complex_pages,
            "timing_seconds": round(time.time() - start, 4),
        }

    def _build_contact_sheet(self, pdf_path: str, max_pages: int = 4) -> Image.Image:
        page_images = self.image_service.pdf_to_images(
            pdf_path, dpi=150, first_page=1, last_page=max_pages
        )
        normalized: List[Image.Image] = []
        widths: List[int] = []
        heights: List[int] = []

        for page_image in page_images:
            rgb_image = page_image.convert("RGB")
            resized = ImageOps.contain(rgb_image, (900, 1200))
            normalized.append(resized)
            widths.append(resized.width)
            heights.append(resized.height)

        canvas_width = max(widths) if widths else 900
        canvas_height = sum(heights) + (20 * max(len(normalized) - 1, 0))
        canvas = Image.new("RGB", (canvas_width, canvas_height or 1200), "white")

        offset_y = 0
        for image in normalized:
            canvas.paste(image, ((canvas_width - image.width) // 2, offset_y))
            offset_y += image.height + 20

        return canvas

    def _build_prompt(
        self,
        base_prompt: str,
        layout_context: Dict[str, Any],
        schema_definition: Dict[str, Any],
    ) -> str:
        compact_pages = [
            {
                "page_number": page["page_number"],
                "text_preview": page["text_preview"][:600],
                "block_count": page["block_count"],
                "image_count": page["image_count"],
                "table_count": page["table_count"],
                "blocks": page["blocks"][:8],
            }
            for page in layout_context["pages"]
        ]
        return (
            f"{base_prompt}\n\n"
            "<hybrid_context>\n"
            "This is a hybrid OCR extraction task. Combine the provided visual page "
            "contact sheet with the OCR/layout notes below.\n"
            "Use visual structure to resolve ambiguities, preserve row/section "
            "relationships, and prefer text/layout evidence when values conflict.\n"
            "</hybrid_context>\n\n"
            f"<layout_data>\n{json.dumps(compact_pages, indent=2)}\n</layout_data>"
        )

    async def process_pdf(
        self,
        pdf_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        layout_context = await asyncio.to_thread(self._extract_layout_context, pdf_path)
        contact_sheet = await asyncio.to_thread(self._build_contact_sheet, pdf_path)
        hybrid_prompt = self._build_prompt(prompt, layout_context, schema_definition)

        vision_start = time.time()
        result = await provider.process_image(
            contact_sheet,
            hybrid_prompt,
            schema_definition,
            model,
            **kwargs,
        )
        vision_timing = round(time.time() - vision_start, 4)

        if "error" in result:
            return {
                "success": False,
                "error": f"Provider error: {result['error']}",
                "raw_response": result,
                "metadata": {
                    "hybrid": {
                        "layout_pages": len(layout_context["pages"]),
                        "complex_pages": layout_context["complex_pages"],
                        "timings": {
                            "layout_seconds": layout_context["timing_seconds"],
                            "vision_seconds": vision_timing,
                        },
                    }
                },
            }

        validation_result = parse_and_validate_response(
            result.get("content", "{}"), schema_definition
        )
        metadata = {
            "hybrid": {
                "layout_pages": len(layout_context["pages"]),
                "complex_pages": layout_context["complex_pages"],
                "timings": {
                    "layout_seconds": layout_context["timing_seconds"],
                    "vision_seconds": vision_timing,
                },
                "page_diagnostics": [
                    {
                        "page_number": page["page_number"],
                        "block_count": page["block_count"],
                        "image_count": page["image_count"],
                        "table_count": page["table_count"],
                        "is_complex": page["is_complex"],
                    }
                    for page in layout_context["pages"]
                ],
            }
        }

        if validation_result["success"]:
            return {
                "success": True,
                "data": validation_result["data"],
                "raw_response": result,
                "metadata": metadata,
            }

        return {
            "success": False,
            "error": validation_result["error"],
            "raw_response": result,
            "metadata": metadata,
        }

    async def process(
        self,
        job_id,
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition,
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        from services.provider_utils import resolve_provider_api_key
        from services.provider_catalog import get_provider

        api_key = resolve_provider_api_key(provider_name)
        if not api_key:
            raise ValueError(f"No API key configured for {provider_name}")

        provider = await get_provider(provider_name, api_key)

        async with provider:
            return await self.process_pdf(
                file_path, provider, model, schema_definition, prompt, **kwargs
            )
