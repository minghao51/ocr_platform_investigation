import logging
from typing import Dict, Any, Optional
from PIL import Image
import json
from .vlm_provider import VLMProvider, ExtractionResult, TokenUsage

logger = logging.getLogger(__name__)


class GeminiProvider(VLMProvider):
    """Google Gemini provider"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "gemini-3-flash-preview",
        **kwargs,
    ) -> ExtractionResult:
        """Process image with Gemini"""

        system_instruction = kwargs.pop("system_prompt", None)

        parts = [
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": self.encode_image(image),
                }
            },
        ]

        content: Dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
                "responseMimeType": "application/json",
                "responseSchema": self._convert_json_schema_to_gemini(schema),
            },
        }

        if system_instruction:
            content["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/models/{model}:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            json=content,
        )

        response.raise_for_status()
        result = response.json()

        # Extract content with better error handling
        try:
            # Check if candidates exist
            if "candidates" not in result or len(result["candidates"]) == 0:
                return ExtractionResult(
                    raw_response=json.dumps(result),
                    content="{}",
                    usage=TokenUsage(
                        prompt_tokens=result.get("usageMetadata", {}).get(
                            "promptTokenCount", 0
                        ),
                        completion_tokens=result.get("usageMetadata", {}).get(
                            "candidatesTokenCount", 0
                        ),
                        total_tokens=result.get("usageMetadata", {}).get(
                            "totalTokenCount", 0
                        ),
                    ),
                    error="No candidates in response",
                    success=False,
                    model=model,
                )

            candidate = result["candidates"][0]

            # Check if content exists
            if "content" not in candidate:
                return ExtractionResult(
                    raw_response=json.dumps(result),
                    content="{}",
                    usage=TokenUsage(
                        prompt_tokens=result.get("usageMetadata", {}).get(
                            "promptTokenCount", 0
                        ),
                        completion_tokens=result.get("usageMetadata", {}).get(
                            "candidatesTokenCount", 0
                        ),
                        total_tokens=result.get("usageMetadata", {}).get(
                            "totalTokenCount", 0
                        ),
                    ),
                    error="No content in candidate",
                    success=False,
                    model=model,
                )

            content = candidate["content"]

            # Check if parts exist
            if "parts" not in content or len(content["parts"]) == 0:
                return ExtractionResult(
                    raw_response=json.dumps(result),
                    content="{}",
                    usage=TokenUsage(
                        prompt_tokens=result.get("usageMetadata", {}).get(
                            "promptTokenCount", 0
                        ),
                        completion_tokens=result.get("usageMetadata", {}).get(
                            "candidatesTokenCount", 0
                        ),
                        total_tokens=result.get("usageMetadata", {}).get(
                            "totalTokenCount", 0
                        ),
                    ),
                    error="No parts in content",
                    success=False,
                    model=model,
                )

            part = content["parts"][0]

            # Check if text exists
            if "text" not in part:
                return ExtractionResult(
                    raw_response=json.dumps(result),
                    content="{}",
                    usage=TokenUsage(
                        prompt_tokens=result.get("usageMetadata", {}).get(
                            "promptTokenCount", 0
                        ),
                        completion_tokens=result.get("usageMetadata", {}).get(
                            "candidatesTokenCount", 0
                        ),
                        total_tokens=result.get("usageMetadata", {}).get(
                            "totalTokenCount", 0
                        ),
                    ),
                    error="No text in part",
                    success=False,
                    model=model,
                )

            content_text = part["text"]

            # Return empty JSON if content is empty
            if not content_text or content_text.strip() == "":
                logger.warning("Empty content received from Gemini model %s", model)
                logger.debug("Raw response: %s", result)
                content_text = "{}"

        except (KeyError, IndexError):
            return ExtractionResult(
                error="Provider request failed", success=False, model=model
            )

        return ExtractionResult(
            content=content_text,
            raw_response=json.dumps(result),
            usage=TokenUsage(
                prompt_tokens=result.get("usageMetadata", {}).get(
                    "promptTokenCount", 0
                ),
                completion_tokens=result.get("usageMetadata", {}).get(
                    "candidatesTokenCount", 0
                ),
                total_tokens=result.get("usageMetadata", {}).get("totalTokenCount", 0),
            ),
            model=model,
        )

    def _convert_json_schema_to_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON Schema to Gemini's responseSchema format."""
        return self._schema_type_to_gemini(schema)

    def _schema_type_to_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively convert JSON Schema to Gemini schema."""
        gemini_type_map = {
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT",
        }

        result: Dict[str, Any] = {}

        if "type" in schema:
            result["type"] = gemini_type_map.get(schema["type"], "STRING")

        if "description" in schema:
            result["description"] = schema["description"]

        if schema.get("type") == "object" and "properties" in schema:
            result["properties"] = {
                key: self._schema_type_to_gemini(val)
                for key, val in schema["properties"].items()
            }
            if "required" in schema:
                result["required"] = schema["required"]

        if schema.get("type") == "array" and "items" in schema:
            result["items"] = self._schema_type_to_gemini(schema["items"])

        return result

    async def process_text(
        self,
        text: str,
        prompt: str,
        schema_definition: Optional[Dict[str, Any]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ExtractionResult:
        """Process text with Gemini text-only model"""
        system_instruction = kwargs.pop("system_prompt", None)

        prompt_text = f"{prompt}\n\nDocument text:\n{text}"
        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        if schema_definition is None:
            prompt_text = (
                f"{prompt}\n\nDocument text:\n{text}\n\n"
                "Return ONLY clean Markdown. Do not wrap the response in JSON."
            )
            generation_config["responseMimeType"] = "text/plain"
        else:
            prompt_text = f"{prompt}\n\nDocument text:\n{text}"
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = self._convert_json_schema_to_gemini(
                schema_definition
            )

        content: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": generation_config,
        }

        if system_instruction:
            content["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            # Make API call
            response = await self.client.post(
                f"{self.BASE_URL}/models/{model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=content,
            )

            response.raise_for_status()
            result = response.json()

            # Extract content with error handling
            if "candidates" not in result or len(result["candidates"]) == 0:
                return ExtractionResult(
                    error="No candidates in response",
                    success=False,
                    model=model,
                )

            candidate = result["candidates"][0]
            finish_reason = candidate.get("finishReason", "")

            if finish_reason == "SAFETY":
                return ExtractionResult(
                    error="Response blocked by safety filters",
                    success=False,
                    model=model,
                )

            if finish_reason == "RECITATION":
                return ExtractionResult(
                    error="Response blocked due to recitation policy",
                    success=False,
                    model=model,
                )

            if finish_reason == "MAX_TOKENS":
                if "content" in candidate and "parts" in candidate["content"]:
                    content_text = candidate["content"]["parts"][0].get("text", "")
                    retry_max = min(max_tokens * 2, 65536)
                    if retry_max > max_tokens:
                        logger.warning(
                            f"Gemini response hit MAX_TOKENS (limit={max_tokens}), retrying with {retry_max} tokens"
                        )
                        generation_config["maxOutputTokens"] = retry_max
                        retry_payload: Dict[str, Any] = {
                            "contents": [{"parts": [{"text": prompt_text}]}],
                            "generationConfig": generation_config,
                        }
                        if system_instruction:
                            retry_payload["systemInstruction"] = {
                                "parts": [{"text": system_instruction}]
                            }
                        retry_response = await self.client.post(
                            f"{self.BASE_URL}/models/{model}:generateContent",
                            headers={
                                "Content-Type": "application/json",
                                "x-goog-api-key": self.api_key,
                            },
                            json=retry_payload,
                        )
                        retry_response.raise_for_status()
                        retry_result = retry_response.json()
                        if (
                            "candidates" in retry_result
                            and len(retry_result["candidates"]) > 0
                        ):
                            retry_candidate = retry_result["candidates"][0]
                            retry_finish = retry_candidate.get("finishReason", "")
                            if (
                                "content" in retry_candidate
                                and "parts" in retry_candidate["content"]
                                and len(retry_candidate["content"]["parts"]) > 0
                                and "text" in retry_candidate["content"]["parts"][0]
                            ):
                                retry_text = retry_candidate["content"]["parts"][0][
                                    "text"
                                ]
                                if retry_finish != "MAX_TOKENS" and retry_text.strip():
                                    return ExtractionResult(
                                        content=retry_text,
                                        model=model,
                                        usage=TokenUsage(
                                            prompt_tokens=retry_result.get(
                                                "usageMetadata", {}
                                            ).get("promptTokenCount", 0),
                                            completion_tokens=retry_result.get(
                                                "usageMetadata", {}
                                            ).get("candidatesTokenCount", 0),
                                            total_tokens=retry_result.get(
                                                "usageMetadata", {}
                                            ).get("totalTokenCount", 0),
                                        ),
                                    )
                return ExtractionResult(
                    error=f"Response truncated (hit max_tokens={max_tokens})",
                    success=False,
                    model=model,
                )

            if "content" not in candidate:
                return ExtractionResult(
                    error="No content in candidate",
                    success=False,
                    model=model,
                )

            content_obj = candidate["content"]

            if "parts" not in content_obj or len(content_obj["parts"]) == 0:
                return ExtractionResult(
                    error="No parts in content",
                    success=False,
                    model=model,
                )

            part = content_obj["parts"][0]

            if "text" not in part:
                return ExtractionResult(
                    error="No text in part",
                    success=False,
                    model=model,
                )

            content_text = part["text"]

            if not content_text or content_text.strip() == "":
                return ExtractionResult(
                    error="Empty content received",
                    success=False,
                    model=model,
                )

            return ExtractionResult(
                content=content_text,
                model=model,
                usage=TokenUsage(
                    prompt_tokens=result.get("usageMetadata", {}).get(
                        "promptTokenCount", 0
                    ),
                    completion_tokens=result.get("usageMetadata", {}).get(
                        "candidatesTokenCount", 0
                    ),
                    total_tokens=result.get("usageMetadata", {}).get(
                        "totalTokenCount", 0
                    ),
                ),
            )

        except Exception:
            return ExtractionResult(
                error="Provider request failed", success=False, model=model
            )

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
