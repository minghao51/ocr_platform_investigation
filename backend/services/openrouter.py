from typing import Dict, Any, List, Optional
from PIL import Image
import json
from .vlm_provider import VLMProvider


class OpenRouterProvider(VLMProvider):
    """OpenRouter provider"""

    BASE_URL = "https://openrouter.ai/api/v1"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "anthropic/claude-3.5-sonnet",
        **kwargs,
    ) -> Dict[str, Any]:
        """Process image with OpenRouter"""

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                        },
                    },
                ],
            }
        ]

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

        response = await self._call_with_fallback(payload)
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        return {
            "raw_response": result,
            "content": content,
            "usage": result.get("usage", {}),
        }

    async def _call_with_fallback(self, payload: dict) -> Any:
        """
        Try json_schema mode first, fall back to json_object, then plain prompt.
        """
        # Attempt 1: Full JSON Schema
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
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
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=fallback_payload,
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
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=plain_payload,
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
    ) -> Dict[str, Any]:
        """Process text with OpenRouter text-only model"""
        if schema_definition is None:
            system_prompt = (
                "You are a document transcription assistant. "
                "Return only clean Markdown with no JSON wrapper."
            )
        else:
            system_prompt = f"""You are a document data extraction assistant. Extract information from the following text according to this JSON schema:

{json.dumps(schema_definition, indent=2)}

Return ONLY valid JSON. No explanations, no markdown formatting."""

        try:
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
                            "content": f"{prompt}\n\nDocument text:\n{text}",
                        },
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return {
                "content": content,
                "model": model,
                "usage": {
                    "prompt_tokens": result["usage"]["prompt_tokens"],
                    "completion_tokens": result["usage"]["completion_tokens"],
                    "total_tokens": result["usage"]["total_tokens"],
                },
            }

        except Exception as e:
            return {"error": str(e), "content": None, "model": model}

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available OpenRouter models with metadata"""
        return [
            {
                "id": "qwen/qwen3.6-plus:free",
                "name": "Qwen3.6 Plus (Free)",
                "tier": "free",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 262144,
                "description": "Free tier model for low-cost extraction",
            },
            {
                "id": "qwen/qwen3.5-flash-02-23",
                "name": "Qwen3.5 Flash",
                "tier": "lite",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 1000000,
                "description": "Cheapest paid vision model, native VL",
            },
            {
                "id": "google/gemini-2.5-flash-lite",
                "name": "Gemini 2.5 Flash Lite",
                "tier": "lite",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 1048576,
                "description": "Ultra-cheap, fast, 1M context",
            },
            {
                "id": "google/gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "tier": "balanced",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 1048576,
                "description": "Balanced Gemini model via OpenRouter",
            },
            {
                "id": "google/gemini-3-flash-preview",
                "name": "Gemini 3 Flash Preview",
                "tier": "balanced",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 1048576,
                "description": "Near-Pro reasoning, #1 Finance ranking",
            },
            {
                "id": "x-ai/grok-4.1-fast",
                "name": "Grok 4.1 Fast",
                "tier": "balanced",
                "capabilities": ["vision", "reasoning"],
                "context_window": 2000000,
                "description": "Cheapest paid vision, 2M context",
            },
            {
                "id": "openai/gpt-4.1-mini",
                "name": "GPT-4.1 Mini",
                "tier": "balanced",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 1048576,
                "description": "General-purpose compact multimodal model",
            },
            {
                "id": "google/gemma-4-31b-it",
                "name": "Gemma 4 31B IT",
                "tier": "lite",
                "capabilities": ["vision", "reasoning", "structured_output"],
                "context_window": 262144,
                "description": "Google open VLM, strong OCR and table extraction",
            },
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
