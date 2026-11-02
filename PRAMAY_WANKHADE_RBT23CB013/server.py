import streamlit as st
import requests
from PIL import Image
import io

# Configure Streamlit page layout and dark-mode aesthetic
st.set_page_config(page_title="AI Image Generator", layout="centered")

# Custom CSS to inject a clean dark-theme modern AI tool aesthetic
st.markdown("""
<style>
    .main {background-color: #121212; color: #FFFFFF;}
    .stButton>button {width: 100%; background-color: #4A154B; color: white; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

st.title("🌌 AI Text-to-Image Generator")
st.write("Connect directly to your Google Colab GPU-powered backend to design custom images.")

# Configurable connection endpoint
backend_url = st.text_input(
    "Backend Endpoint (Ngrok URL)",
    value="https://your-ngrok-subdomain.ngrok-free.app",
    help="Paste the Ngrok public URL generated in Colab here."
)

# Left inputs and right preview column
col1, col2 = st.columns([1, 1.2])

with col1:
    prompt = st.text_area("Prompt", value="A futuristic cyberpunk skyline")
    neg_prompt = st.text_area("Negative Prompt", value="blurry, low quality")
    style = st.selectbox(
        "Style", 
        ["Realistic", "Anime", "Digital Art", "3D Render", "Oil Painting"],
        index=2
    )
    steps = st.slider("Inference Steps", 10, 30, 20)
    guidance_scale = st.slider("Guidance Scale", 1.0, 15.0, 7.5, 0.5)
    
    generate_btn = st.button("Generate Image")

with col2:
    st.subheader("Output Preview")
    if generate_btn:
        if not backend_url.strip():
            st.error("Please enter a valid Ngrok backend URL.")
        else:
            # Construct final URL endpoint cleanly
            clean_url = backend_url.strip().rstrip("/") + "/generate"
            headers = {"Content-Type": "application/json"}
            payload = {
                "prompt": prompt,
                "negative_prompt": neg_prompt,
                "style": style,
                "steps": steps,
                "guidance_scale": guidance_scale
            }
            
            with st.spinner("Executing generation pipeline on Colab GPU..."):
                try:
                    response = requests.post(clean_url, json=payload, headers=headers, timeout=120)
                    if response.status_code == 200:
                        # Read binary PNG data
                        image_bytes = response.content
                        image = Image.open(io.BytesIO(image_bytes))
                        st.image(image, use_container_width=True)
                        
                        # Download button integration
                        st.download_button(
                            label="📥 Download Image",
                            data=image_bytes,
                            file_name="generated_image.png",
                            mime="image/png"
                        )
                        st.success("Image generated successfully!")
                    else:
                        st.error(f"Backend returned error ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
    else:
        st.info("Awaiting prompt parameters to begin rendering.")
