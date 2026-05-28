from typing import Dict, Any, Optional
from PIL import Image
import json
import asyncio
from .vlm_provider import VLMProvider, ExtractionResult, TokenUsage


class OpenRouterProvider(VLMProvider):
    """OpenRouter provider"""

    BASE_URL = "https://openrouter.ai/api/v1"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "qwen/qwen3.5-flash-02-23",
        **kwargs,
    ) -> ExtractionResult:
        """Process image with OpenRouter"""

        system_prompt = kwargs.pop("system_prompt", None)

        user_content = [
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                },
            },
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        # Build structured output format
        json_schema = {
            "name": "extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
                "additionalProperties": False,
            },
        }

        payload = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_schema", "json_schema": json_schema},
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        try:
            response = await self._call_with_fallback(payload)
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return ExtractionResult(
                content=content,
                raw_response=json.dumps(result),
                usage=TokenUsage(
                    prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
                    completion_tokens=result.get("usage", {}).get(
                        "completion_tokens", 0
                    ),
                    total_tokens=result.get("usage", {}).get("total_tokens", 0),
                ),
                model=model,
            )
        except Exception:
            return ExtractionResult(
                error="Provider request failed", success=False, model=model
            )

    async def _call_with_retry(self, url, payload, headers, max_retries=3):
        for attempt in range(max_retries):
            response = await self.client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2**attempt))
                await asyncio.sleep(min(retry_after, 30))
            elif response.status_code in (500, 502, 503, 504):
                await asyncio.sleep(2**attempt)
            elif response.status_code in (400, 422):
                break
            else:
                break
        return response

    async def _call_with_fallback(self, payload: dict) -> Any:
        """
        Try json_schema mode first, fall back to json_object, then plain prompt.
        Uses retry with backoff for transient failures.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Attempt 1: Full JSON Schema
        response = await self._call_with_retry(
            f"{self.BASE_URL}/chat/completions", payload, headers
        )

        if response.status_code == 200:
            return response

        # Attempt 2: Fallback to json_object mode
        if response.status_code in (400, 422):
            fallback_payload = {
                "model": payload["model"],
                "messages": payload["messages"],
                "response_format": {"type": "json_object"},
                "temperature": payload.get("temperature", 0.1),
                "max_tokens": payload.get("max_tokens", 4096),
            }
            response = await self._call_with_retry(
                f"{self.BASE_URL}/chat/completions", fallback_payload, headers
            )
            if response.status_code == 200:
                return response

        # Attempt 3: No structured output at all — rely on prompt
        plain_payload = {
            "model": payload["model"],
            "messages": payload["messages"],
            "temperature": payload.get("temperature", 0.1),
            "max_tokens": payload.get("max_tokens", 4096),
        }
        response = await self._call_with_retry(
            f"{self.BASE_URL}/chat/completions", plain_payload, headers
        )
        response.raise_for_status()
        return response

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
        """Process text with OpenRouter text-only model"""
        system_prompt_override = kwargs.pop("system_prompt", None)

        if schema_definition is None:
            system_prompt = system_prompt_override or (
                "You are a document transcription assistant. "
                "Return only clean Markdown with no JSON wrapper."
            )
        else:
            system_prompt = system_prompt_override or (
                "You are a document data extraction assistant. "
                "Extract information from the following text according to the provided schema. "
                "Return ONLY valid JSON. No explanations, no markdown formatting."
            )

        try:
            user_content = f"{prompt}\n\nDocument text:\n{text}"
            if schema_definition is not None:
                user_content += (
                    "\n\nTarget JSON schema:\n"
                    f"{json.dumps(schema_definition, indent=2)}"
                )
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": user_content,
                        },
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return ExtractionResult(
                content=content,
                model=model,
                usage=TokenUsage(
                    prompt_tokens=result["usage"]["prompt_tokens"],
                    completion_tokens=result["usage"]["completion_tokens"],
                    total_tokens=result["usage"]["total_tokens"],
                ),
            )

        except Exception:
            return ExtractionResult(
                error="Provider request failed", success=False, model=model
            )

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
