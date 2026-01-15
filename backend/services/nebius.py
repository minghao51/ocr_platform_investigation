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
        model: str = "meta-llama/Llama-3.2-90B-Vision-Instruct",
        **kwargs
    ) -> Dict[str, Any]:
        """Process image with Nebius"""

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
                "response_format": {"type": "json_object"},
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

    def get_models(self) -> List[str]:
        return [
            "meta-llama/Llama-3.2-90B-Vision-Instruct",
            "meta-llama/Llama-3.2-11B-Vision-Instruct"
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
