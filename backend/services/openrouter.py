from typing import Dict, Any, List
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
        **kwargs
    ) -> Dict[str, Any]:
        """Process image with OpenRouter"""

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                        }
                    }
                ]
            }
        ]

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 4096)
            }
        )

        response.raise_for_status()
        result = response.json()

        # Extract content
        content = result["choices"][0]["message"]["content"]

        return {
            "raw_response": result,
            "content": content,
            "usage": result.get("usage", {})
        }

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available OpenRouter models with metadata"""
        return [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "tier": "premium",
                "capabilities": ["vision", "reasoning"],
                "context_window": 200000,
                "description": "Advanced reasoning with vision"
            },
            {
                "id": "google/gemini-pro-1.5",
                "name": "Gemini Pro 1.5",
                "tier": "balanced",
                "capabilities": ["vision", "reasoning"],
                "context_window": 2800000,
                "description": "Large context window with vision"
            },
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "tier": "premium",
                "capabilities": ["vision", "reasoning"],
                "context_window": 128000,
                "description": "OpenAI's latest multimodal model"
            },
            {
                "id": "meta-llama/llama-3.2-90b-vision-preview",
                "name": "Llama 3.2 90B Vision",
                "tier": "balanced",
                "capabilities": ["vision", "reasoning"],
                "context_window": 131072,
                "description": "Large open-source vision model"
            }
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
