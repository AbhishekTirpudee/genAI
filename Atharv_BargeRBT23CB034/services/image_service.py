"""
Image Service for VisionQA.
Handles image validation, EXIF correction, transparency handling,
resizing, and in-memory preprocessing.
"""

import io
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageOps, UnidentifiedImageError

# Configuration constants
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}
MAX_DIMENSION = 1600  # Maximum width or height to preserve memory and speed up inference


class ImageValidationError(Exception):
    """Exception raised for image validation errors."""
    pass


def validate_file_size(file_bytes: bytes, max_size: int = MAX_FILE_SIZE_BYTES) -> None:
    """
    Validate that the uploaded file size does not exceed the allowed maximum.
    
    Args:
        file_bytes: Raw bytes of the uploaded file.
        max_size: Maximum allowed size in bytes (default 10 MB).
        
    Raises:
        ImageValidationError: If file size exceeds the limit or is empty.
    """
    if not file_bytes:
        raise ImageValidationError("The uploaded file is empty (0 bytes).")
    
    size = len(file_bytes)
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        raise ImageValidationError(
            f"File size exceeds the {max_mb:.1f} MB limit (uploaded file is {actual_mb:.2f} MB)."
        )


def validate_image_format(image: Image.Image) -> str:
    """
    Validate that the Pillow-detected format is among allowed formats.
    
    Args:
        image: PIL Image instance.
        
    Returns:
        The normalized format string.
        
    Raises:
        ImageValidationError: If the format is unsupported or unknown.
    """
    fmt = (image.format or "").upper()
    if fmt == "JPG":
        fmt = "JPEG"
        
    if fmt not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format: '{fmt or 'Unknown'}'. "
            f"Allowed formats are JPG, JPEG, PNG, and WEBP."
        )
    return fmt


def correct_exif_orientation(image: Image.Image) -> Image.Image:
    """
    Correct image orientation based on EXIF metadata (e.g. mobile photos).
    
    Args:
        image: PIL Image.
        
    Returns:
        Transposed PIL Image with correct upright orientation.
    """
    try:
        # ImageOps.exif_transpose handles EXIF orientation tag 0x0112 safely
        transposed = ImageOps.exif_transpose(image)
        return transposed if transposed is not None else image
    except Exception:
        # Fall back to original image if EXIF parsing fails
        return image


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """
    Convert image to RGB mode, properly handling transparency in PNG and WEBP.
    Transparent pixels are composited onto a clean white background.
    
    Args:
        image: PIL Image in any mode (RGBA, LA, P, L, RGB, etc.).
        
    Returns:
        PIL Image in standard 'RGB' mode.
    """
    if image.mode == "RGB":
        return image

    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        # Convert to RGBA first to ensure consistent alpha channel
        rgba_image = image.convert("RGBA")
        # Create a white background
        background = Image.new("RGBA", rgba_image.size, (255, 255, 255, 255))
        # Composite image over white background
        alpha_composite = Image.alpha_composite(background, rgba_image)
        return alpha_composite.convert("RGB")

    return image.convert("RGB")


def resize_image_if_needed(image: Image.Image, max_dim: int = MAX_DIMENSION) -> Tuple[Image.Image, bool]:
    """
    Resize image proportionally if width or height exceeds max_dim.
    Preserves exact aspect ratio using high-quality LANCZOS filtering.
    
    Args:
        image: PIL Image.
        max_dim: Maximum width or height allowed.
        
    Returns:
        Tuple of (resized_image, was_resized_boolean).
    """
    width, height = image.size
    if width <= max_dim and height <= max_dim:
        return image, False

    if width > height:
        new_width = max_dim
        new_height = int(round((height * max_dim) / width))
    else:
        new_height = max_dim
        new_width = int(round((width * max_dim) / height))

    # Ensure dimensions are at least 1 pixel
    new_width = max(1, new_width)
    new_height = max(1, new_height)

    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized, True


def process_uploaded_image(file_data: Any) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Complete end-to-end processing pipeline for uploaded images:
    1. Read and validate raw bytes and size.
    2. Open image with Pillow and verify integrity (reject corrupt files).
    3. Validate format (JPG, JPEG, PNG, WEBP).
    4. Correct EXIF orientation.
    5. Convert to RGB handling transparency.
    6. Proportional downsampling if dimensions exceed threshold.
    7. Return processed in-memory PIL Image and metadata dict.
    
    Args:
        file_data: Raw bytes, BytesIO, or Streamlit UploadedFile object.
        
    Returns:
        Tuple of (processed_pil_image, metadata_dictionary).
        
    Raises:
        ImageValidationError: If any validation or processing step fails.
    """
    # Extract bytes
    if hasattr(file_data, "getvalue"):
        raw_bytes = file_data.getvalue()
    elif hasattr(file_data, "read"):
        raw_bytes = file_data.read()
    elif isinstance(file_data, (bytes, bytearray)):
        raw_bytes = bytes(file_data)
    else:
        raise ImageValidationError("Invalid file data type provided.")

    # Validate size
    validate_file_size(raw_bytes)

    # Open and verify image integrity
    try:
        buffer = io.BytesIO(raw_bytes)
        img = Image.open(buffer)
        
        # Verify the file is not corrupted
        img.verify()
        
        # img.verify() closes or invalidates the buffer for some operations,
        # so reopen a clean copy for pixel operations
        buffer.seek(0)
        img = Image.open(buffer)
        # Force loading image data to detect truncated / corrupt chunks
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError) as e:
        raise ImageValidationError(f"Invalid or corrupted image file: {str(e)}")
    except Exception as e:
        raise ImageValidationError(f"Could not open image: {str(e)}")

    # Validate format
    detected_format = validate_image_format(img)
    original_size = img.size

    # Correct EXIF orientation
    img = correct_exif_orientation(img)

    # Convert to RGB mode (with clean alpha handling)
    img = convert_to_rgb(img)

    # Resize if extremely large
    img, was_resized = resize_image_if_needed(img, MAX_DIMENSION)

    metadata = {
        "format": detected_format,
        "original_width": original_size[0],
        "original_height": original_size[1],
        "current_width": img.size[0],
        "current_height": img.size[1],
        "size_bytes": len(raw_bytes),
        "size_mb": round(len(raw_bytes) / (1024 * 1024), 2),
        "was_resized": was_resized,
        "mode": img.mode,
    }

    return img, metadata


def image_to_bytes(image: Image.Image, format: str = "JPEG", quality: int = 90) -> bytes:
    """
    Convert a PIL Image to raw bytes in memory.
    
    Args:
        image: PIL Image.
        format: Target format (e.g. 'JPEG', 'PNG', 'WEBP').
        quality: JPEG compression quality (1-100).
        
    Returns:
        Raw bytes of the image.
    """
    buf = io.BytesIO()
    save_format = format.upper()
    if save_format in ("JPG", "JPEG"):
        image.save(buf, format="JPEG", quality=quality, optimize=True)
    elif save_format == "PNG":
        image.save(buf, format="PNG", optimize=True)
    elif save_format == "WEBP":
        image.save(buf, format="WEBP", quality=quality)
    else:
        image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
