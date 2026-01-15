import time
from pathlib import Path
from typing import Dict, Any, Optional
from config import get_settings
from services.nebius import NebiusProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.image_service import ImageService
from services.schema_service import SchemaService
from database import crud

settings = get_settings()

class ProcessingService:
    """Main processing pipeline"""

    def __init__(self):
        self.providers = {
            "nebius": NebiusProvider,
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider
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
        **kwargs
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
        **kwargs
    ) -> Dict[str, Any]:
        """Process a single image"""

        # Load image
        image = self.image_service.load_image(image_path)

        # Resize for provider
        target_size = provider.get_default_image_size()
        image = self.image_service.resize_image(image, target_size)

        # Process with VLM
        result = await provider.process_image(image, prompt, schema_definition, model, **kwargs)

        # Validate result
        content = result.get("content", "{}")

        try:
            import json
            data = json.loads(content)
            is_valid, validated_data, error = self.schema_service.validate_data(
                data, schema_definition
            )

            if is_valid:
                return {
                    "success": True,
                    "data": validated_data,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Validation failed: {error}",
                    "raw_response": result
                }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON response: {str(e)}",
                "raw_response": result
            }

    async def _process_pdf(
        self,
        pdf_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs
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
            result = await provider.process_image(resized, prompt, schema_definition, model, **kwargs)

            # Validate
            content = result.get("content", "{}")
            try:
                import json
                data = json.loads(content)
                is_valid, validated_data, error = self.schema_service.validate_data(
                    data, schema_definition
                )

                if is_valid:
                    results.append(validated_data)
                else:
                    errors.append(f"Page {i+1}: {error}")
            except json.JSONDecodeError as e:
                errors.append(f"Page {i+1}: Invalid JSON - {str(e)}")

        return {
            "success": len(errors) == 0,
            "data": results,
            "errors": errors if errors else None,
            "total_pages": len(images),
            "successful_pages": len(results)
        }

async def run_processing_job(job_id: int) -> None:
    """Run a processing job (called asynchronously)"""

    from config import get_settings
    from pathlib import Path

    # Get job details
    job = await crud.get_job(job_id)
    if not job:
        return

    # Update status to processing
    await crud.update_job_status(job_id, "processing")

    # Get file path
    file_path = f"./data/uploads/{job['file_id']}"
    file_ext = Path(file_path).suffix

    # Determine file type from job record
    file_type = job['file_type']

    # Get schema
    if job['schema_id']:
        schema_record = await crud.get_schema(job['schema_id'])
        if schema_record:
            import json
            schema_definition = json.loads(schema_record['definition'])
        else:
            schema_definition = SchemaService.get_builtin_templates()["Generic"]
    else:
        schema_definition = SchemaService.get_builtin_templates()["Generic"]

    # Process
    service = ProcessingService()
    start_time = time.time()

    try:
        result = await service.process_file(
            file_id=job['file_id'],
            file_path=file_path,
            file_type=file_type,
            provider_name=job['provider'],
            model=job['model'],
            schema_definition=schema_definition,
            prompt="Extract all information from this document",
            temperature=0.1,
            max_tokens=4096
        )

        processing_time = time.time() - start_time

        if result['success']:
            await crud.update_job_status(
                job_id,
                "success",
                result=result.get('data'),
                processing_time=processing_time
            )
        else:
            await crud.update_job_status(
                job_id,
                "error",
                error_message=result.get('error'),
                processing_time=processing_time
            )

    except Exception as e:
        processing_time = time.time() - start_time
        await crud.update_job_status(
            job_id,
            "error",
            error_message=str(e),
            processing_time=processing_time
        )
