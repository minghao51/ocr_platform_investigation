from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
import base64
from io import BytesIO
from PIL import Image

class VLMProvider(ABC):
    """Base class for VLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    @abstractmethod
    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Process an image and extract structured data"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models"""
        pass

    @abstractmethod
    def get_default_image_size(self) -> tuple[int, int]:
        """Get default image size for this provider"""
        pass

    def encode_image(self, image: Image.Image, format: str = "JPEG") -> str:
        """Encode image to base64"""
        buffer = BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
