import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import json
from .vlm_provider import VLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(VLMProvider):
    """Google Gemini provider"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "gemini-1.5-pro",
        **kwargs,
    ) -> Dict[str, Any]:
        """Process image with Gemini"""

        # Prepare content
        content = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": self.encode_image(image),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
                "responseMimeType": "application/json",
                "responseSchema": self._convert_json_schema_to_gemini(schema),
            },
        }

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json=content,
        )

        response.raise_for_status()
        result = response.json()

        # Extract content with better error handling
        try:
            # Check if candidates exist
            if "candidates" not in result or len(result["candidates"]) == 0:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": "No candidates in response",
                }

            candidate = result["candidates"][0]

            # Check if content exists
            if "content" not in candidate:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": "No content in candidate",
                }

            content = candidate["content"]

            # Check if parts exist
            if "parts" not in content or len(content["parts"]) == 0:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": "No parts in content",
                }

            part = content["parts"][0]

            # Check if text exists
            if "text" not in part:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": f"No text in part. Available keys: {list(part.keys())}",
                }

            content_text = part["text"]

            # Return empty JSON if content is empty
            if not content_text or content_text.strip() == "":
                print(f"Warning: Empty content received from Gemini model {model}")
                print(f"Raw response: {result}")
                content_text = "{}"

        except (KeyError, IndexError) as e:
            return {
                "raw_response": result,
                "content": "{}",
                "usage": result.get("usageMetadata", {}),
                "error": f"Failed to extract content: {str(e)}",
            }

        return {
            "raw_response": result,
            "content": content_text,
            "usage": result.get("usageMetadata", {}),
        }

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
    ) -> Dict[str, Any]:
        """Process text with Gemini text-only model"""
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
            prompt_text = (
                f"{prompt}\n\nDocument text:\n{text}\n\n"
                f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema_definition, indent=2)}"
            )
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = self._convert_json_schema_to_gemini(
                schema_definition
            )

        # Prepare content (text-only, no image)
        content = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": generation_config,
        }

        try:
            # Make API call
            response = await self.client.post(
                f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=content,
            )

            response.raise_for_status()
            result = response.json()

            # Extract content with error handling
            if "candidates" not in result or len(result["candidates"]) == 0:
                return {
                    "error": "No candidates in response",
                    "content": None,
                    "model": model,
                }

            candidate = result["candidates"][0]
            finish_reason = candidate.get("finishReason", "")

            if finish_reason == "SAFETY":
                safety_ratings = candidate.get("safetyRatings", [])
                blocked_categories = [
                    r.get("category", "unknown")
                    for r in safety_ratings
                    if r.get("probability", "") in ("HIGH", "NEGLIGIBLE")
                    and r.get("blocked", False)
                ]
                return {
                    "error": f"Response blocked by safety filters. Categories: {blocked_categories or 'unknown'}",
                    "content": None,
                    "model": model,
                }

            if finish_reason == "RECITATION":
                return {
                    "error": "Response blocked due to recitation policy",
                    "content": None,
                    "model": model,
                }

            if finish_reason == "MAX_TOKENS":
                if "content" in candidate and "parts" in candidate["content"]:
                    content_text = candidate["content"]["parts"][0].get("text", "")
                    retry_max = min(max_tokens * 2, 65536)
                    if retry_max > max_tokens:
                        logger.warning(
                            f"Gemini response hit MAX_TOKENS (limit={max_tokens}), retrying with {retry_max} tokens"
                        )
                        generation_config["maxOutputTokens"] = retry_max
                        retry_response = await self.client.post(
                            f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}",
                            headers={"Content-Type": "application/json"},
                            json={
                                "contents": [{"parts": [{"text": prompt_text}]}],
                                "generationConfig": generation_config,
                            },
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
                                    return {
                                        "content": retry_text,
                                        "model": model,
                                        "usage": {
                                            "prompt_tokens": retry_result.get(
                                                "usageMetadata", {}
                                            ).get("promptTokenCount", 0),
                                            "completion_tokens": retry_result.get(
                                                "usageMetadata", {}
                                            ).get("candidatesTokenCount", 0),
                                            "total_tokens": retry_result.get(
                                                "usageMetadata", {}
                                            ).get("totalTokenCount", 0),
                                        },
                                    }
                return {
                    "error": f"Response truncated (hit max_tokens={max_tokens}). Try reducing schema complexity or increasing max_tokens.",
                    "content": content_text if content_text else None,
                    "model": model,
                }

            if "content" not in candidate:
                return {
                    "error": "No content in candidate",
                    "content": None,
                    "model": model,
                }

            content_obj = candidate["content"]

            if "parts" not in content_obj or len(content_obj["parts"]) == 0:
                return {"error": "No parts in content", "content": None, "model": model}

            part = content_obj["parts"][0]

            if "text" not in part:
                return {
                    "error": f"No text in part. Available keys: {list(part.keys())}",
                    "content": None,
                    "model": model,
                }

            content_text = part["text"]

            if not content_text or content_text.strip() == "":
                return {
                    "error": "Empty content received",
                    "content": None,
                    "model": model,
                }

            return {
                "content": content_text,
                "model": model,
                "usage": {
                    "prompt_tokens": result.get("usageMetadata", {}).get(
                        "promptTokenCount", 0
                    ),
                    "completion_tokens": result.get("usageMetadata", {}).get(
                        "candidatesTokenCount", 0
                    ),
                    "total_tokens": result.get("usageMetadata", {}).get(
                        "totalTokenCount", 0
                    ),
                },
            }

        except Exception as e:
            return {"error": str(e), "content": None, "model": model}

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available Gemini models with metadata"""
        return [
            {
                "id": "gemini-3-pro-preview",
                "name": "Gemini 3 Pro Preview",
                "tier": "premium",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Highest quality Gemini preview model",
            },
            {
                "id": "gemini-3-flash-preview",
                "name": "Gemini 3 Flash Preview",
                "tier": "balanced",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Balanced speed and intelligence for scale",
            },
            {
                "id": "gemini-2.5-pro",
                "name": "Gemini 2.5 Pro",
                "tier": "premium",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Higher reasoning quality Gemini 2.5 tier",
            },
            {
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "tier": "balanced",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Balanced speed and quality",
            },
            {
                "id": "gemini-2.5-flash-lite",
                "name": "Gemini 2.5 Flash Lite",
                "tier": "lite",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Fastest, most cost-efficient model",
            },
            {
                "id": "gemini-2.0-flash",
                "name": "Gemini 2.0 Flash",
                "tier": "balanced",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Stable balanced Gemini model",
            },
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
