from __future__ import annotations

from io import BytesIO
from pathlib import Path

import streamlit as st
import torch

from generator import generate_image, load_pipeline


OUTPUTS_DIR = Path(__file__).parent / "outputs"

st.set_page_config(
    page_title="AI Text-to-Image Generator",
    page_icon="🎨",
    layout="centered",
)


@st.cache_resource(show_spinner=False)
def get_pipeline():
    return load_pipeline()


def main() -> None:
    st.title("🎨 AI Text-to-Image Generator")
    st.write(
        "Describe an image in natural language and generate it with "
        "Stable Diffusion 1.5."
    )

    cuda_available = torch.cuda.is_available()
    if cuda_available:
        st.success(f"CUDA GPU detected: {torch.cuda.get_device_name(0)}")
    else:
        st.warning(
            "CUDA is not available. CPU generation is supported but can take "
            "several minutes per image."
        )

    with st.form("generation_form"):
        prompt = st.text_area(
            "Prompt",
            placeholder="A cinematic mountain lake at sunrise, ultra detailed",
            height=110,
        )
        negative_prompt = st.text_area(
            "Negative prompt (optional)",
            value="blurry, distorted, low quality, watermark, text",
            height=80,
        )

        col1, col2 = st.columns(2)
        with col1:
            style = st.selectbox(
                "Image style",
                ["Realistic", "Anime", "Digital Art", "3D Render", "Painting"],
            )
        with col2:
            steps = st.slider(
                "Inference steps",
                min_value=10,
                max_value=50,
                value=20,
                help="More steps can improve detail but increase generation time.",
            )

        seed = st.number_input(
            "Seed (optional, -1 for random)",
            min_value=-1,
            max_value=2**31 - 1,
            value=-1,
            step=1,
            help="Use a fixed seed to reproduce an image.",
        )
        submitted = st.form_submit_button(
            "🚀 Generate Image",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not prompt.strip():
            st.error("Please enter a text prompt before generating an image.")
            return

        try:
            with st.spinner("Loading the model and generating your image..."):
                pipeline = get_pipeline()
                image = generate_image(
                    pipeline=pipeline,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    style=style,
                    steps=steps,
                    seed=None if seed == -1 else int(seed),
                )

            OUTPUTS_DIR.mkdir(exist_ok=True)
            output_path = OUTPUTS_DIR / "generated_image.png"
            image.save(output_path, format="PNG")
            st.session_state["generated_image"] = image
            st.session_state["generated_path"] = output_path
            st.success("Image generated successfully.")
        except Exception as exc:
            st.error(str(exc))

    image = st.session_state.get("generated_image")
    if image is not None:
        st.subheader("Generated image")
        st.image(image, caption="Stable Diffusion 1.5 output", use_container_width=True)
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        st.download_button(
            "⬇️ Download PNG",
            data=image_bytes.getvalue(),
            file_name="generated_image.png",
            mime="image/png",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
