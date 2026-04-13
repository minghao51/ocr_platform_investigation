import time
import json
from typing import Dict, Any, Optional, Type
from config import get_settings
from services.vlm_provider import VLMProvider
from services.nebius import NebiusProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.image_service import ImageService
from services.schema_service import SchemaService
from database import crud

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
    """Main processing pipeline"""

    def __init__(self):
        self.providers = {
            "nebius": NebiusProvider,
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
        }
        self.image_service = ImageService()
        self.schema_service = SchemaService()

    def get_provider(self, provider_name: str, api_key: str):
        """Get provider instance"""
        provider_class = self.providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        return provider_class(api_key)

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

        # Get API key
        api_key = getattr(settings, f"{provider_name}_api_key")
        if not api_key:
            raise ValueError(f"No API key configured for {provider_name}")

        async with self.get_provider(provider_name, api_key) as provider:
            if file_type == "image":
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
        **kwargs,
    ) -> Dict[str, Any]:
        """Process a single image"""

        # Load image
        image = self.image_service.load_image(image_path)

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
            }
        else:
            return {
                "success": False,
                "error": validation_result["error"],
                "raw_response": result,
            }

    async def _process_pdf(
        self,
        pdf_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Process PDF (multiple pages)"""

        # Convert PDF to images
        images = self.image_service.pdf_to_images(pdf_path)

        results = []
        errors = []

        for i, image in enumerate(images):
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

        return {
            "success": len(errors) == 0,
            "data": results,
            "errors": errors if errors else None,
            "total_pages": len(images),
            "successful_pages": len(results),
        }


async def run_processing_job(
    job_id: int,
    file_path: str,
    schema_definition_override: Optional[Dict[str, Any]] = None,
    prompt_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
    max_tokens_override: Optional[int] = None,
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
    service = ProcessingService()
    start_time = time.time()

    try:
        print(f"Starting processing for job {job_id}")
        print(f"  File: {file_path}")
        print(f"  Provider: {job['provider']}")
        print(f"  Model: {job['model']}")

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
        )

        print(f"Processing completed for job {job_id}")
        print(f"  Result: {result.get('success')}")

        processing_time = time.time() - start_time

        if result["success"]:
            raw_response = result.get("raw_response", {})
            usage = raw_response.get("usage") if isinstance(raw_response, dict) else None
            await update_job_status_with_broadcast(
                job_id,
                "success",
                result=result.get("data"),
                processing_time=processing_time,
                usage=usage,
            )
        else:
            raw_response = result.get("raw_response", {})
            usage = raw_response.get("usage") if isinstance(raw_response, dict) else None
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
        print(f"  File: {file_path}")
        print(f"  Provider: {job['provider']}")
        print(f"  Model: {job['model']}")

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

        print(f"  Extracted {len(extracted_text)} characters")

        # Step 2: Get provider and process text
        providers: Dict[str, Type[VLMProvider]] = {
            "nebius": NebiusProvider,
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
