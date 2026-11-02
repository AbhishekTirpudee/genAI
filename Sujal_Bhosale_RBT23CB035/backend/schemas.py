from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class GenerateImageRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The text prompt describing the image to generate.",
        examples=["A majestic snow leopard resting on Himalayan peaks at sunrise"]
    )
    style: str = Field(
        default="photorealistic",
        description="Artistic style preset identifier."
    )
    width: Optional[int] = Field(
        default=1024,
        ge=256,
        le=1440,
        description="Width of generated image in pixels (multiples of 16 recommended)."
    )
    height: Optional[int] = Field(
        default=1024,
        ge=256,
        le=1440,
        description="Height of generated image in pixels (multiples of 16 recommended)."
    )
    num_inference_steps: Optional[int] = Field(
        default=4,
        ge=1,
        le=12,
        description="Number of inference steps for FLUX.1-schnell (default is 4)."
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional seed for deterministic generation."
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Prompt cannot be empty or purely whitespace.")
        return clean

class GenerateImageResponse(BaseModel):
    success: bool = True
    image_base64: str = Field(description="Base64-encoded PNG image data.")
    mime_type: str = "image/png"
    prompt: str
    enhanced_prompt: str
    style: str
    width: int
    height: int
    seed: Optional[int] = None
    generation_time_seconds: float
    model: str

class StyleInfo(BaseModel):
    id: str
    name: str
    description: str

class StylesResponse(BaseModel):
    styles: List[StyleInfo]

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    model: str
    token_configured: bool
    message: str

