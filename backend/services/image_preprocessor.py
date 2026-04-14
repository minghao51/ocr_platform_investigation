"""
Image Preprocessor for OCR Quality Improvement

Auto-corrects image quality issues detected by the quality gate:
- Deskew (rotation correction)
- Contrast enhancement (CLAHE)
- Denoising
- Binarization
- Brightness/contrast normalization
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingResult:
    """Result of preprocessing an image."""

    original: Image.Image
    processed: Image.Image
    applied: list[str] = field(default_factory=list)
    quality_improvement: float = 0.0  # Score delta
    metadata: dict = field(default_factory=dict)


class ImagePreprocessor:
    """
    Applies corrective operations to images before VLM processing.

    Usage:
        preprocessor = ImagePreprocessor()
        result = preprocessor.fix(image, quality_report)
        # result.processed is the improved image
    """

    def __init__(self):
        pass

    def fix(
        self,
        image: Image.Image,
        quality_report=None,
        operations: Optional[list[str]] = None,
    ) -> PreprocessingResult:
        """
        Apply automatic corrections to an image based on quality report
        or explicit operation list.

        Args:
            image: PIL Image to preprocess
            quality_report: QualityReport from QualityGate (used to decide what to fix)
            operations: Explicit list of operations to apply (overrides quality report)
                       Options: "deskew", "denoise", "clahe", "normalize", "binarize"

        Returns:
            PreprocessingResult with original, processed image, and metadata
        """
        original = image.copy()
        cv_image = self._pil_to_cv(image)
        applied = []

        if operations is not None:
            # Use explicit operation list
            for op in operations:
                cv_image, success = self._apply_operation(cv_image, op)
                if success:
                    applied.append(op)
        elif quality_report is not None:
            # Auto-detect operations from quality report
            cv_image, applied = self._auto_fix(cv_image, quality_report)
        else:
            # Default: apply all safe corrections
            cv_image, applied = self._apply_all(cv_image)

        processed = self._cv_to_pil(cv_image)

        # Build metadata
        metadata = {
            "original_size": image.size,
            "processed_size": processed.size,
            "operations_applied": applied,
        }

        return PreprocessingResult(
            original=original,
            processed=processed,
            applied=applied,
            metadata=metadata,
        )

    def deskew(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Detect and correct document skew.
        Returns (corrected_image, success).
        """
        gray = self._to_gray(image)
        h, w = gray.shape

        # Threshold to get text regions
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        thresh = cv2.bitwise_not(thresh)

        # Find contours of text blobs
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) < 3:
            # Fallback: use Hough lines
            return self._deskew_hough(image)

        # Get bounding boxes and compute angles
        angles = []
        for contour in contours:
            rect = cv2.minAreaRect(contour)
            angle = rect[2]

            # Normalize angle
            if rect[1][0] < rect[1][1]:
                angle = angle - 90

            # Only consider significant contours (filter tiny ones)
            area = cv2.contourArea(contour)
            min_area = (h * w) * 0.0001  # At least 0.01% of image
            if area > min_area and abs(angle) > 0.5:
                angles.append(angle)

        if len(angles) < 3:
            return self._deskew_hough(image)

        skew_angle = float(np.median(angles))

        if abs(skew_angle) < 0.3:
            return image, False  # No significant skew

        # Rotate to correct
        center = (w // 2, h // 2)
        rot_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)

        # Compute new bounding to avoid cropping
        cos = abs(rot_matrix[0, 0])
        sin = abs(rot_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        rot_matrix[0, 2] += (new_w / 2) - center[0]
        rot_matrix[1, 2] += (new_h / 2) - center[1]

        rotated = cv2.warpAffine(
            image,
            rot_matrix,
            (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
            borderValue=(255, 255, 255),
        )

        logger.info(f"Deskewed image by {skew_angle:.1f}°")
        return rotated, True

    def _deskew_hough(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """Fallback deskew using Hough line transform."""
        gray = self._to_gray(image)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=100,
            minLineLength=min(gray.shape[1] * 0.3, 200),
            maxLineGap=10,
        )

        if lines is None or len(lines) < 3:
            return image, False

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 == x1:
                continue
            angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
            angles.append(angle)

        skew_angle = float(np.median(angles))
        if skew_angle < -45:
            skew_angle += 90
        elif skew_angle > 45:
            skew_angle -= 90

        if abs(skew_angle) < 0.3:
            return image, False

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rot_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)

        cos = abs(rot_matrix[0, 0])
        sin = abs(rot_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        rot_matrix[0, 2] += (new_w / 2) - center[0]
        rot_matrix[1, 2] += (new_h / 2) - center[1]

        rotated = cv2.warpAffine(
            image,
            rot_matrix,
            (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
            borderValue=(255, 255, 255),
        )

        logger.info(f"Deskewed image by {skew_angle:.1f}° (Hough)")
        return rotated, True

    def denoise(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Apply non-local means denoising.
        Good for scan noise and JPEG artifacts.
        """
        if len(image.shape) == 2 or image.shape[2] == 1:
            gray = self._to_gray(image)
            denoised = cv2.fastNlMeansDenoising(
                gray, h=10, templateWindowSize=7, searchWindowSize=21
            )
            result = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
        else:
            result = cv2.fastNlMeansDenoisingColored(
                image,
                None,
                10,
                10,
                7,
                21,
            )

        return result, True

    def enhance_contrast(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
        Improves local contrast without over-amplifying noise.
        """
        gray = self._to_gray(image)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Convert back to BGR for compatibility
        result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        return result, True

    def normalize_brightness(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Normalize brightness to target range.
        Uses gamma correction for non-linear adjustment.
        """
        gray = self._to_gray(image)
        mean_brightness = float(np.mean(gray))

        # Target brightness range: 120-160 (mid-range)
        target = 140.0

        if 80 <= mean_brightness <= 200:
            return image, False  # Already in good range

        # Compute gamma
        if mean_brightness < 80:
            # Too dark — increase brightness (gamma < 1)
            gamma = mean_brightness / target
        else:
            # Too bright — decrease brightness (gamma > 1)
            gamma = (255 - mean_brightness) / (255 - target)

        gamma = max(0.3, min(2.5, gamma))  # Clamp to reasonable range

        # Build lookup table
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(
            "uint8"
        )

        if len(image.shape) == 2 or image.shape[2] == 1:
            result = cv2.LUT(gray, table)
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        else:
            result = cv2.LUT(image, table)

        logger.info(
            f"Brightness normalized: {mean_brightness:.0f} → {target:.0f} (gamma={gamma:.2f})"
        )
        return result, True

    def binarize(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Apply Otsu's binarization for maximum text clarity.
        Produces pure black-and-white output.
        """
        gray = self._to_gray(image)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        return result, True

    # ─── Auto-fix Logic ─────────────────────────────────────────────────────

    def _auto_fix(
        self, cv_image: np.ndarray, quality_report
    ) -> tuple[np.ndarray, list[str]]:
        """Apply corrections based on quality report failures."""
        applied = []
        checks = quality_report.checks

        # Order matters: denoise before CLAHE, deskew before everything
        if (
            "skew" in checks
            and checks["skew"].auto_fixable
            and checks["skew"].severity != "pass"
        ):
            cv_image, success = self.deskew(cv_image)
            if success:
                applied.append("deskew")

        if (
            "noise" in checks
            and checks["noise"].auto_fixable
            and checks["noise"].severity != "pass"
        ):
            cv_image, success = self.denoise(cv_image)
            if success:
                applied.append("denoise")

        if (
            "contrast" in checks
            and checks["contrast"].auto_fixable
            and checks["contrast"].severity != "pass"
        ):
            cv_image, success = self.enhance_contrast(cv_image)
            if success:
                applied.append("clahe")

        if (
            "brightness" in checks
            and checks["brightness"].auto_fixable
            and checks["brightness"].severity != "pass"
        ):
            cv_image, success = self.normalize_brightness(cv_image)
            if success:
                applied.append("normalize")

        return cv_image, applied

    def _apply_all(self, cv_image: np.ndarray) -> tuple[np.ndarray, list[str]]:
        """Apply all safe corrections unconditionally."""
        applied = []

        # Always denoise first (improves subsequent operations)
        cv_image, success = self.denoise(cv_image)
        if success:
            applied.append("denoise")

        # Then enhance contrast
        cv_image, success = self.enhance_contrast(cv_image)
        if success:
            applied.append("clahe")

        return cv_image, applied

    def _apply_operation(
        self, cv_image: np.ndarray, operation: str
    ) -> tuple[np.ndarray, bool]:
        """Apply a single named operation."""
        operations = {
            "deskew": self.deskew,
            "denoise": self.denoise,
            "clahe": self.enhance_contrast,
            "normalize": self.normalize_brightness,
            "binarize": self.binarize,
        }

        func = operations.get(operation)
        if func is None:
            logger.warning(f"Unknown preprocessing operation: {operation}")
            return cv_image, False

        return func(cv_image)

    # ─── Image Conversion Helpers ───────────────────────────────────────────

    @staticmethod
    def _pil_to_cv(image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV BGR format."""
        rgb = image.convert("RGB")
        return cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _cv_to_pil(image: np.ndarray) -> Image.Image:
        """Convert OpenCV BGR to PIL Image."""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        """Convert to grayscale."""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
