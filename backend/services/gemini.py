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

        # Extract content with better error handling
        try:
            # Check if candidates exist
            if "candidates" not in result or len(result["candidates"]) == 0:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": "No candidates in response"
                }

            candidate = result["candidates"][0]

            # Check if content exists
            if "content" not in candidate:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": "No content in candidate"
                }

            content = candidate["content"]

            # Check if parts exist
            if "parts" not in content or len(content["parts"]) == 0:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": "No parts in content"
                }

            part = content["parts"][0]

            # Check if text exists
            if "text" not in part:
                return {
                    "raw_response": result,
                    "content": "{}",
                    "usage": result.get("usageMetadata", {}),
                    "error": f"No text in part. Available keys: {list(part.keys())}"
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
                "error": f"Failed to extract content: {str(e)}"
            }

        return {
            "raw_response": result,
            "content": content_text,
            "usage": result.get("usageMetadata", {})
        }

    async def process_text(
        self,
        text: str,
        prompt: str,
        schema_definition: Dict[str, Any],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """Process text with Gemini text-only model"""
        # Prepare content (text-only, no image)
        content = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{prompt}\n\nDocument text:\n{text}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema_definition, indent=2)}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"
            }
        }

        try:
            # Make API call
            response = await self.client.post(
                f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=content
            )

            response.raise_for_status()
            result = response.json()

            # Extract content with error handling
            if "candidates" not in result or len(result["candidates"]) == 0:
                return {
                    "error": "No candidates in response",
                    "content": None,
                    "model": model
                }

            candidate = result["candidates"][0]

            if "content" not in candidate:
                return {
                    "error": "No content in candidate",
                    "content": None,
                    "model": model
                }

            content_obj = candidate["content"]

            if "parts" not in content_obj or len(content_obj["parts"]) == 0:
                return {
                    "error": "No parts in content",
                    "content": None,
                    "model": model
                }

            part = content_obj["parts"][0]

            if "text" not in part:
                return {
                    "error": f"No text in part. Available keys: {list(part.keys())}",
                    "content": None,
                    "model": model
                }

            content_text = part["text"]

            if not content_text or content_text.strip() == "":
                return {
                    "error": "Empty content received",
                    "content": None,
                    "model": model
                }

            return {
                "content": content_text,
                "model": model,
                "usage": {
                    "prompt_tokens": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "completion_tokens": result.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                    "total_tokens": result.get("usageMetadata", {}).get("totalTokenCount", 0)
                }
            }

        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "model": model
            }

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available Gemini models with metadata"""
        return [
            # Gemini 3 Series (Latest - Nov/Dec 2025)
            {
                "id": "gemini-3-pro-preview",
                "name": "Gemini 3 Pro Preview",
                "tier": "premium",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Most intelligent multimodal model with advanced reasoning"
            },
            {
                "id": "gemini-3-pro-image-preview",
                "name": "Gemini 3 Pro Image Preview",
                "tier": "premium",
                "capabilities": ["vision", "image_generation"],
                "context_window": 65536,
                "description": "Image generation with advanced vision understanding"
            },
            {
                "id": "gemini-3-flash-preview",
                "name": "Gemini 3 Flash Preview",
                "tier": "balanced",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Balanced speed and intelligence for scale"
            },

            # Gemini 2.5 Series (Stable - Jun/Jul 2025)
            {
                "id": "gemini-2.5-pro",
                "name": "Gemini 2.5 Pro",
                "tier": "premium",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Advanced thinking model for complex reasoning"
            },
            {
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "tier": "balanced",
                "capabilities": ["vision", "thinking", "pdf", "video"],
                "context_window": 1048576,
                "description": "Best price-performance for large-scale processing"
            },
            {
                "id": "gemini-2.5-flash-lite",
                "name": "Gemini 2.5 Flash Lite",
                "tier": "lite",
                "capabilities": ["vision", "thinking", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Fastest, most cost-efficient model"
            },

            # Gemini 2.0 Series (Previous Gen - Feb 2025)
            {
                "id": "gemini-2.0-flash",
                "name": "Gemini 2.0 Flash",
                "tier": "balanced",
                "capabilities": ["vision", "pdf", "video", "audio"],
                "context_window": 1048576,
                "description": "Second generation workhorse, 1M context"
            }
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
