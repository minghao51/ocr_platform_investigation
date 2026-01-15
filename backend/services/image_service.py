from pathlib import Path
from typing import List
from PIL import Image
import pdf2image
from io import BytesIO

class ImageService:
    """Service for processing images and PDFs"""

    @staticmethod
    def load_image(file_path: str) -> Image.Image:
        """Load an image file"""
        return Image.open(file_path)

    @staticmethod
    def resize_image(
        image: Image.Image,
        target_size: tuple[int, int],
        maintain_aspect: bool = True
    ) -> Image.Image:
        """Resize image to target size"""

        if maintain_aspect:
            # Calculate aspect ratio
            aspect_ratio = image.width / image.height
            target_width, target_height = target_size

            if aspect_ratio > target_width / target_height:
                # Width is limiting factor
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                # Height is limiting factor
                new_height = target_height
                new_width = int(target_height * aspect_ratio)

            return image.resize((new_width, new_height), Image.LANCZOS)
        else:
            return image.resize(target_size, Image.LANCZOS)

    @staticmethod
    def pdf_to_images(
        pdf_path: str,
        dpi: int = 200,
        first_page: int = None,
        last_page: int = None
    ) -> List[Image.Image]:
        """Convert PDF to list of images"""

        images = pdf2image.convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=first_page,
            last_page=last_page
        )

        return images

    @staticmethod
    def optimize_image(image: Image.Image, max_size: int = 5 * 1024 * 1024) -> bytes:
        """Optimize image to stay under size limit"""

        # Try different quality levels
        for quality in [95, 85, 75, 65, 55]:
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            size = buffer.tell()

            if size <= max_size:
                return buffer.getvalue()

        # If still too large, resize
        width, height = image.size
        scale = 0.9
        while scale > 0.1:
            new_size = (int(width * scale), int(height * scale))
            resized = image.resize(new_size, Image.LANCZOS)

            for quality in [85, 75, 65]:
                buffer = BytesIO()
                resized.save(buffer, format="JPEG", quality=quality, optimize=True)
                if buffer.tell() <= max_size:
                    return buffer.getvalue()

            scale -= 0.1

        raise ValueError("Unable to optimize image to target size")
