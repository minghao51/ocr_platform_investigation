import json
import logging
from typing import Any, Dict, Optional

from database import crud
from services.image_service import ImageService
from services.image_preprocessor import ImagePreprocessor
from services.quality_gate import QualityGate
from services.schema_service import SchemaService
from services.processing_utils import parse_and_validate_response
from services.processors.base import Processor

logger = logging.getLogger(__name__)


class VisionProcessor(Processor):
    def __init__(
        self,
        quality_threshold: float = 40.0,
        auto_preprocess: bool = True,
        skip_quality: bool = False,
    ):
        self.image_service = ImageService()
        self._schema_service: Optional[SchemaService] = None
        self.quality_gate = QualityGate()
        self.preprocessor = ImagePreprocessor()
        self.quality_threshold = quality_threshold
        self.auto_preprocess = auto_preprocess
        self.skip_quality = skip_quality

    def _get_schema_service(self) -> SchemaService:
        if self._schema_service is None:
            self._schema_service = SchemaService()
        return self._schema_service

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
        image = self.image_service.load_image(image_path)

        quality_report = None

        if not self.skip_quality:
            quality_report = self.quality_gate.assess(image)

            if job_id is not None:
                await crud.update_quality_info(
                    job_id=job_id,
                    quality_score=quality_report.overall_score,
                    quality_checks=self.quality_gate.to_dict(quality_report),
                )

            if not quality_report.passed:
                if self.auto_preprocess and quality_report.auto_fixable_issues:
                    preprocess_result = self.preprocessor.fix(
                        image, quality_report=quality_report
                    )
                    image = preprocess_result.processed

                    post_quality = self.quality_gate.assess(image)

                    if job_id is not None:
                        await crud.update_quality_info(
                            job_id=job_id,
                            quality_score=post_quality.overall_score,
                            quality_checks=self.quality_gate.to_dict(post_quality),
                            preprocessing_applied=preprocess_result.applied,
                        )

                    quality_report = post_quality

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

        target_size = provider.get_default_image_size()
        image = self.image_service.resize_image(image, target_size)

        provider_kwargs = {k: v for k, v in kwargs.items()}
        system_prompt = provider_kwargs.pop("system_prompt", None)
        if system_prompt:
            provider_kwargs["system_prompt"] = system_prompt

        result = await provider.process_image(
            image, prompt, schema_definition, model, **provider_kwargs
        )

        if "error" in result:
            return {
                "success": False,
                "error": f"Provider error: {result['error']}",
                "raw_response": result,
                "quality_report": self.quality_gate.to_dict(quality_report)
                if quality_report
                else None,
            }

        content = result.get("content") or "{}"

        validation_result = parse_and_validate_response(
            content, schema_definition, self._get_schema_service()
        )

        if validation_result["success"]:
            return {
                "success": True,
                "data": validation_result["data"],
                "raw_response": result,
                "quality_report": self.quality_gate.to_dict(quality_report)
                if quality_report
                else None,
            }
        else:
            return {
                "success": False,
                "error": validation_result["error"],
                "raw_response": result,
                "quality_report": self.quality_gate.to_dict(quality_report)
                if quality_report
                else None,
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
        images = self.image_service.pdf_to_images(pdf_path)

        results = []
        errors = []
        page_quality_reports = []

        for i, image in enumerate(images):
            if not self.skip_quality:
                quality_report = self.quality_gate.assess(image)
                page_quality_reports.append(quality_report)

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
                        prev = await crud.get_job(job_id)
                        existing_preproc = []
                        if prev and prev.get("preprocessing_applied"):
                            try:
                                existing_preproc = json.loads(
                                    prev["preprocessing_applied"]
                                )
                            except Exception:
                                pass
                        merged = list(
                            set(existing_preproc + preprocess_result.applied)
                        )
                        await crud.update_quality_info(
                            job_id=job_id,
                            quality_checks=self.quality_gate.to_dict(quality_report),
                            preprocessing_applied=merged,
                        )

            target_size = provider.get_default_image_size()
            resized = self.image_service.resize_image(image, target_size)

            result = await provider.process_image(
                resized, prompt, schema_definition, model, **kwargs
            )

            if "error" in result:
                errors.append(f"Page {i + 1}: {result['error']}")
                continue

            content = result.get("content") or "{}"
            validation_result = parse_and_validate_response(
                content, schema_definition, self._get_schema_service()
            )

            if validation_result["success"]:
                results.append(validation_result["data"])
            else:
                errors.append(f"Page {i + 1}: {validation_result['error']}")

        if job_id is not None and page_quality_reports:
            avg_score = sum(r.overall_score for r in page_quality_reports) / len(
                page_quality_reports
            )
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
            if file_type == "image":
                return await self._process_single_image(
                    file_path,
                    provider,
                    model,
                    schema_definition,
                    prompt,
                    job_id,
                    **kwargs,
                )
            else:
                return await self._process_pdf(
                    file_path,
                    provider,
                    model,
                    schema_definition,
                    prompt,
                    job_id,
                    **kwargs,
                )
