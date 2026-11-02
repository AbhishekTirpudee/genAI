import base64
import io
import logging
import time
from typing import Optional, Tuple
from fastapi import HTTPException, status
from PIL import Image
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError

from backend.config import settings
from backend.services.style_presets import enhance_prompt_with_style

logger = logging.getLogger("dreamcanvas.generator")

def get_inference_client(token: Optional[str] = None) -> InferenceClient:
    """Instantiate a Hugging Face InferenceClient with configured credentials."""
    active_token = (token or settings.HF_TOKEN or "").strip()
    if not active_token or active_token.lower().startswith("hf_placeholder") or active_token.lower() == "your_huggingface_api_token_here":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Hugging Face API token is not configured. Please set HF_TOKEN in your "
                "backend/.env file. You can create a free token at https://huggingface.co/settings/tokens"
            )
        )
    return InferenceClient(
        token=active_token,
        timeout=120.0
    )

def generate_image_flux(
    prompt: str,
    style: str = "photorealistic",
    width: int = 1024,
    height: int = 1024,
    num_inference_steps: int = 4,
    seed: Optional[int] = None,
    custom_token: Optional[str] = None
) -> Tuple[str, str, float, int, int]:
    """
    Generates an image using black-forest-labs/FLUX.1-schnell via Hugging Face Inference.
    Converts output into PNG format using Pillow, then returns base64 string.
    
    Returns:
        (image_base64, enhanced_prompt, generation_time, final_width, final_height)
    """
    enhanced_prompt = enhance_prompt_with_style(prompt, style)
    client = get_inference_client(custom_token)
    
    logger.info(f"Generating image with model {settings.HF_MODEL}...")
    logger.info(f"Original Prompt: {prompt}")
    logger.info(f"Enhanced Prompt: {enhanced_prompt}")
    
    start_time = time.time()
    
    try:
        # Call Hugging Face text_to_image API
        # Note: black-forest-labs/FLUX.1-schnell requires dimensions divisible by 16
        # Align width and height to 16 multiples
        aligned_width = (max(256, min(1440, width)) // 16) * 16
        aligned_height = (max(256, min(1440, height)) // 16) * 16
        
        call_kwargs = {
            "prompt": enhanced_prompt,
            "model": settings.HF_MODEL,
            "width": aligned_width,
            "height": aligned_height,
            "num_inference_steps": max(1, min(12, num_inference_steps or 4)),
        }
        if seed is not None:
            call_kwargs["seed"] = seed
            
        raw_result = client.text_to_image(**call_kwargs)
        
        # Convert generated output into PNG using Pillow
        if isinstance(raw_result, Image.Image):
            pil_image = raw_result
        elif isinstance(raw_result, (bytes, bytearray)):
            pil_image = Image.open(io.BytesIO(raw_result))
        else:
            raise ValueError(f"Unexpected image output type from InferenceClient: {type(raw_result)}")
            
        # Ensure image is in RGB or RGBA mode for standard PNG export
        if pil_image.mode not in ("RGB", "RGBA"):
            pil_image = pil_image.convert("RGB")
            
        png_buffer = io.BytesIO()
        pil_image.save(png_buffer, format="PNG", optimize=True)
        png_bytes = png_buffer.getvalue()
        image_base64 = base64.b64encode(png_bytes).decode("utf-8")
        
        elapsed_time = round(time.time() - start_time, 2)
        actual_width, actual_height = pil_image.size
        
        logger.info(f"Generation completed successfully in {elapsed_time}s ({actual_width}x{actual_height} PNG).")
        return image_base64, enhanced_prompt, elapsed_time, actual_width, actual_height

    except HfHubHTTPError as hf_err:
        logger.error(f"Hugging Face API HTTP error: {hf_err}")
        status_code = getattr(hf_err.response, "status_code", 502) if hasattr(hf_err, "response") else 502
        detail_msg = str(hf_err)
        
        if status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Hugging Face API token. Please check your HF_TOKEN in backend/.env"
            )
        elif status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hugging Face rate limit reached. Please wait a moment before trying again."
            )
        elif status_code == 503:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The FLUX.1-schnell model is currently loading on Hugging Face providers. Please retry in 30 seconds."
            )
        else:
            raise HTTPException(
                status_code=status_code if 400 <= status_code < 600 else 500,
                detail=f"Hugging Face generation error: {detail_msg}"
            )
            
    except RepositoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{settings.HF_MODEL}' not found or inaccessible with current token permissions."
        )
        
    except HTTPException:
        raise
        
    except Exception as exc:
        logger.exception("Unexpected error while generating image")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(exc)}"
        )

