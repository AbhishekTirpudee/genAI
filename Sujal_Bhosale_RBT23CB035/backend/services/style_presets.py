from typing import Dict, Any

STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "none": {
        "id": "none",
        "name": "Natural / No Style",
        "description": "Pure prompt interpretation without specific stylistic bias",
        "prefix": "",
        "suffix": ", high resolution, detailed",
    },
    "photorealistic": {
        "id": "photorealistic",
        "name": "Photorealistic",
        "description": "Ultra-realistic 8k photography, natural lighting, sharp focus",
        "prefix": "Award-winning professional photograph of ",
        "suffix": ", 35mm lens, f/1.8 aperture, natural lighting, ultra-sharp focus, photorealistic 8k, hyperdetailed textures",
    },
    "anime": {
        "id": "anime",
        "name": "Anime & Manga",
        "description": "Modern Japanese anime style with vibrant colors and expressive line art",
        "prefix": "Anime aesthetic masterpiece, Makoto Shinkai and Studio Ghibli inspired, ",
        "suffix": ", vibrant colors, expressive line art, cinematic lighting, 4k anime visual novel illustration",
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "Cyberpunk Neon",
        "description": "Futuristic dystopian sci-fi with neon glow, rain reflections, and high tech",
        "prefix": "Futuristic cyberpunk sci-fi scene of ",
        "suffix": ", neon soaked alleyway, holographic displays, volumetric fog, chromatic aberration, ray tracing reflections, 8k render",
    },
    "fantasy": {
        "id": "fantasy",
        "name": "Epic Fantasy",
        "description": "Magical mystical world with ethereal atmosphere and grand scale",
        "prefix": "High fantasy digital concept art of ",
        "suffix": ", magical ethereal particles, atmospheric mist, grand worldbuilding, artstation trending, dramatic golden hour lighting",
    },
    "oil_painting": {
        "id": "oil_painting",
        "name": "Classic Oil Painting",
        "description": "Rich oil canvas textures, visible palette knife strokes, classical masterwork",
        "prefix": "Classical oil on canvas painting of ",
        "suffix": ", heavy impasto brushwork, rich textural depth, chiaroscuro lighting, Rembrandt and John Singer Sargent style",
    },
    "cinematic": {
        "id": "cinematic",
        "name": "Cinematic Movie",
        "description": "Dramatic Hollywood film still with anamorphic lens flare and cinematic grade",
        "prefix": "Cinematic movie still from a blockbusting film, ",
        "suffix": ", 70mm IMAX film, anamorphic bokeh, color graded, dramatic atmospheric lighting, film grain",
    },
    "digital_art": {
        "id": "digital_art",
        "name": "Modern Digital Art",
        "description": "Sharp, clean vector and digital painting with vivid colors",
        "prefix": "Masterpiece digital artwork of ",
        "suffix": ", trending on ArtStation, crisp details, smooth gradients, dynamic composition, ambient occlusion",
    },
    "3d_render": {
        "id": "3d_render",
        "name": "3D Render & Pixar",
        "description": "Octane rendered 3D animated character or environment, playful and polished",
        "prefix": "Pixar and Disney 3D animation style render of ",
        "suffix": ", Octane Render, subsurface scattering, soft studio lighting, cute stylized proportions, 4k resolution",
    },
    "watercolor": {
        "id": "watercolor",
        "name": "Delicate Watercolor",
        "description": "Fluid watercolor pigment bleeds on textured cold-press cotton paper",
        "prefix": "Original watercolor painting of ",
        "suffix": ", soft wet-on-wet paint washes, watercolor splashes, gentle paper texture, delicate pastel palette",
    },
    "studio_portrait": {
        "id": "studio_portrait",
        "name": "Studio Portrait",
        "description": "Studio lighting setup with softbox, Rembrandt lighting, and sharp depth of field",
        "prefix": "High-end studio beauty portrait of ",
        "suffix": ", Profoto softbox lighting, shallow depth of field, 85mm lens, tack-sharp eyes, commercial editorial quality",
    },
    "pixel_art": {
        "id": "pixel_art",
        "name": "16-Bit Pixel Art",
        "description": "Nostalgic retro video game pixel sprite art with limited palette",
        "prefix": "Detailed 16-bit pixel art of ",
        "suffix": ", retro SNES video game aesthetic, clean pixel grid, vibrant dithered palette, pixel perfection",
    }
}

def enhance_prompt_with_style(prompt: str, style_id: str) -> str:
    """Enhance the user's prompt by applying the selected artistic style preset."""
    style_key = style_id.lower().strip() if style_id else "none"
    style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["none"])
    
    prefix = style.get("prefix", "")
    suffix = style.get("suffix", "")
    
    clean_prompt = prompt.strip()
    return f"{prefix}{clean_prompt}{suffix}".strip()

