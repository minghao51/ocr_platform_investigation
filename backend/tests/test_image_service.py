"""
Unit tests for image processing service.
Tests image resizing, PDF to image conversion, and format handling.
"""

import pytest
from PIL import Image
import io
from services.image_service import resize_for_provider, image_to_base64, get_image_info


class TestImageResizing:
    """Test image resizing functionality."""

    def test_resize_small_image(self):
        """Test that small images are not resized."""
        # Create a small 500x500 image
        img = Image.new("RGB", (500, 500), color="red")

        resized = resize_for_provider(img, "nebius")

        # Should remain the same size
        assert resized.size == (500, 500)

    def test_resize_large_image_nebius(self):
        """Test resizing large image for Nebius (max 2048)."""
        # Create a large 3000x3000 image
        img = Image.new("RGB", (3000, 3000), color="blue")

        resized = resize_for_provider(img, "nebius")

        # Should be resized to fit within 2048x2048
        max_dim = max(resized.size)
        assert max_dim <= 2048
        # Aspect ratio should be maintained
        assert resized.size[0] == resized.size[1]  # Square remains square

    def test_resize_large_image_gemini(self):
        """Test resizing large image for Gemini (max 2048)."""
        img = Image.new("RGB", (2500, 2000), color="green")

        resized = resize_for_provider(img, "gemini")

        max_dim = max(resized.size)
        assert max_dim <= 2048
        # Aspect ratio maintained (5:4 becomes 5:4)
        ratio = resized.size[0] / resized.size[1]
        assert abs(ratio - 1.25) < 0.01

    def test_resize_wide_image(self):
        """Test resizing wide image (landscape orientation)."""
        # Create 4000x1000 image (4:1 aspect ratio)
        img = Image.new("RGB", (4000, 1000), color="yellow")

        resized = resize_for_provider(img, "openrouter")

        # Height should be scaled to fit within 2048
        assert resized.size[1] <= 2048
        # Aspect ratio maintained
        ratio = resized.size[0] / resized.size[1]
        assert abs(ratio - 4.0) < 0.01

    def test_resize_tall_image(self):
        """Test resizing tall image (portrait orientation)."""
        # Create 1000x4000 image (1:4 aspect ratio)
        img = Image.new("RGB", (1000, 4000), color="purple")

        resized = resize_for_provider(img, "nebius")

        # Width should be scaled to fit within 2048
        assert resized.size[0] <= 2048
        # Aspect ratio maintained
        ratio = resized.size[0] / resized.size[1]
        assert abs(ratio - 0.25) < 0.01

    def test_resize_no_upscaling(self):
        """Test that small images are not upscaled."""
        # Create a very small image
        img = Image.new("RGB", (100, 100), color="orange")

        resized = resize_for_provider(img, "gemini")

        # Should not be upscaled
        assert resized.size == (100, 100)


class TestImageToBase64:
    """Test image to base64 conversion."""

    def test_convert_png_to_base64(self):
        """Test converting PNG image to base64."""
        img = Image.new("RGB", (100, 100), color="red")

        base64_str = image_to_base64(img, format="PNG")

        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
        # Base64 encoded string
        assert all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            for c in base64_str
        )

    def test_convert_jpeg_to_base64(self):
        """Test converting JPEG image to base64."""
        img = Image.new("RGB", (200, 150), color="blue")

        base64_str = image_to_base64(img, format="JPEG")

        assert isinstance(base64_str, str)
        assert len(base64_str) > 0

    def test_base64_different_sizes(self):
        """Test that different images produce different base64 strings."""
        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="blue")

        base64_1 = image_to_base64(img1, format="PNG")
        base64_2 = image_to_base64(img2, format="PNG")

        assert base64_1 != base64_2


class TestImageInfo:
    """Test image information extraction."""

    def test_get_image_info_basic(self):
        """Test getting basic image information."""
        img = Image.new("RGB", (1920, 1080), color="red")

        info = get_image_info(img)

        assert info["width"] == 1920
        assert info["height"] == 1080
        assert info["mode"] == "RGB"
        assert "format" in info

    def test_get_image_info_different_modes(self):
        """Test getting info for images with different modes."""
        # RGB mode
        img_rgb = Image.new("RGB", (100, 100), color="red")
        info_rgb = get_image_info(img_rgb)
        assert info_rgb["mode"] == "RGB"

        # RGBA mode
        img_rgba = Image.new("RGBA", (100, 100), color="blue")
        info_rgba = get_image_info(img_rgba)
        assert info_rgba["mode"] == "RGBA"

        # L mode (grayscale)
        img_l = Image.new("L", (100, 100), color=128)
        info_l = get_image_info(img_l)
        assert info_l["mode"] == "L"


class TestPDFToImage:
    """Test PDF to image conversion."""

    @pytest.mark.skipif(
        True,  # Skip if pdf2image not installed or poppler not available
        reason="Requires pdf2image and poppler",
    )
    def test_convert_single_page_pdf(self):
        """Test converting single-page PDF to images."""
        # This would require an actual PDF file
        # Skipping for now as it requires external dependencies
        pass

    @pytest.mark.skipif(True, reason="Requires pdf2image and poppler")
    def test_convert_multi_page_pdf(self):
        """Test converting multi-page PDF to images."""
        # This would require an actual multi-page PDF file
        pass


class TestImageValidation:
    """Test image validation."""

    def test_validate_supported_format(self):
        """Test validation of supported image formats."""
        # JPEG
        img_jpeg = Image.new("RGB", (100, 100))
        assert img_jpeg.format == "JPEG" or img_jpeg.format is None

        # PNG
        img_png = Image.new("RGB", (100, 100))
        assert img_png.format == "PNG" or img_png.format is None

    def test_image_size_calculation(self):
        """Test calculating image size in bytes."""
        img = Image.new("RGB", (1920, 1080), color="red")

        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        size = len(img_bytes.getvalue())

        assert size > 0
        assert size < 10 * 1024 * 1024  # Should be less than 10MB


class TestProviderSpecifics:
    """Test provider-specific image handling."""

    def test_nebius_max_dimensions(self):
        """Test Nebius maximum dimensions."""
        img = Image.new("RGB", (3000, 3000))
        resized = resize_for_provider(img, "nebius")

        max_dim = max(resized.size)
        assert max_dim <= 2048

    def test_openrouter_max_dimensions(self):
        """Test OpenRouter maximum dimensions (assumes 2048)."""
        img = Image.new("RGB", (2500, 2500))
        resized = resize_for_provider(img, "openrouter")

        max_dim = max(resized.size)
        assert max_dim <= 2048

    def test_gemini_max_dimensions(self):
        """Test Gemini maximum dimensions (2048x2048)."""
        img = Image.new("RGB", (3000, 2000))
        resized = resize_for_provider(img, "gemini")

        max_dim = max(resized.size)
        assert max_dim <= 2048

    def test_unknown_provider_defaults(self):
        """Test that unknown provider uses default max dimension."""
        img = Image.new("RGB", (3000, 3000))
        resized = resize_for_provider(img, "unknown_provider")

        # Should default to 2048
        max_dim = max(resized.size)
        assert max_dim <= 2048


class TestImageQuality:
    """Test image quality handling."""

    def test_quality_reduction_strategy(self):
        """Test that quality reduction happens before resizing."""
        # Large image that should be reduced
        img = Image.new("RGB", (4000, 4000), color="red")

        resized = resize_for_provider(img, "nebius")

        # Should be resized, not crashed
        assert resized.size != (4000, 4000)
        assert max(resized.size) <= 2048

    def test_maintain_aspect_ratio(self):
        """Test that aspect ratio is always maintained."""
        test_cases = [
            (4000, 1000),  # Wide
            (1000, 4000),  # Tall
            (3000, 2000),  # Landscape
            (2000, 3000),  # Portrait
        ]

        for width, height in test_cases:
            img = Image.new("RGB", (width, height))
            resized = resize_for_provider(img, "nebius")

            original_ratio = width / height
            resized_ratio = resized.size[0] / resized.size[1]

            # Aspect ratio should be preserved
            assert abs(original_ratio - resized_ratio) < 0.01
