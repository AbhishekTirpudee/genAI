"""
OCR and Image Clarity Service for VisionQA.
Detects blurry or low-clarity images using Laplacian edge variance
and automatically extracts text using Tesseract OCR with image enhancement filters.
"""

import os
import shutil
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import numpy as np

# Configure Tesseract binary path
TESSERACT_CANDIDATE_PATHS = [
    os.getenv("TESSERACT_PATH", ""),
    shutil.which("tesseract") or "",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]

_TESSERACT_CONFIGURED = False


def configure_tesseract() -> bool:
    """
    Locate and configure the Tesseract executable for pytesseract.
    Returns True if Tesseract is available, False otherwise.
    """
    global _TESSERACT_CONFIGURED
    try:
        import pytesseract
        for candidate in TESSERACT_CANDIDATE_PATHS:
            if candidate and os.path.isfile(candidate):
                pytesseract.pytesseract.tesseract_cmd = candidate
                _TESSERACT_CONFIGURED = True
                return True
        # If in PATH
        if shutil.which("tesseract"):
            _TESSERACT_CONFIGURED = True
            return True
    except Exception:
        pass
    _TESSERACT_CONFIGURED = False
    return False


# Attempt initial configuration
configure_tesseract()


def calculate_image_clarity(image: Image.Image) -> Tuple[float, bool, str]:
    """
    Compute image sharpness/clarity score using Laplacian variance.
    Lower scores indicate blurriness, compression artifacts, or poor focus.
    
    Args:
        image: PIL Image.
        
    Returns:
        Tuple of (score: float, is_unclear: bool, label: str)
    """
    # Convert image to grayscale numpy array
    rgb_img = image.convert("RGB")
    np_img = np.array(rgb_img)

    try:
        import cv2
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        # Laplacian variance measures edge frequency content
        score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    except Exception:
        # Fallback using PIL edge filtering
        gray_pil = rgb_img.convert("L")
        edges = gray_pil.filter(ImageFilter.FIND_EDGES)
        edge_data = np.array(edges, dtype=np.float32)
        score = float(np.var(edge_data))

    # Threshold classification:
    # < 200: Low clarity / blurry
    # 200 - 450: Moderate clarity
    # > 450: Sharp / high clarity
    if score < 200.0:
        is_unclear = True
        label = "Blurry / Low Clarity"
    elif score <= 450.0:
        is_unclear = False
        label = "Moderate Clarity"
    else:
        is_unclear = False
        label = "Sharp / High Clarity"

    return round(score, 1), is_unclear, label


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Apply image enhancement filters (denoising, contrast enhancement, sharpening)
    to maximize OCR text recovery on unclear, degraded, or blurry photographs.
    
    Args:
        image: PIL Image.
        
    Returns:
        Enhanced PIL Image optimized for OCR text extraction.
    """
    # 1. Convert to grayscale
    gray = image.convert("L")

    # 2. Upscale small images to improve character edge resolution
    w, h = gray.size
    if max(w, h) < 1200:
        scale = min(2.5, 1200.0 / max(w, h))
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        gray = gray.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 3. Enhance local contrast
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.8)

    # 4. Sharpen character boundaries
    sharpened = enhanced.filter(ImageFilter.SHARPEN)

    # 5. Adaptive binarization via OpenCV if available
    try:
        import cv2
        np_gray = np.array(sharpened)
        # Apply Otsu's thresholding after slight Gaussian blur
        blurred = cv2.GaussianBlur(np_gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)
    except Exception:
        # Fallback to PIL autothreshold
        return sharpened


def extract_ocr_text(image: Image.Image, enhance: bool = True) -> str:
    """
    Extract readable text from an image using Tesseract OCR.
    
    Args:
        image: PIL Image.
        enhance: Whether to apply image preprocessing filters first.
        
    Returns:
        Cleaned extracted text string, or empty string if no text found.
    """
    if not _TESSERACT_CONFIGURED:
        if not configure_tesseract():
            return ""

    try:
        import pytesseract

        candidates_text = []

        # Pass 1: Enhanced image with psm 6 (uniform block)
        if enhance:
            enhanced_img = preprocess_for_ocr(image)
            t1 = pytesseract.image_to_string(enhanced_img, config="--psm 6").strip()
            if t1:
                candidates_text.append(t1)

            t2 = pytesseract.image_to_string(enhanced_img, config="--psm 3").strip()
            if t2:
                candidates_text.append(t2)

        # Pass 2: Raw image with psm 3 (standard layout)
        t3 = pytesseract.image_to_string(image, config="--psm 3").strip()
        if t3:
            candidates_text.append(t3)

        if not candidates_text:
            return ""

        # Return the candidate with the highest information content (longest cleaned text)
        best_text = max(candidates_text, key=lambda s: len(s.strip()))
        return best_text.strip()
    except Exception:
        return ""


def analyze_image_clarity_and_ocr(
    image: Image.Image,
    force_ocr: bool = False,
    auto_ocr_if_unclear: bool = True,
) -> Dict[str, Any]:
    """
    Comprehensive pipeline:
    1. Evaluates image clarity & blur score.
    2. If the image is unclear (or force_ocr is True), runs OCR enhancement.
    3. Returns metadata and extracted text.
    
    Args:
        image: PIL Image.
        force_ocr: If True, always runs OCR regardless of clarity score.
        auto_ocr_if_unclear: If True, triggers OCR whenever is_unclear is True.
        
    Returns:
        Dictionary with clarity score, status label, and OCR results.
    """
    score, is_unclear, label = calculate_image_clarity(image)

    should_run_ocr = force_ocr or (is_unclear and auto_ocr_if_unclear)
    ocr_text = ""
    ocr_applied = False

    if should_run_ocr:
        ocr_text = extract_ocr_text(image, enhance=True)
        ocr_applied = True

    return {
        "clarity_score": score,
        "is_unclear": is_unclear,
        "clarity_label": label,
        "ocr_applied": ocr_applied,
        "ocr_text": ocr_text,
    }
