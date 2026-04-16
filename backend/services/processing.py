import time
import json
from typing import Dict, Any, Optional, Type
from pathlib import Path
from config import get_settings
from services.vlm_provider import VLMProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.image_service import ImageService
from services.schema_service import SchemaService
from services.quality_gate import QualityGate
from services.image_preprocessor import ImagePreprocessor
from services.hybrid_processing import HybridProcessingService
from services.docling_service import DoclingService
from services.chunking_service import MarkdownSplitter
from services.transcription_service import TranscriptionService
from database import crud

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
CHUNK_THRESHOLD_RATIO = 0.8

settings = get_settings()


def parse_and_validate_response(
    content: str,
    schema_definition: Dict[str, Any],
    schema_service: Optional[SchemaService] = None,
) -> Dict[str, Any]:
    """
    Parse JSON content and validate against schema.
    Returns a dict with success status and either data/error.
    """
    if schema_service is None:
        schema_service = SchemaService()

    try:
        data = json.loads(content)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass

        is_valid, validated_data, error = schema_service.validate_data(
            data, schema_definition
        )

        if is_valid:
            return {"success": True, "data": validated_data}
        else:
            return {"success": False, "error": f"Validation failed: {error}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON response: {str(e)}"}


async def update_job_status_with_broadcast(
    job_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None,
    usage: Optional[Dict[str, Any]] = None,
):
    """
    Update job status in database and broadcast via WebSocket.

    This function combines the database update with WebSocket notification
    to keep all connected clients informed of job progress.
    """
    job = await crud.update_job_status(
        job_id,
        status,
        result=result,
        error_message=error_message,
        processing_time=processing_time,
        usage=usage,
    )

    # Broadcast update via WebSocket if job was found
    if job:
        try:
            # Import here to avoid circular dependency
            from routers.websocket import broadcast_job_update

            await broadcast_job_update(job_id, job)
        except Exception as e:
            # Log but don't fail - WebSocket is optional
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to broadcast job update via WebSocket: {e}")

    return job


class ProcessingService:
    """Main processing pipeline with quality gate"""

    def __init__(self, quality_threshold: float = 40.0, auto_preprocess: bool = True):
        self.providers = {
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
        }
        self.image_service = ImageService()
        self.schema_service = SchemaService()
        self.quality_gate = QualityGate()
        self.preprocessor = ImagePreprocessor()
        self.hybrid_service = HybridProcessingService()
        self.docling_service = DoclingService()
        self.chunking_service = MarkdownSplitter()
        self.transcription_service = TranscriptionService()
        self.quality_threshold = quality_threshold
        self.auto_preprocess = auto_preprocess

    def get_provider(self, provider_name: str, api_key: str):
        """Get provider instance"""
        provider_class = self.providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        return provider_class(api_key)

    def _validate_file_size(self, file_path: str) -> None:
        """Validate file is under size limit"""
        size = Path(file_path).stat().st_size
        if size > MAX_FILE_SIZE:
            raise ValueError(f"File too large ({size/1024/1024:.1f}MB). Max: {MAX_FILE_SIZE/1024/1024}MB")

    def _should_chunk(self, text: str, model: str) -> bool:
        """Check if document needs chunking"""
        # Get model context window (simplified)
        context_windows = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gemini-2.0-flash": 1000000,
        }
        max_tokens = context_windows.get(model, 128000)
        threshold = int(max_tokens * CHUNK_THRESHOLD_RATIO)

        return self.chunking_service.count_tokens(text) > threshold

    async def _process_via_docling(
        self,
        file_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        is_transcription: bool = False,
        job_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process document using Docling for extraction.

        This method uses DoclingService to extract structured content from documents,
        with optional transcription for audio files and chunking for large documents.
        """
        try:
            # Validate file size
            self._validate_file_size(file_path)

            # Handle transcription for audio files
            if is_transcription:
                transcription_result = await self.transcription_service.transcribe(file_path)
                if not transcription_result["success"]:
                    return {
                        "success": False,
                        "error": f"Transcription failed: {transcription_result.get('error', 'Unknown error')}",
                    }
                markdown_content = transcription_result["text"]
            else:
                # Extract content using Docling
                try:
                    markdown_content = self.docling_service.parse_document(file_path)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Docling extraction failed: {str(e)}",
                    }

            # Check if chunking is needed
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

            # Process as single document
            result = await provider.process_text(
                text=markdown_content,
                prompt=prompt,
                schema_definition=schema_definition,
                model=model,
                **kwargs,
            )

            # Check for provider-level errors
            if "error" in result:
                return {
                    "success": False,
                    "error": f"Provider error: {result['error']}",
                    "raw_response": result,
                }

            # Validate result
            content = result.get("content", "{}")
            validation_result = parse_and_validate_response(
                content, schema_definition, self.schema_service
            )

            if validation_result["success"]:
                return {
                    "success": True,
                    "data": validation_result["data"],
                    "raw_response": result,
                    "metadata": {
                        "extraction_method": "docling",
                        "chunked": False,
                    },
                }
            else:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "raw_response": result,
                }

        except Exception as e:
            # Check if it's a docling-related error
            error_type = type(e).__name__
            if "docling" in str(e).lower() or "Docling" in error_type:
                return {
                    "success": False,
                    "error": f"Docling error: {str(e)}",
                }
            else:
                raise
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            import traceback

            return {
                "success": False,
                "error": f"Unexpected error: {type(e).__name__}: {str(e)}",
                "traceback": traceback.format_exc(),
            }

    async def _process_chunked_document(
        self,
        markdown_content: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        job_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process large document by splitting into chunks and merging results.

        This method chunks the document, processes each chunk separately,
        and merges the results intelligently.
        """
        try:
            # Split document into chunks
            chunks = self.chunking_service.split(markdown_content)

            if not chunks:
                return {
                    "success": False,
                    "error": "Failed to split document into chunks",
                }

            results = []
            errors = []

            # Process each chunk
            for i, chunk in enumerate(chunks):
                chunk_prompt = f"{prompt}\n\n(Process chunk {i + 1} of {len(chunks)})"

                try:
                    result = await provider.process_text(
                        text=chunk,
                        prompt=chunk_prompt,
                        schema_definition=schema_definition,
                        model=model,
                        **kwargs,
                    )

                    # Check for provider-level errors
                    if "error" in result:
                        errors.append(f"Chunk {i + 1}: {result['error']}")
                        continue

                    # Validate result
                    content = result.get("content", "{}")
                    validation_result = parse_and_validate_response(
                        content, schema_definition, self.schema_service
                    )

                    if validation_result["success"]:
                        results.append(validation_result["data"])
                    else:
                        errors.append(f"Chunk {i + 1}: {validation_result['error']}")

                except Exception as e:
                    errors.append(f"Chunk {i + 1}: {type(e).__name__}: {str(e)}")

            # Merge results
            if not results:
                return {
                    "success": False,
                    "error": f"All chunks failed to process: {'; '.join(errors)}",
                    "errors": errors,
                }

            # Simple merge: combine all results
            # For more sophisticated merging, you might implement field-specific logic
            merged_data = {}
            for result in results:
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key not in merged_data:
                            merged_data[key] = value
                        elif isinstance(value, list):
                            # Append to existing list
                            if isinstance(merged_data[key], list):
                                merged_data[key].extend(value)
                            else:
                                # Convert to list if needed
                                merged_data[key] = [merged_data[key]] + value
                        elif isinstance(value, dict) and isinstance(merged_data.get(key), dict):
                            # Merge nested dicts
                            merged_data[key].update(value)

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
                    "extraction_method": "docling",
                    "chunked": True,
                    "total_chunks": len(chunks),
                    "successful_chunks": len(results),
                },
            }

        except Exception as e:
            import traceback

            return {
                "success": False,
                "error": f"Chunk processing error: {type(e).__name__}: {str(e)}",
                "traceback": traceback.format_exc(),
            }

    async def process_file(
        self,
        file_id: str,
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Process a file (image or PDF)"""
        extraction_method = kwargs.pop("extraction_method", "docling")  # Default to docling
        is_transcription = kwargs.pop("is_transcription", False)

        # Get API key
        api_key = getattr(settings, f"{provider_name}_api_key")
        if not api_key:
            raise ValueError(f"No API key configured for {provider_name}")

        async with self.get_provider(provider_name, api_key) as provider:
            if extraction_method == "docling":
                return await self._process_via_docling(
                    file_path, provider, model, schema_definition, prompt, is_transcription, **kwargs
                )
            elif file_type == "pdf" and extraction_method == "hybrid":
                return await self.hybrid_service.process_pdf(
                    file_path, provider, model, schema_definition, prompt, **kwargs
                )
            elif file_type == "image":
                return await self._process_single_image(
                    file_path, provider, model, schema_definition, prompt, **kwargs
                )
            else:  # PDF
                return await self._process_pdf(
                    file_path, provider, model, schema_definition, prompt, **kwargs
                )

    async def _process_single_image(
        self,
        image_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        job_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Process a single image with quality gate"""

        # Load image
        image = self.image_service.load_image(image_path)

        # Quality gate check
        quality_report = self.quality_gate.assess(image)

        # Save quality info to job if job_id provided
        if job_id is not None:
            await crud.update_quality_info(
                job_id=job_id,
                quality_score=quality_report.overall_score,
                quality_checks=self.quality_gate.to_dict(quality_report),
            )

        # Check if quality is too low
        if not quality_report.passed:
            if self.auto_preprocess and quality_report.auto_fixable_issues:
                # Try to auto-fix
                preprocess_result = self.preprocessor.fix(
                    image, quality_report=quality_report
                )
                image = preprocess_result.processed

                # Re-assess after preprocessing
                post_quality = self.quality_gate.assess(image)

                # Update job with preprocessing info
                if job_id is not None:
                    await crud.update_quality_info(
                        job_id=job_id,
                        quality_score=post_quality.overall_score,
                        quality_checks=self.quality_gate.to_dict(post_quality),
                        preprocessing_applied=preprocess_result.applied,
                    )

                quality_report = post_quality

                # If still below threshold after preprocessing, reject
                if quality_report.overall_score < self.quality_threshold:
                    return {
                        "success": False,
                        "error": (
                            f"Image quality is too poor for reliable extraction "
                            f"(score: {quality_report.overall_score}/100, "
                            f"threshold: {self.quality_threshold}). "
                            f"Issues: {'; '.join(quality_report.recommendations)}"
                        ),
                        "quality_report": self.quality_gate.to_dict(quality_report),
                    }
            else:
                # No auto-preprocess or no fixable issues — reject
                return {
                    "success": False,
                    "error": (
                        f"Image quality is too poor for reliable extraction "
                        f"(score: {quality_report.overall_score}/100, "
                        f"threshold: {self.quality_threshold}). "
                        f"Issues: {'; '.join(quality_report.recommendations)}"
                    ),
                    "quality_report": self.quality_gate.to_dict(quality_report),
                }

        # Resize for provider
        target_size = provider.get_default_image_size()
        image = self.image_service.resize_image(image, target_size)

        # Process with VLM
        result = await provider.process_image(
            image, prompt, schema_definition, model, **kwargs
        )

        # Check for provider-level errors
        if "error" in result:
            return {
                "success": False,
                "error": f"Provider error: {result['error']}",
                "raw_response": result,
                "quality_report": self.quality_gate.to_dict(quality_report),
            }

        # Validate result
        content = result.get("content", "{}")

        validation_result = parse_and_validate_response(
            content, schema_definition, self.schema_service
        )

        if validation_result["success"]:
            return {
                "success": True,
                "data": validation_result["data"],
                "raw_response": result,
                "quality_report": self.quality_gate.to_dict(quality_report),
            }
        else:
            return {
                "success": False,
                "error": validation_result["error"],
                "raw_response": result,
                "quality_report": self.quality_gate.to_dict(quality_report),
            }

    async def _process_pdf(
        self,
        pdf_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        job_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Process PDF (multiple pages) with quality gate"""

        # Convert PDF to images
        images = self.image_service.pdf_to_images(pdf_path)

        results = []
        errors = []
        page_quality_reports = []

        for i, image in enumerate(images):
            # Quality gate check per page
            quality_report = self.quality_gate.assess(image)
            page_quality_reports.append(quality_report)

            # Auto-preprocess if needed
            if (
                not quality_report.passed
                and self.auto_preprocess
                and quality_report.auto_fixable_issues
            ):
                preprocess_result = self.preprocessor.fix(
                    image, quality_report=quality_report
                )
                image = preprocess_result.processed
                quality_report = self.quality_gate.assess(image)

                if job_id is not None:
                    # Track preprocessing operations per page
                    prev = await crud.get_job(job_id)
                    existing_preproc = []
                    if prev and prev.get("preprocessing_applied"):
                        try:
                            existing_preproc = json.loads(prev["preprocessing_applied"])
                        except Exception:
                            pass
                    merged = list(set(existing_preproc + preprocess_result.applied))
                    await crud.update_quality_info(
                        job_id=job_id,
                        quality_checks=self.quality_gate.to_dict(quality_report),
                        preprocessing_applied=merged,
                    )

            # Resize
            target_size = provider.get_default_image_size()
            resized = self.image_service.resize_image(image, target_size)

            # Process
            result = await provider.process_image(
                resized, prompt, schema_definition, model, **kwargs
            )

            # Check for provider-level errors
            if "error" in result:
                errors.append(f"Page {i + 1}: {result['error']}")
                continue

            # Validate
            content = result.get("content", "{}")
            validation_result = parse_and_validate_response(
                content, schema_definition, self.schema_service
            )

            if validation_result["success"]:
                results.append(validation_result["data"])
            else:
                errors.append(f"Page {i + 1}: {validation_result['error']}")

        # Save aggregate quality info for PDF
        if job_id is not None and page_quality_reports:
            avg_score = sum(r.overall_score for r in page_quality_reports) / len(
                page_quality_reports
            )
            # Save the first page's detailed checks as representative
            await crud.update_quality_info(
                job_id=job_id,
                quality_score=round(avg_score, 1),
                quality_checks=self.quality_gate.to_dict(page_quality_reports[0]),
            )

        return {
            "success": len(errors) == 0,
            "data": results,
            "errors": errors if errors else None,
            "total_pages": len(images),
            "successful_pages": len(results),
            "quality_report": self.quality_gate.to_dict(page_quality_reports[0])
            if page_quality_reports
            else None,
        }


async def run_processing_job(
    job_id: int,
    file_path: str,
    schema_definition_override: Optional[Dict[str, Any]] = None,
    prompt_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    max_tokens_override: Optional[int] = None,
    quality_threshold: Optional[float] = None,
    auto_preprocess: Optional[bool] = None,
    extraction_method_override: Optional[str] = None,
) -> None:
    """
    Run vision extraction job (processes images/PDFs as images using VLMs).
    Best for: Scanned documents, images, PDFs with visual elements.

    Optional overrides preserve request-time settings when the job is queued in-memory.
    """

    # Get job details
    job = await crud.get_job(job_id)
    if not job:
        return

    # Update status to processing
    await update_job_status_with_broadcast(job_id, "processing")

    # Determine file type from job record
    file_type = job["file_type"]

    # Get schema
    if schema_definition_override is not None:
        schema_definition = schema_definition_override
    elif job["schema_id"]:
        schema_record = await crud.get_schema(job["schema_id"])
        if schema_record:
            import json

            schema_definition = json.loads(schema_record["definition"])
        else:
            schema_definition = SchemaService.get_builtin_templates()["Generic"]
    else:
        schema_definition = SchemaService.get_builtin_templates()["Generic"]

    prompt = prompt_override or "Extract all information from this document"
    temperature = 0.1 if temperature_override is None else temperature_override
    max_tokens = 4096 if max_tokens_override is None else max_tokens_override

    # Process
    service = ProcessingService(
        quality_threshold=quality_threshold if quality_threshold is not None else 40.0,
        auto_preprocess=auto_preprocess if auto_preprocess is not None else True,
    )
    start_time = time.time()

    try:
        result = await service.process_file(
            file_id=str(job_id),  # Use job_id as file_id reference
            file_path=file_path,  # Use the provided file_path
            file_type=file_type,
            provider_name=job["provider"],
            model=job["model"],
            schema_definition=schema_definition,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            job_id=job_id,
            extraction_method=extraction_method_override
            or job.get("processing_method")
            or "vision",
        )

        print(f"Processing completed for job {job_id} Result: {result.get('success')}")

        processing_time = time.time() - start_time

        if result["success"]:
            raw_response = result.get("raw_response", {})
            usage = (
                raw_response.get("usage") if isinstance(raw_response, dict) else None
            )
            if result.get("metadata"):
                await crud.update_job_metadata(job_id, result["metadata"])
            await update_job_status_with_broadcast(
                job_id,
                "success",
                result=result.get("data"),
                processing_time=processing_time,
                usage=usage,
            )
        else:
            raw_response = result.get("raw_response", {})
            usage = (
                raw_response.get("usage") if isinstance(raw_response, dict) else None
            )
            if result.get("metadata"):
                await crud.update_job_metadata(job_id, result["metadata"])
            await update_job_status_with_broadcast(
                job_id,
                "error",
                error_message=result.get("error"),
                processing_time=processing_time,
                usage=usage,
            )

    except Exception as e:
        processing_time = time.time() - start_time
        import traceback

        error_details = f"{type(e).__name__}: {str(e)}"
        print(f"ERROR processing job {job_id}: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        await update_job_status_with_broadcast(
            job_id,
            "error",
            error_message=error_details,
            processing_time=processing_time,
        )


async def run_text_processing_job(
    job_id: int,
    file_path: str,
    schema_definition_override: Optional[Dict[str, Any]] = None,
    prompt_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    max_tokens_override: Optional[int] = None,
) -> None:
    """
    Run text extraction job (extracts text from PDFs using pdfplumber, then processes with LLM).
    Best for: Digital PDFs with extractable text (faster & more cost-effective).
    """

    from config import get_settings
    from services.text_extraction import TextExtractionService
    from database import crud
    from services.schema_service import SchemaService

    settings = get_settings()

    # Get job details
    job = await crud.get_job(job_id)
    if not job:
        return

    # Update status to processing
    await update_job_status_with_broadcast(job_id, "processing")

    # Get schema
    if schema_definition_override is not None:
        schema_definition = schema_definition_override
    elif job["schema_id"]:
        schema_record = await crud.get_schema(job["schema_id"])
        if schema_record:
            schema_definition = json.loads(schema_record["definition"])
        else:
            schema_definition = SchemaService.get_builtin_templates()["Generic"]
    else:
        schema_definition = SchemaService.get_builtin_templates()["Generic"]

    prompt = prompt_override or "Extract all information from this document"
    temperature = 0.1 if temperature_override is None else temperature_override
    max_tokens = 4096 if max_tokens_override is None else max_tokens_override

    # Get API key
    provider_name = job["provider"]
    api_key = getattr(settings, f"{provider_name}_api_key")
    if not api_key:
        await update_job_status_with_broadcast(
            job_id, "error", error_message=f"No API key configured for {provider_name}"
        )
        return

    # Process
    start_time = time.time()

    try:
        print(f"Starting TEXT processing for job {job_id}")

        # Step 1: Extract text using pdfplumber
        text_service = TextExtractionService()
        extracted_text = text_service.extract_text_from_pdf(file_path)

        if not extracted_text:
            await update_job_status_with_broadcast(
                job_id,
                "error",
                error_message="This PDF appears to be image-based. Please use the Vision Extraction tab instead.",
                processing_time=time.time() - start_time,
            )
            return

        providers: Dict[str, Type[VLMProvider]] = {
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
        }

        provider_class = providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        async with provider_class(api_key) as provider:
            result = await provider.process_text(
                text=extracted_text,
                prompt=prompt,
                schema_definition=schema_definition,
                model=job["model"],
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Check for errors
        if "error" in result:
            await update_job_status_with_broadcast(
                job_id,
                "error",
                error_message=f"Provider error: {result['error']}",
                processing_time=time.time() - start_time,
            )
            return

        # Validate result
        content = result.get("content", "{}")
        schema_service = SchemaService()
        validation_result = parse_and_validate_response(
            content, schema_definition, schema_service
        )

        if validation_result["success"]:
            await update_job_status_with_broadcast(
                job_id,
                "success",
                result=validation_result["data"],
                processing_time=time.time() - start_time,
                usage=result.get("usage"),
            )
            print(f"Processing completed for job {job_id}")
        else:
            await update_job_status_with_broadcast(
                job_id,
                "error",
                error_message=validation_result["error"],
                processing_time=time.time() - start_time,
                usage=result.get("usage"),
            )

    except Exception as e:
        processing_time = time.time() - start_time
        import traceback

        error_details = f"{type(e).__name__}: {str(e)}"
        print(f"ERROR processing job {job_id}: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        await update_job_status_with_broadcast(
            job_id,
            "error",
            error_message=error_details,
            processing_time=processing_time,
        )
