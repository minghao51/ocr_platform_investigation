"""
Pre-OCR Image Quality Gate

Assesses image quality before sending to VLM APIs to:
- Reject images that will produce poor results (save cost)
- Identify auto-fixable issues (deskew, contrast, denoise)
- Provide quality metrics for benchmarking and user feedback
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Overall quality assessment levels."""

    EXCELLENT = "excellent"  # 80-100: No issues, ready for VLM
    GOOD = "good"  # 60-79: Minor issues, still fine
    ACCEPTABLE = "acceptable"  # 40-59: Noticeable issues but usable
    POOR = "poor"  # 20-39: Significant quality problems
    CRITICAL = "critical"  # 0-19: Reject - will fail


class CheckSeverity(str, Enum):
    """Severity of individual quality checks."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class QualityCheck:
    """Result of a single quality check."""

    name: str
    severity: CheckSeverity
    score: float  # 0-100, higher is better
    value: float  # Raw measurement
    threshold: float  # Pass/fail threshold
    message: str = ""
    auto_fixable: bool = False
    fix_recommendation: str = ""


@dataclass
class QualityReport:
    """Complete quality assessment for an image."""

    passed: bool
    overall_score: float
    level: QualityLevel
    checks: dict[str, QualityCheck]
    recommendations: list[str] = field(default_factory=list)
    auto_fixable_issues: list[str] = field(default_factory=list)
    should_reject: bool = False
    rejection_reason: str = ""


# Default thresholds - tunable via settings
DEFAULT_THRESHOLDS = {
    "blur": 100.0,  # Laplacian variance below this = blurry
    "skew_degrees": 2.0,  # Degrees above this = skewed
    "noise_level": 50.0,  # Normalized noise above this = noisy
    "contrast_min": 30.0,  # Std dev below this = low contrast
    "contrast_max": 120.0,  # Std dev above this = high contrast (usually ok)
    "brightness_min": 40.0,  # Mean below this = too dark
    "brightness_max": 220.0,  # Mean above this = too bright/washed out
    "content_density": 0.02,  # Non-white pixel ratio below this = near-blank
    "min_dpi": 150,  # Effective DPI below this = low resolution
}

# Weights for overall score computation
CHECK_WEIGHTS = {
    "blur": 0.30,  # Most critical for text recognition
    "skew": 0.15,
    "noise": 0.15,
    "contrast": 0.15,
    "brightness": 0.10,
    "content_density": 0.10,
    "resolution": 0.05,
}


class QualityGate:
    """
    Pre-OCR quality gate that assesses images before VLM processing.

    Usage:
        gate = QualityGate()
        report = gate.assess(pil_image)
        if not report.passed:
            # reject or preprocess
    """

    def __init__(self, thresholds: Optional[dict] = None):
        self.thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    def assess(self, image: Image.Image, estimated_dpi: int = 200) -> QualityReport:
        """
        Run all quality checks on an image.

        Args:
            image: PIL Image to assess
            estimated_dpi: Known or estimated DPI of the source image

        Returns:
            QualityReport with all check results and recommendations
        """
        # Convert PIL to OpenCV format (BGR grayscale)
        cv_image = self._pil_to_cv(image)

        checks: dict[str, QualityCheck] = {}

        checks["blur"] = self._check_blur(cv_image)
        checks["skew"] = self._check_skew(cv_image)
        checks["noise"] = self._check_noise(cv_image)
        checks["contrast"] = self._check_contrast(cv_image)
        checks["brightness"] = self._check_brightness(cv_image)
        checks["content_density"] = self._check_content_density(cv_image)
        checks["resolution"] = self._check_resolution(cv_image, estimated_dpi)

        # Compute overall weighted score
        overall_score = self._compute_overall_score(checks)

        # Determine quality level
        level = self._score_to_level(overall_score)

        # Generate recommendations
        recommendations = []
        auto_fixable = []
        for name, check in checks.items():
            if check.severity != CheckSeverity.PASS:
                recommendations.append(check.message)
                if check.auto_fixable:
                    auto_fixable.append(check.fix_recommendation)

        # Determine pass/fail
        should_reject = overall_score < 20  # Critical level
        passed = overall_score >= 40  # Acceptable or better

        report = QualityReport(
            passed=passed,
            overall_score=round(overall_score, 1),
            level=level,
            checks=checks,
            recommendations=recommendations,
            auto_fixable_issues=auto_fixable,
            should_reject=should_reject,
            rejection_reason="Image quality is critically poor. "
            "VLM extraction will likely fail. "
            "Please provide a higher quality image."
            if should_reject
            else "",
        )

        return report

    def assess_from_cv(
        self, cv_image: np.ndarray, estimated_dpi: int = 200
    ) -> QualityReport:
        """Assess quality from an OpenCV image (numpy array)."""
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        return self.assess(pil_image, estimated_dpi)

    # ─── Individual Quality Checks ──────────────────────────────────────────

    def _check_blur(self, image: np.ndarray) -> QualityCheck:
        """
        Detect blur using Laplacian variance.
        Sharp images have high variance; blurry images have low variance.
        """
        gray = self._to_gray(image)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        threshold = self.thresholds["blur"]
        # Score: 0 at 0 variance, 100 at 2x threshold
        score = min(100.0, (laplacian_var / (threshold * 2)) * 100)

        if laplacian_var >= threshold:
            severity = CheckSeverity.PASS
            message = "Image is sharp"
        elif laplacian_var >= threshold * 0.5:
            severity = CheckSeverity.WARN
            message = (
                f"Image is slightly blurry (Laplacian variance: {laplacian_var:.1f})"
            )
        else:
            severity = CheckSeverity.FAIL
            message = f"Image is too blurry (Laplacian variance: {laplacian_var:.1f})"

        return QualityCheck(
            name="blur",
            severity=severity,
            score=round(score, 1),
            value=round(laplacian_var, 1),
            threshold=threshold,
            message=message,
            auto_fixable=False,
            fix_recommendation="Re-scan or re-capture at higher resolution",
        )

    def _check_skew(self, image: np.ndarray) -> QualityCheck:
        """
        Detect document skew using Hough line transform.
        Text lines should be horizontal; deviation = skew.
        """
        gray = self._to_gray(image)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough line detection
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=100,
            minLineLength=min(gray.shape[1] * 0.3, 200),
            maxLineGap=10,
        )

        if lines is None or len(lines) < 3:
            # Not enough lines to determine skew — may be a photo, not a document
            return QualityCheck(
                name="skew",
                severity=CheckSeverity.PASS,
                score=80.0,
                value=0.0,
                threshold=self.thresholds["skew_degrees"],
                message="Insufficient lines to detect skew",
                auto_fixable=False,
            )

        # Calculate median angle
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 == x1:
                continue
            angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
            angles.append(angle)

        skew_angle = float(np.median(angles))
        # Normalize to -90 to +90 range
        if skew_angle < -45:
            skew_angle += 90
        elif skew_angle > 45:
            skew_angle -= 90

        abs_skew = abs(skew_angle)
        threshold = self.thresholds["skew_degrees"]

        # Score: 100 at 0°, 0 at 2x threshold
        score = max(0.0, 100.0 - (abs_skew / (threshold * 2)) * 100)

        if abs_skew <= threshold:
            severity = CheckSeverity.PASS
            message = f"Skew angle: {skew_angle:.1f}° (within tolerance)"
        elif abs_skew <= threshold * 2:
            severity = CheckSeverity.WARN
            message = f"Skew detected: {skew_angle:.1f}°"
        else:
            severity = CheckSeverity.FAIL
            message = f"Significant skew detected: {skew_angle:.1f}°"

        return QualityCheck(
            name="skew",
            severity=severity,
            score=round(score, 1),
            value=round(skew_angle, 2),
            threshold=threshold,
            message=message,
            auto_fixable=True,
            fix_recommendation=f"Deskew by {-skew_angle:.1f}°",
        )

    def _check_noise(self, image: np.ndarray) -> QualityCheck:
        """
        Estimate noise level using local variance in homogeneous regions.
        """
        gray = self._to_gray(image)

        # Apply Gaussian blur to create a "clean" reference
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Noise estimate = difference between original and blurred
        noise = cv2.absdiff(gray, blurred)
        noise_level = float(np.mean(noise))

        # Normalize to 0-100 scale (typical max diff is ~80 for very noisy)
        threshold = self.thresholds["noise_level"]
        score = max(0.0, min(100.0, 100.0 - (noise_level / threshold) * 100))

        if noise_level <= threshold * 0.5:
            severity = CheckSeverity.PASS
            message = f"Low noise level ({noise_level:.1f})"
        elif noise_level <= threshold:
            severity = CheckSeverity.WARN
            message = f"Moderate noise detected ({noise_level:.1f})"
        else:
            severity = CheckSeverity.FAIL
            message = f"High noise level ({noise_level:.1f})"

        return QualityCheck(
            name="noise",
            severity=severity,
            score=round(score, 1),
            value=round(noise_level, 1),
            threshold=threshold,
            message=message,
            auto_fixable=True,
            fix_recommendation="Apply denoising filter",
        )

    def _check_contrast(self, image: np.ndarray) -> QualityCheck:
        """
        Check contrast using standard deviation of pixel intensities.
        Low contrast = washed-out scan; very high = usually fine for documents.
        """
        gray = self._to_gray(image)
        contrast = float(np.std(gray))

        min_threshold = self.thresholds["contrast_min"]
        max_threshold = self.thresholds["contrast_max"]

        if contrast >= min_threshold and contrast <= max_threshold:
            severity = CheckSeverity.PASS
            score = min(
                100.0,
                80.0
                + ((contrast - min_threshold) / (max_threshold - min_threshold)) * 20,
            )
            message = f"Good contrast (σ={contrast:.1f})"
        elif contrast >= min_threshold * 0.5:
            severity = CheckSeverity.WARN
            score = min(100.0, (contrast / min_threshold) * 50)
            message = f"Low contrast (σ={contrast:.1f})"
        else:
            severity = CheckSeverity.FAIL
            score = max(0.0, (contrast / (min_threshold * 0.5)) * 20)
            message = f"Very low contrast (σ={contrast:.1f})"

        return QualityCheck(
            name="contrast",
            severity=severity,
            score=round(score, 1),
            value=round(contrast, 1),
            threshold=min_threshold,
            message=message,
            auto_fixable=True,
            fix_recommendation="Apply contrast enhancement (CLAHE)",
        )

    def _check_brightness(self, image: np.ndarray) -> QualityCheck:
        """
        Check brightness using mean pixel intensity.
        Too dark = underexposed; too bright = washed out.
        """
        gray = self._to_gray(image)
        brightness = float(np.mean(gray))

        min_threshold = self.thresholds["brightness_min"]
        max_threshold = self.thresholds["brightness_max"]

        if min_threshold <= brightness <= max_threshold:
            severity = CheckSeverity.PASS
            score = 80.0  # Good range
            message = f"Normal brightness (μ={brightness:.1f})"
        elif brightness < min_threshold:
            if brightness >= min_threshold * 0.6:
                severity = CheckSeverity.WARN
                score = (brightness / min_threshold) * 60
            else:
                severity = CheckSeverity.FAIL
                score = max(0.0, (brightness / (min_threshold * 0.6)) * 30)
            message = f"Image too dark (μ={brightness:.1f})"
        else:
            if brightness <= max_threshold * 1.2:
                severity = CheckSeverity.WARN
                score = max(
                    0.0,
                    80.0 - ((brightness - max_threshold) / (max_threshold * 0.2)) * 30,
                )
            else:
                severity = CheckSeverity.FAIL
                score = max(
                    0.0,
                    50.0 - ((brightness - max_threshold * 1.2) / max_threshold) * 50,
                )
            message = f"Image too bright/washed out (μ={brightness:.1f})"

        return QualityCheck(
            name="brightness",
            severity=severity,
            score=round(score, 1),
            value=round(brightness, 1),
            threshold=min_threshold,
            message=message,
            auto_fixable=True,
            fix_recommendation="Adjust brightness and contrast",
        )

    def _check_content_density(self, image: np.ndarray) -> QualityCheck:
        """
        Check if the image has meaningful content (not blank/near-empty).
        Uses Otsu's threshold to count non-background pixels.
        """
        gray = self._to_gray(image)

        # Otsu's thresholding to separate content from background
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Count non-zero (content) pixels
        total_pixels = binary.shape[0] * binary.shape[1]
        content_pixels = cv2.countNonZero(binary)
        density = content_pixels / total_pixels if total_pixels > 0 else 0

        threshold = self.thresholds["content_density"]

        if density >= threshold:
            severity = CheckSeverity.PASS
            score = min(100.0, (density / (threshold * 5)) * 100)
            message = f"Content density: {density:.3f} (adequate)"
        elif density >= threshold * 0.3:
            severity = CheckSeverity.WARN
            score = (density / threshold) * 50
            message = f"Low content density: {density:.3f} (mostly blank page?)"
        else:
            severity = CheckSeverity.FAIL
            score = max(0.0, (density / (threshold * 0.3)) * 20)
            message = f"Very low content density: {density:.3f} (likely blank)"

        return QualityCheck(
            name="content_density",
            severity=severity,
            score=round(score, 1),
            value=round(density, 4),
            threshold=threshold,
            message=message,
            auto_fixable=False,
            fix_recommendation="Verify the document has content to extract",
        )

    def _check_resolution(self, image: np.ndarray, estimated_dpi: int) -> QualityCheck:
        """
        Check if the image resolution (DPI) is adequate for text extraction.
        Minimum ~150 DPI for readable text; 300+ is ideal.
        """
        threshold = self.thresholds["min_dpi"]
        height, width = image.shape[:2]

        # Also check absolute pixel dimensions
        min_dimension = min(height, width)
        if min_dimension < 200:
            # Very small image regardless of DPI
            return QualityCheck(
                name="resolution",
                severity=CheckSeverity.FAIL,
                score=10.0,
                value=estimated_dpi,
                threshold=threshold,
                message=f"Image too small ({width}x{height}px)",
                auto_fixable=True,
                fix_recommendation=f"Increase DPI to at least {threshold}",
            )

        if estimated_dpi >= 300:
            severity = CheckSeverity.PASS
            score = 100.0
            message = f"High resolution ({estimated_dpi} DPI)"
        elif estimated_dpi >= threshold:
            severity = CheckSeverity.PASS
            score = 70.0
            message = f"Adequate resolution ({estimated_dpi} DPI)"
        elif estimated_dpi >= threshold * 0.7:
            severity = CheckSeverity.WARN
            score = 45.0
            message = f"Low resolution ({estimated_dpi} DPI, recommend {threshold}+)"
        else:
            severity = CheckSeverity.FAIL
            score = max(0.0, (estimated_dpi / (threshold * 0.7)) * 40)
            message = (
                f"Very low resolution ({estimated_dpi} DPI, recommend {threshold}+)"
            )

        return QualityCheck(
            name="resolution",
            severity=severity,
            score=round(score, 1),
            value=estimated_dpi,
            threshold=threshold,
            message=message,
            auto_fixable=True,
            fix_recommendation=f"Re-render at higher DPI (recommended: {max(threshold, 300)})",
        )

    # ─── Scoring Utilities ─────────────────────────────────────────────────

    def _compute_overall_score(self, checks: dict[str, QualityCheck]) -> float:
        """Compute weighted overall score."""
        total = 0.0
        total_weight = 0.0
        for name, check in checks.items():
            weight = CHECK_WEIGHTS.get(name, 0.1)
            total += check.score * weight
            total_weight += weight
        return total / total_weight if total_weight > 0 else 0

    @staticmethod
    def _score_to_level(score: float) -> QualityLevel:
        """Convert numeric score to quality level."""
        if score >= 80:
            return QualityLevel.EXCELLENT
        elif score >= 60:
            return QualityLevel.GOOD
        elif score >= 40:
            return QualityLevel.ACCEPTABLE
        elif score >= 20:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    # ─── Image Conversion Helpers ───────────────────────────────────────────

    @staticmethod
    def _pil_to_cv(image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format (BGR numpy array)."""
        rgb = image.convert("RGB")
        bgr = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        return bgr

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        """Convert to grayscale if needed."""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def to_dict(self, report: QualityReport) -> dict:
        """Serialize a QualityReport for API/JSON response."""
        checks_dict = {}
        for name, check in report.checks.items():
            checks_dict[name] = asdict(check)
        return {
            "passed": report.passed,
            "overall_score": report.overall_score,
            "level": report.level.value,
            "checks": checks_dict,
            "recommendations": report.recommendations,
            "auto_fixable_issues": report.auto_fixable_issues,
            "should_reject": report.should_reject,
            "rejection_reason": report.rejection_reason,
        }
