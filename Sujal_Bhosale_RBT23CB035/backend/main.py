import io
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.schemas import (
    GenerateImageRequest,
    GenerateImageResponse,
    HealthResponse,
    StylesResponse,
    StyleInfo
)
from backend.services.cf_generator import generate_image_cloudflare
from backend.services.style_presets import STYLE_PRESETS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dreamcanvas.api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DreamCanvas — AI Text-to-Image Generator powered by @cf/black-forest-labs/flux-1-schnell via Cloudflare Workers AI"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal server error occurred.", "details": str(exc)}
    )

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "provider": "Cloudflare Workers AI",
        "model": settings.CLOUDFLARE_MODEL,
        "docs_url": "/docs",
        "health_check": "/api/health"
    }

@app.get("/api/health", response_model=HealthResponse)
def get_health():
    token = settings.CLOUDFLARE_API_TOKEN.strip()
    account_id = settings.CLOUDFLARE_ACCOUNT_ID.strip()
    
    token_valid = bool(token and not token.startswith("your_") and token != "cf_token_placeholder")
    account_valid = bool(account_id and not account_id.startswith("your_") and account_id != "cf_account_id_placeholder")
    
    is_configured = token_valid and account_valid
    
    if not token_valid and not account_valid:
        msg = "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID need to be configured in backend/.env."
    elif not account_valid:
        msg = "CLOUDFLARE_ACCOUNT_ID is missing in backend/.env. Find it under Workers & Pages in Cloudflare Dashboard."
    elif not token_valid:
        msg = "CLOUDFLARE_API_TOKEN is missing or placeholder in backend/.env."
    else:
        msg = "Backend is operational and ready to generate images using Cloudflare Workers AI."

    return HealthResponse(
        status="healthy" if is_configured else "degraded",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        model=settings.CLOUDFLARE_MODEL,
        token_configured=is_configured,
        message=msg
    )

@app.get("/api/styles", response_model=StylesResponse)
def get_styles():
    styles_list = [
        StyleInfo(id=k, name=v["name"], description=v["description"])
        for k, v in STYLE_PRESETS.items()
    ]
    return StylesResponse(styles=styles_list)

@app.post("/api/generate")
def generate_image(
    request: Request,
    payload: GenerateImageRequest,
    format: Optional[str] = Query(None, description="Set to 'raw' or 'bytes' to receive direct image/png bytes")
):
    """
    Generate an image from prompt using Cloudflare Workers AI (@cf/black-forest-labs/flux-1-schnell).
    - If Accept header contains 'image/png' or query param format=raw/bytes: returns direct image/png bytes.
    - Otherwise returns JSON with image_base64 to preserve frontend compatibility.
    """
    logger.info(f"Generating image for prompt: '{payload.prompt[:60]}...' with style: '{payload.style}'")
    
    png_bytes, image_base64, enhanced_prompt, elapsed, final_w, final_h = generate_image_cloudflare(
        prompt=payload.prompt,
        style=payload.style,
        steps=payload.num_inference_steps or settings.DEFAULT_STEPS,
        seed=payload.seed
    )
    
    # Return direct image/png bytes when requested
    accept_header = request.headers.get("accept", "")
    if format in ("raw", "bytes") or ("image/png" in accept_header and "application/json" not in accept_header):
        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": 'inline; filename="dreamcanvas-generated.png"',
                "X-Prompt": payload.prompt[:80],
                "X-Style": payload.style,
                "X-Generation-Time": str(elapsed)
            }
        )
    
    # Return JSON for React frontend
    return GenerateImageResponse(
        success=True,
        image_base64=image_base64,
        mime_type="image/png",
        prompt=payload.prompt,
        enhanced_prompt=enhanced_prompt,
        style=payload.style,
        width=final_w,
        height=final_h,
        seed=payload.seed,
        generation_time_seconds=elapsed,
        model=settings.CLOUDFLARE_MODEL
    )

@app.post("/api/generate/raw")
def generate_image_raw(payload: GenerateImageRequest):
    """
    Dedicated endpoint that always returns direct image/png bytes.
    """
    png_bytes, _, _, elapsed, _, _ = generate_image_cloudflare(
        prompt=payload.prompt,
        style=payload.style,
        steps=payload.num_inference_steps or settings.DEFAULT_STEPS,
        seed=payload.seed
    )
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": 'inline; filename="dreamcanvas-generated.png"',
            "X-Generation-Time": str(elapsed)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=settings.PORT, reload=True)
