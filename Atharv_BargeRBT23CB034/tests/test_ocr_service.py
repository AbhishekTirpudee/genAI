"""
Unit tests for services/ocr_service.py.
Tests image sharpness calculation, blur detection, enhancement filters,
and OCR extraction pipeline.
"""

from unittest.mock import patch, MagicMock
import pytest
from PIL import Image, ImageDraw, ImageFilter

from services.ocr_service import (
    calculate_image_clarity,
    preprocess_for_ocr,
    extract_ocr_text,
    analyze_image_clarity_and_ocr,
)


def create_test_text_image(text: str = "VISIONQA TEST 2026", size=(400, 100)) -> Image.Image:
    """Helper to generate an image with high-contrast text."""
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    # Draw simple high-contrast geometric text lines
    draw.rectangle([10, 10, 390, 90], outline="black", width=3)
    draw.text((30, 35), text, fill="black")
    return img


def test_clarity_sharp_vs_blurry():
    """Test: Sharp image has higher clarity score than blurred version."""
    sharp_img = create_test_text_image()
    score_sharp, is_unclear_sharp, _ = calculate_image_clarity(sharp_img)

    # Apply heavy blur
    blurry_img = sharp_img.filter(ImageFilter.GaussianBlur(radius=8))
    score_blurry, is_unclear_blurry, label_blurry = calculate_image_clarity(blurry_img)

    assert score_sharp > score_blurry
    assert is_unclear_blurry is True
    assert "Blurry" in label_blurry


def test_preprocess_for_ocr():
    """Test: Preprocessing enhancement returns valid image with appropriate dimensions."""
    img = Image.new("RGB", (200, 100), color="blue")
    enhanced = preprocess_for_ocr(img)
    assert isinstance(enhanced, Image.Image)
    assert enhanced.size[0] >= 200
    assert enhanced.size[1] >= 100


@patch("pytesseract.image_to_string")
def test_extract_ocr_text_mocked(mock_tesseract):
    """Test: OCR text extraction with mocked tesseract."""
    mock_tesseract.return_value = "Extracted Label 123"
    img = create_test_text_image()
    text = extract_ocr_text(img)
    assert text == "Extracted Label 123"


def test_analyze_image_clarity_and_ocr_auto_triggers_on_blurry():
    """Test: Blurry image automatically triggers OCR pipeline."""
    sharp_img = create_test_text_image()
    blurry_img = sharp_img.filter(ImageFilter.GaussianBlur(radius=10))

    with patch("services.ocr_service.extract_ocr_text") as mock_extract:
        mock_extract.return_value = "Recovered OCR text"
        result = analyze_image_clarity_and_ocr(blurry_img, auto_ocr_if_unclear=True)

        assert result["is_unclear"] is True
        assert result["ocr_applied"] is True
        assert result["ocr_text"] == "Recovered OCR text"


def test_analyze_image_clarity_and_ocr_sharp_image_no_force():
    """Test: Sharp image does not trigger OCR unless force_ocr is True."""
    sharp_img = create_test_text_image()
    # Mock calculate_image_clarity to ensure it reports sharp
    with patch("services.ocr_service.calculate_image_clarity", return_value=(500.0, False, "Sharp / High Clarity")):
        result = analyze_image_clarity_and_ocr(sharp_img, force_ocr=False, auto_ocr_if_unclear=True)
        assert result["is_unclear"] is False
        assert result["ocr_applied"] is False
