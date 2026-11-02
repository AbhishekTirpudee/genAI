from __future__ import annotations

from typing import Optional

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image


MODEL_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"
IMAGE_SIZE = 512

STYLE_PROMPTS = {
    "Realistic": "photorealistic, natural lighting, highly detailed",
    "Anime": "anime style, clean line art, vibrant colors, detailed illustration",
    "Digital Art": "digital art, polished concept art, expressive details",
    "3D Render": "3D render, physically based materials, studio lighting",
    "Painting": "traditional painting, visible brushwork, rich artistic composition",
}


def load_pipeline() -> StableDiffusionPipeline:
    """Load Stable Diffusion once and configure it for the available hardware."""
    use_cuda = torch.cuda.is_available()
    dtype = torch.float16 if use_cuda else torch.float32

    try:
        pipeline = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            use_safetensors=True,
        )
        pipeline.enable_attention_slicing()

        if use_cuda:
            # Accelerate places layers on the GPU only when needed.
            pipeline.enable_model_cpu_offload()
        else:
            pipeline.to("cpu")
        return pipeline
    except Exception as exc:
        raise RuntimeError(
            "Model loading failed. Check your internet connection, disk space, "
            "and Hugging Face model access. Original error: "
            f"{exc}"
        ) from exc


def generate_image(
    pipeline: StableDiffusionPipeline,
    prompt: str,
    negative_prompt: str,
    style: str,
    steps: int = 20,
    seed: Optional[int] = None,
) -> Image.Image:
    """Generate one 512x512 image from a prompt."""
    if not prompt.strip():
        raise ValueError("The prompt cannot be empty.")
    if not 10 <= steps <= 50:
        raise ValueError("Inference steps must be between 10 and 50.")
    if style not in STYLE_PROMPTS:
        raise ValueError(f"Unsupported style: {style}")

    styled_prompt = f"{prompt.strip()}, {STYLE_PROMPTS[style]}"
    generator = None
    if seed is not None:
        generator = torch.Generator(
            device="cuda" if torch.cuda.is_available() else "cpu"
        ).manual_seed(seed)

    try:
        result = pipeline(
            prompt=styled_prompt,
            negative_prompt=negative_prompt.strip() or None,
            height=IMAGE_SIZE,
            width=IMAGE_SIZE,
            num_inference_steps=steps,
            guidance_scale=7.5,
            generator=generator,
        )
        return result.images[0]
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise RuntimeError(
                "GPU memory was insufficient. Try fewer inference steps, close "
                "other GPU applications, or run with CPU fallback."
            ) from exc
        raise RuntimeError(f"Image generation failed: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Image generation failed: {exc}") from exc
