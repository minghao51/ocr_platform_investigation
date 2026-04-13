from abc import ABC, abstractmethod
from typing import Dict, Any, List
import httpx
import base64
from io import BytesIO
from PIL import Image


class VLMProvider(ABC):
    """Base class for VLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Increase timeout to 300 seconds (5 minutes) for VLM processing
        self.client = httpx.AsyncClient(timeout=300.0)

    @abstractmethod
    async def process_image(
        self, image: Image.Image, prompt: str, schema: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Process an image and extract structured data"""
        pass

    @abstractmethod
    async def process_text(
        self,
        text: str,
        prompt: str,
        schema_definition: Dict[str, Any],
        model: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process extracted text with text-only LLM

        Args:
            text: Extracted text content
            prompt: Extraction prompt
            schema_definition: JSON schema for validation
            model: Model name
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Dict with keys:
                - content (str): Extracted JSON content
                - model (str): Model used
                - usage (dict): Token usage stats
                - error (str, optional): Error message if failed
        """
        pass

    @abstractmethod
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with metadata"""
        pass

    @abstractmethod
    def get_default_image_size(self) -> tuple[int, int]:
        """Get default image size for this provider"""
        pass

    def encode_image(self, image: Image.Image, format: str = "JPEG") -> str:
        """Encode image to base64"""
        buffer = BytesIO()
        # Convert RGBA to RGB if needed for JPEG format
        if format == "JPEG" and image.mode == "RGBA":
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
