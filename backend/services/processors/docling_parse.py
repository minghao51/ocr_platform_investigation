import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from services.chunking_service import MarkdownSplitter
from services.docling_service import DoclingService
from services.processing_utils import parse_and_validate_response
from services.processors.base import Processor

logger = logging.getLogger(__name__)

CHUNK_THRESHOLD_RATIO = 0.8


class DoclingParseProcessor(Processor):
    def __init__(self, docling_parse_timeout_seconds: int = 30):
        self.chunking_service = MarkdownSplitter()
        self.docling_service = DoclingService()
        self.docling_parse_timeout_seconds = max(1, int(docling_parse_timeout_seconds))

    def _validate_file_size(self, file_path: str) -> None:
        from config import get_settings

        max_size = get_settings().max_file_size
        size = Path(file_path).stat().st_size
        if size > max_size:
            raise ValueError(
                f"File too large ({size / 1024 / 1024:.1f}MB). Max: {max_size / 1024 / 1024}MB"
            )

    def _extract_markdown_with_pymupdf(self, file_path: str) -> str:
        import fitz

        doc = fitz.open(file_path)
        try:
            parts = []
            for i, page in enumerate(doc, start=1):
                try:
                    page_markdown = page.get_text("markdown").strip()
                except Exception:
                    page_markdown = ""
                if not page_markdown:
                    page_markdown = page.get_text("text").strip()
                if page_markdown:
                    parts.append(f"\n\n--- PAGE {i} ---\n\n{page_markdown}")
            if not parts:
                raise ValueError("No text extracted from PDF via PyMuPDF")
            return "".join(parts)
        finally:
            doc.close()

    async def _parse_with_timeout(self, file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()
        parser = (
            self._extract_markdown_with_pymupdf
            if suffix == ".pdf"
            else self.docling_service.parse_document
        )
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(parser, file_path),
                timeout=self.docling_parse_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.error(
                "Parse timed out after %ss for %s",
                self.docling_parse_timeout_seconds,
                file_path,
            )
            raise TimeoutError(
                f"Parsing timed out after {self.docling_parse_timeout_seconds}s"
            ) from exc

    def _should_chunk(self, text: str, model: str) -> bool:
        context_windows = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gemini-2.0-flash": 1000000,
        }
        max_tokens = context_windows.get(model, 128000)
        threshold = int(max_tokens * CHUNK_THRESHOLD_RATIO)
        return self.chunking_service.count_tokens(text) > threshold

    async def _process_chunked_document(
        self,
        markdown_content: str,
        provider,
        model: str,
        schema_definition: Optional[Dict[str, Any]],
        prompt: str,
        job_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            if schema_definition is None:
                return {
                    "success": False,
                    "error": "Raw output is not supported for chunked document processing.",
                }

            chunks = self.chunking_service.split(markdown_content)

            if not chunks:
                return {
                    "success": False,
                    "error": "Failed to split document into chunks",
                }

            results = []
            errors = []

            system_prompt = kwargs.pop("system_prompt", None)

            for i, chunk in enumerate(chunks):
                chunk_prompt = (
                    f"{prompt}\n\n"
                    f"<chunk_context>This is chunk {i + 1} of {len(chunks)} "
                    f"from a larger document. Extract all relevant data from this chunk. "
                    f"If this is not the first chunk, continue from where the previous chunk left off. "
                    f"Do not repeat data already likely extracted from earlier chunks.</chunk_context>"
                )

                try:
                    chunk_kwargs = {**kwargs}
                    if system_prompt:
                        chunk_kwargs["system_prompt"] = system_prompt

                    result = await provider.process_text(
                        text=chunk,
                        prompt=chunk_prompt,
                        schema_definition=schema_definition,
                        model=model,
                        **chunk_kwargs,
                    )

                    if "error" in result:
                        errors.append(f"Chunk {i + 1}: {result['error']}")
                        continue

                    content = result.get("content") or "{}"
                    validation_result = parse_and_validate_response(
                        content, schema_definition
                    )

                    if validation_result["success"]:
                        results.append(validation_result["data"])
                    else:
                        errors.append(f"Chunk {i + 1}: {validation_result['error']}")

                except Exception as e:
                    errors.append(f"Chunk {i + 1}: {type(e).__name__}: {str(e)}")

            if not results:
                return {
                    "success": False,
                    "error": f"All chunks failed to process: {'; '.join(errors)}",
                    "errors": errors,
                }

            merged_data = {}
            merge_conflicts = []
            for result in results:
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key not in merged_data:
                            merged_data[key] = value
                        elif isinstance(value, list):
                            if isinstance(merged_data[key], list):
                                merged_data[key].extend(value)
                            else:
                                merged_data[key] = [merged_data[key]] + value
                        elif isinstance(value, dict) and isinstance(
                            merged_data.get(key), dict
                        ):
                            merged_data[key].update(value)
                        elif merged_data.get(key) is None and value is not None:
                            merged_data[key] = value
                        elif value is not None and merged_data.get(key) != value:
                            merge_conflicts.append(
                                {
                                    "field": key,
                                    "kept_value": merged_data.get(key),
                                    "discarded_value": value,
                                }
                            )

            return {
                "success": len(errors) == 0,
                "data": merged_data,
                "raw_response": {
                    "total_chunks": len(chunks),
                    "successful_chunks": len(results),
                    "failed_chunks": len(errors),
                    "chunk_results": results,
                },
                "errors": errors if errors else None,
                "metadata": {
                    "extraction_method": "docling-parse",
                    "chunked": True,
                    "total_chunks": len(chunks),
                    "successful_chunks": len(results),
                    "merge_conflict_count": len(merge_conflicts),
                    "merge_conflicts": merge_conflicts[:20],
                },
            }

        except Exception as e:
            logger.error("Chunk processing error: %s", e, exc_info=True)
            return {
                "success": False,
                "error": f"Chunk processing error: {type(e).__name__}: {str(e)}",
            }

    async def _run(
        self,
        file_path: str,
        provider,
        model: str,
        schema_definition: Optional[Dict[str, Any]],
        prompt: str,
        is_transcription: bool = False,
        job_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            self._validate_file_size(file_path)

            if is_transcription:
                try:
                    markdown_content = await self._parse_with_timeout(file_path)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Docling extraction failed: {str(e)}",
                        "metadata": {"extraction_method": "transcription"},
                    }

                return {
                    "success": True,
                    "data": {"text": markdown_content},
                    "metadata": {
                        "extraction_method": "transcription",
                        "chunked": False,
                    },
                }

            if schema_definition is None:
                try:
                    markdown_content = await self._parse_with_timeout(file_path)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Docling extraction failed: {str(e)}",
                        "metadata": {"extraction_method": "docling-parse"},
                    }

                return {
                    "success": True,
                    "data": {"text": markdown_content},
                    "metadata": {
                        "extraction_method": "docling-parse",
                        "chunked": False,
                        "raw_output": True,
                    },
                }

            try:
                markdown_content = await self._parse_with_timeout(file_path)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Docling extraction failed: {str(e)}",
                }

            if self._should_chunk(markdown_content, model):
                return await self._process_chunked_document(
                    markdown_content,
                    provider,
                    model,
                    schema_definition,
                    prompt,
                    job_id,
                    **kwargs,
                )

            result = await provider.process_text(
                text=markdown_content,
                prompt=prompt,
                schema_definition=schema_definition,
                model=model,
                **kwargs,
            )

            if "error" in result:
                return {
                    "success": False,
                    "error": f"Provider error: {result['error']}",
                    "raw_response": result,
                }

            content = result.get("content") or "{}"
            validation_result = parse_and_validate_response(
                content, schema_definition
            )

            if validation_result["success"]:
                return {
                    "success": True,
                    "data": validation_result["data"],
                    "raw_response": result,
                    "metadata": {
                        "extraction_method": "docling-parse",
                        "chunked": False,
                    },
                }
            else:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "raw_response": result,
                }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            error_type = type(e).__name__
            if "docling" in str(e).lower() or "Docling" in error_type:
                return {
                    "success": False,
                    "error": f"Docling error: {str(e)}",
                }
            return {
                "success": False,
                "error": f"Unexpected error: {type(e).__name__}: {str(e)}",
            }

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

        is_transcription = kwargs.pop("is_transcription", False)

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
            return await self._run(
                file_path,
                provider,
                model,
                schema_definition,
                prompt,
                is_transcription,
                job_id,
                **kwargs,
            )
