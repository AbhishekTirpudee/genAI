import base64
import io
import logging
import time
from typing import Optional, Tuple
import httpx
from fastapi import HTTPException, status
from PIL import Image

from backend.config import settings
from backend.services.style_presets import enhance_prompt_with_style

logger = logging.getLogger("dreamcanvas.cf_generator")

def validate_credentials():
    """Verify that Cloudflare credentials are set in configuration."""
    token = (settings.CLOUDFLARE_API_TOKEN or "").strip()
    account_id = (settings.CLOUDFLARE_ACCOUNT_ID or "").strip()
    
    if not token or token.startswith("your_") or token == "cf_token_placeholder":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Cloudflare API Token is not configured. Please set CLOUDFLARE_API_TOKEN "
                "in your backend/.env file."
            )
        )
        
    if not account_id or account_id.startswith("your_") or account_id == "cf_account_id_placeholder":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Cloudflare Account ID is not configured. Please set CLOUDFLARE_ACCOUNT_ID "
                "in your backend/.env file. Find your Account ID in the Cloudflare Dashboard under Workers & Pages."
            )
        )

def generate_image_cloudflare(
    prompt: str,
    style: str = "photorealistic",
    steps: int = 4,
    seed: Optional[int] = None
) -> Tuple[bytes, str, str, float, int, int]:
    """
    Generate an image using Cloudflare Workers AI:
    POST https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell
    
    1. Send prompt & steps using httpx.
    2. Decode result.image from base64.
    3. Convert the output to PNG using Pillow.
    4. Return (png_bytes, base64_png, enhanced_prompt, elapsed_seconds, width, height).
    """
    validate_credentials()
    
    enhanced_prompt = enhance_prompt_with_style(prompt, style)
    steps_count = max(1, min(8, steps or settings.DEFAULT_STEPS))
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/run/{settings.CLOUDFLARE_MODEL}"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "prompt": enhanced_prompt,
        "steps": steps_count
    }
    if seed is not None:
        body["seed"] = seed

    logger.info(f"Calling Cloudflare Workers AI model: {settings.CLOUDFLARE_MODEL}")
    logger.info(f"Prompt: {enhanced_prompt[:80]}... | Steps: {steps_count}")
    
    start_time = time.time()
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=body)
            
        elapsed_time = round(time.time() - start_time, 2)
        
        # Check HTTP response status
        if response.status_code != 200:
            logger.error(f"Cloudflare returned HTTP {response.status_code}: {response.text}")
            error_detail = response.text
            try:
                err_json = response.json()
                if "errors" in err_json and err_json["errors"]:
                    error_detail = "; ".join([e.get("message", str(e)) for e in err_json["errors"]])
            except Exception:
                pass
                
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Cloudflare authentication failed: {error_detail}. Please verify your CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID."
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cloudflare resource or account not found: {error_detail}. Check CLOUDFLARE_ACCOUNT_ID."
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Cloudflare rate limit reached. Please wait a moment before trying again."
                )
            else:
                raise HTTPException(
                    status_code=response.status_code if 400 <= response.status_code < 600 else 500,
                    detail=f"Cloudflare Workers AI generation failed: {error_detail}"
                )

        # Parse output - Decode result.image from base64
        content_type = response.headers.get("content-type", "")
        raw_bytes = None
        
        if "application/json" in content_type:
            data = response.json()
            if not data.get("success", True) and "errors" in data and data["errors"]:
                error_msg = "; ".join([e.get("message", str(e)) for e in data["errors"]])
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Cloudflare Workers AI returned an error: {error_msg}"
                )
                
            result = data.get("result", {})
            if isinstance(result, dict) and "image" in result:
                raw_bytes = base64.b64decode(result["image"])
            elif "image" in data:
                raw_bytes = base64.b64decode(data["image"])
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Cloudflare Workers AI response missing 'result.image' base64 field."
                )
        else:
            # Direct binary image response
            raw_bytes = response.content

        if not raw_bytes:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Received empty image payload from Cloudflare Workers AI."
            )

        # Convert the output to PNG using Pillow
        try:
            pil_image = Image.open(io.BytesIO(raw_bytes))
        except Exception as img_err:
            logger.error(f"Failed to open image bytes with Pillow: {img_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse generated image with Pillow: {str(img_err)}"
            )

        if pil_image.mode not in ("RGB", "RGBA"):
            pil_image = pil_image.convert("RGB")

        png_buffer = io.BytesIO()
        pil_image.save(png_buffer, format="PNG", optimize=True)
        png_bytes = png_buffer.getvalue()
        image_base64 = base64.b64encode(png_bytes).decode("utf-8")
        
        width, height = pil_image.size
        logger.info(f"Cloudflare generation completed: {width}x{height} PNG in {elapsed_time}s")
        
        return png_bytes, image_base64, enhanced_prompt, elapsed_time, width, height

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Cloudflare Workers AI request timed out. Please try again."
        )
    except httpx.RequestError as req_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Cloudflare API: {str(req_err)}"
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during Cloudflare Workers AI generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(exc)}"
        )

