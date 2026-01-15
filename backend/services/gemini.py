from typing import Dict, Any, List
from PIL import Image
import json
from .vlm_provider import VLMProvider

class GeminiProvider(VLMProvider):
    """Google Gemini provider"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "gemini-1.5-pro",
        **kwargs
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
                                "data": self.encode_image(image)
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
                "responseMimeType": "application/json"
            }
        }

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json=content
        )

        response.raise_for_status()
        result = response.json()

        # Extract content
        content_text = result["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "raw_response": result,
            "content": content_text,
            "usage": result.get("usageMetadata", {})
        }

    def get_models(self) -> List[str]:
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
