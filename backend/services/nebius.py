from typing import Dict, Any, List
from PIL import Image
import json
from .vlm_provider import VLMProvider


class NebiusProvider(VLMProvider):
    """Nebius AI Studio provider"""

    BASE_URL = "https://api.studio.nebius.ai/v1"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "Qwen/Qwen2.5-VL-72B-Instruct",
        **kwargs,
    ) -> Dict[str, Any]:
        """Process image with Nebius"""

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

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "response_format": {"type": "json_schema", "json_schema": json_schema},
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 4096),
            },
        )

        response.raise_for_status()
        result = response.json()

        # Extract content
        content = result["choices"][0]["message"]["content"]

        return {
            "raw_response": result,
            "content": content,
            "usage": result.get("usage", {}),
        }

    async def process_text(
        self,
        text: str,
        prompt: str,
        schema_definition: Dict[str, Any],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process text with Nebius text-only model
        """
        # Build the prompt
        system_prompt = f"""You are a document data extraction assistant. Extract information from the following text according to this JSON schema:

{json.dumps(schema_definition, indent=2)}

Return ONLY valid JSON. No explanations, no markdown formatting."""

        try:
            # Make API call (text-only, no image)
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
                    "response_format": {"type": "json_object"},
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
        """Get available Nebius models with metadata"""
        return [
            {
                "id": "Qwen/Qwen2.5-VL-72B-Instruct",
                "name": "Qwen2.5-VL 72B",
                "tier": "premium",
                "capabilities": ["vision", "reasoning", "video"],
                "context_window": 131072,
                "description": "High-performance vision model for complex visual tasks",
            }
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
