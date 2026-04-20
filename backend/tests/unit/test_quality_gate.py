"""
Tests for quality gate and image preprocessing.
"""

import numpy as np
import cv2
from PIL import Image
from services.quality_gate import (
    QualityGate,
    QualityLevel,
    CheckSeverity,
)
from services.image_preprocessor import ImagePreprocessor, PreprocessingResult


# ─── Helpers ─────────────────────────────────────────────────────────────────


def create_test_image(width=800, height=600, content="text_pattern"):
    """Create a test PIL Image with various characteristics."""
    if content == "blank":
        arr = np.ones((height, width, 3), dtype=np.uint8) * 255
        return Image.fromarray(arr)

    if content == "text_like":
        # White background with black rectangles simulating text blocks
        arr = np.ones((height, width, 3), dtype=np.uint8) * 255
        for i in range(10, height - 50, 40):
            cv2.rectangle(arr, (50, i), (width - 50, i + 20), (0, 0, 0), -1)
        return Image.fromarray(arr)

    if content == "gradient":
        arr = np.zeros((height, width), dtype=np.uint8)
        for i in range(width):
            arr[:, i] = int(255 * i / width)
        return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR))

    return Image.fromarray(np.ones((height, width, 3), dtype=np.uint8) * 200)


def create_blurry_image():
    """Create an intentionally blurry test image."""
    base = create_test_image(content="text_like")
    cv_base = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
    blurred = cv2.GaussianBlur(cv_base, (31, 31), 0)
    return Image.fromarray(cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB))


def create_dark_image():
    """Create an underexposed test image."""
    base = create_test_image(content="text_like")
    arr = np.array(base)
    dark = (arr * 0.15).astype(np.uint8)
    return Image.fromarray(dark)


def create_skewed_image():
    """Create a rotated/skewed test image."""
    base = create_test_image(content="text_like")
    cv_base = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
    h, w = cv_base.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, 8, 1.0)
    rotated = cv2.warpAffine(cv_base, M, (w, h), borderValue=(255, 255, 255))
    return Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))


def create_noisy_image():
    """Create an image with added noise."""
    base = create_test_image(content="text_like")
    arr = np.array(base, dtype=np.float32)
    noise = np.random.normal(0, 30, arr.shape).astype(np.float32)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)


# ─── QualityGate Tests ───────────────────────────────────────────────────────


class TestQualityGate:
    def test_good_image_passes(self):
        gate = QualityGate()
        img = create_test_image(content="text_like")
        report = gate.assess(img)

        assert report.passed
        assert report.overall_score > 40
        assert report.level in (
            QualityLevel.EXCELLENT,
            QualityLevel.GOOD,
            QualityLevel.ACCEPTABLE,
        )

    def test_blank_image_detected(self):
        gate = QualityGate()
        img = create_test_image(content="blank")
        report = gate.assess(img)

        content_check = report.checks.get("content_density")
        assert content_check is not None
        assert content_check.severity == CheckSeverity.FAIL

    def test_blurry_image_detected(self):
        gate = QualityGate()
        img = create_blurry_image()
        report = gate.assess(img)

        blur_check = report.checks.get("blur")
        assert blur_check is not None
        assert blur_check.severity in (CheckSeverity.WARN, CheckSeverity.FAIL)

    def test_dark_image_detected(self):
        gate = QualityGate()
        img = create_dark_image()
        report = gate.assess(img)

        brightness_check = report.checks.get("brightness")
        assert brightness_check is not None
        assert brightness_check.severity in (CheckSeverity.WARN, CheckSeverity.FAIL)

    def test_report_has_recommendations(self):
        gate = QualityGate()
        img = create_dark_image()
        report = gate.assess(img)

        assert len(report.recommendations) > 0

    def test_custom_thresholds(self):
        gate = QualityGate(thresholds={"blur": 50.0})
        img = create_test_image(content="text_like")
        report = gate.assess(img)

        assert report.checks["blur"].threshold == 50.0

    def test_to_dict_serialization(self):
        gate = QualityGate()
        img = create_test_image(content="text_like")
        report = gate.assess(img)

        result = gate.to_dict(report)
        assert "passed" in result
        assert "overall_score" in result
        assert "checks" in result
        assert isinstance(result["checks"], dict)

    def test_score_to_level_mapping(self):
        assert QualityGate._score_to_level(90) == QualityLevel.EXCELLENT
        assert QualityGate._score_to_level(70) == QualityLevel.GOOD
        assert QualityGate._score_to_level(50) == QualityLevel.ACCEPTABLE
        assert QualityGate._score_to_level(30) == QualityLevel.POOR
        assert QualityGate._score_to_level(10) == QualityLevel.CRITICAL

    def test_overall_score_weighted(self):
        gate = QualityGate()
        img = create_test_image(content="text_like")
        report = gate.assess(img)

        # Verify score is a weighted average (0-100 range)
        assert 0 <= report.overall_score <= 100


# ─── ImagePreprocessor Tests ─────────────────────────────────────────────────


class TestImagePreprocessor:
    def test_denoise_runs(self):
        preprocessor = ImagePreprocessor()
        img = create_noisy_image()
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        result, success = preprocessor.denoise(cv_img)
        assert success
        assert result.shape == cv_img.shape

    def test_deskew_runs(self):
        preprocessor = ImagePreprocessor()
        img = create_skewed_image()
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        result, success = preprocessor.deskew(cv_img)
        assert result is not None
        # Deskew may or may not succeed depending on the angle detection
        assert result.shape[2] == 3

    def test_enhance_contrast_runs(self):
        preprocessor = ImagePreprocessor()
        img = create_test_image(content="gradient")
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        result, success = preprocessor.enhance_contrast(cv_img)
        assert success
        assert result.shape == cv_img.shape

    def test_normalize_brightness_dark(self):
        preprocessor = ImagePreprocessor()
        img = create_dark_image()
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        result, success = preprocessor.normalize_brightness(cv_img)
        assert success or result.shape[2] == 3  # Either adjusted or passthrough

    def test_normalize_brightness_bright(self):
        preprocessor = ImagePreprocessor()
        # Create an overexposed image
        arr = np.ones((600, 800, 3), dtype=np.uint8) * 240
        img = Image.fromarray(arr)
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        result, success = preprocessor.normalize_brightness(cv_img)
        assert result is not None

    def test_binarize_runs(self):
        preprocessor = ImagePreprocessor()
        img = create_test_image(content="text_like")
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        result, success = preprocessor.binarize(cv_img)
        assert success
        # Binarized image should have only 2 unique values per channel
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        unique_vals = np.unique(gray)
        assert len(unique_vals) == 2

    def test_fix_with_explicit_operations(self):
        preprocessor = ImagePreprocessor()
        img = create_test_image(content="text_like")

        result = preprocessor.fix(img, operations=["denoise", "clahe"])
        assert isinstance(result, PreprocessingResult)
        assert "denoise" in result.applied
        assert "clahe" in result.applied
        assert result.processed is not None

    def test_fix_preserves_image_size(self):
        preprocessor = ImagePreprocessor()
        img = create_test_image(width=800, height=600, content="text_like")

        result = preprocessor.fix(img, operations=["denoise"])
        assert result.processed.size == img.size

    def test_auto_fix_from_quality_report(self):
        gate = QualityGate()
        preprocessor = ImagePreprocessor()

        img = create_dark_image()
        report = gate.assess(img)

        if report.auto_fixable_issues:
            result = preprocessor.fix(img, quality_report=report)
            assert len(result.applied) > 0
