"""
VisionQA — Image-Based Question Answering System.
Built with Streamlit, Pillow, Google Gen AI SDK, and SQLite.
"""

import os
import io
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from services.image_service import (
    process_uploaded_image,
    ImageValidationError,
)
from services.vision_service import (
    answer_image_question,
    get_api_key,
    get_configured_model,
    VisionServiceError,
    DEFAULT_MODEL,
)
from services.ollama_service import (
    answer_image_question_ollama,
    check_ollama_connection,
    KNOWN_VISION_MODELS,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    OllamaServiceError,
)
from services.ocr_service import analyze_image_clarity_and_ocr
from utils.helpers import (
    init_session_state,
    reset_conversation,
    validate_question,
    mask_api_key,
    generate_conversation_id,
)
from utils.db import (
    init_db,
    save_conversation_meta,
    save_message_to_db,
    load_conversation_messages,
    get_saved_conversations,
    clear_history_db,
)

# Load environment configuration
load_dotenv()

# Initialize SQLite database
init_db()

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VisionQA — Image-Based Question Answering",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished, clean, professional aesthetics
st.markdown(
    """
    <style>
    /* Main container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Header typography */
    .vision-header {
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .vision-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    .vision-subtitle {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    
    /* Image metadata badge bar */
    .meta-badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
        margin-bottom: 0.8rem;
    }
    .meta-badge {
        background-color: #f1f5f9;
        color: #334155;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }

    /* Sidebar info box */
    .sidebar-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.85rem;
        margin-bottom: 1rem;
        font-size: 0.875rem;
    }
    
    /* Chat message spacing */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state variables
init_session_state(st.session_state)


# -----------------------------------------------------------------------------
# Sidebar Configuration and Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("👁️ VisionQA")
    st.markdown(
        "**Multimodal Visual Q&A**  \n"
        "Ask detailed natural language questions about your photographs."
    )
    st.divider()

    # Primary Chat Actions
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ New Chat", use_container_width=True, help="Start a new session and reset image"):
            reset_conversation(st.session_state, clear_image=True)
            st.rerun()

    with col_btn2:
        if st.button("🧹 Clear Chat", use_container_width=True, help="Clear messages while keeping the current image"):
            reset_conversation(st.session_state, clear_image=False)
            st.rerun()

    # AI Engine Provider Selection
    st.markdown("### 🤖 AI Engine Provider")
    env_provider = os.getenv("AI_PROVIDER", "gemini").lower()
    default_provider_idx = 1 if "ollama" in env_provider else 0
    selected_provider = st.radio(
        "AI Engine Provider",
        options=["Google Gemini (Cloud)", "Ollama (Local)"],
        index=default_provider_idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["selected_provider"] = selected_provider

    # Provider & Model Settings Expander
    with st.expander("⚙️ Provider & Model Settings", expanded=False):
        if selected_provider == "Google Gemini (Cloud)":
            env_key = os.getenv("GEMINI_API_KEY", "")
            masked_env = mask_api_key(env_key)

            api_key_input = st.text_input(
                "Gemini API Key",
                type="password",
                value=st.session_state.get("custom_api_key", ""),
                help="Enter your API key or leave blank to use GEMINI_API_KEY from .env",
                placeholder="Enter key to override .env",
            )
            if api_key_input:
                st.session_state["custom_api_key"] = api_key_input.strip()

            st.caption(f"Environment Key: `{masked_env}`")

            model_options = [
                "gemini-flash-lite-latest",
                "gemini-3.1-flash-lite",
                "gemini-pro-latest",
                "gemini-3.8-flash",
                "gemini-1.5-flash",
            ]
            current_env_model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
            default_index = model_options.index(current_env_model) if current_env_model in model_options else 0

            selected_model = st.selectbox(
                "Gemini Vision Model",
                options=model_options,
                index=default_index,
                help="Select the multimodal Gemini model for visual analysis.",
            )
            st.session_state["selected_model"] = selected_model

        else:
            # Ollama (Local) Settings
            ollama_host = st.text_input(
                "Ollama Host URL",
                value=st.session_state.get("custom_ollama_host", os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)),
                help="Base URL of your local or remote Ollama instance.",
            )
            st.session_state["custom_ollama_host"] = ollama_host

            # Check Ollama connection status
            is_online, installed_models = check_ollama_connection(ollama_host)
            if is_online:
                st.success(f"🟢 Ollama Online ({len(installed_models)} model(s) installed)")
            else:
                st.error("🔴 Ollama Offline — Is the Ollama desktop app running?")

            # Model options: combine installed models with known vision models
            combined_models = list(installed_models)
            for m in KNOWN_VISION_MODELS:
                if m not in combined_models:
                    combined_models.append(m)

            current_ollama_model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
            ollama_default_idx = combined_models.index(current_ollama_model) if current_ollama_model in combined_models else 0

            selected_ollama_model = st.selectbox(
                "Ollama Vision Model",
                options=combined_models,
                index=ollama_default_idx,
                help="Select or enter your local Ollama vision model.",
            )
            st.session_state["selected_ollama_model"] = selected_ollama_model

            st.markdown(
                """
                <small>💡 <b>Quick Pull:</b> In your terminal, run:<br>
                <code>ollama run llama3.2-vision</code> or <code>ollama run llava</code></small>
                """,
                unsafe_allow_html=True,
            )

    # Blur & OCR Settings Expander
    with st.expander("🔍 Blur & OCR Settings", expanded=False):
        auto_ocr = st.checkbox(
            "Auto-OCR on unclear/blurry image",
            value=st.session_state.get("auto_ocr", True),
            help="Automatically activates Optical Character Recognition when an image is detected as blurry or low-clarity.",
        )
        st.session_state["auto_ocr"] = auto_ocr

        force_ocr = st.checkbox(
            "Always run OCR on all images",
            value=st.session_state.get("force_ocr", False),
            help="Extract OCR text from every photograph regardless of blur score.",
        )
        st.session_state["force_ocr"] = force_ocr

    st.markdown("### 📊 Conversation Status")
    status_img = "✅ Loaded" if st.session_state.uploaded_image is not None else "⏳ Awaiting Upload"
    msg_count = len(st.session_state.messages)
    conv_id_short = st.session_state.conversation_id[:8] + "..."
    provider_badge = "🌐 Gemini" if selected_provider == "Google Gemini (Cloud)" else "💻 Ollama"
    active_model_name = (
        st.session_state.get("selected_model", DEFAULT_MODEL)
        if selected_provider == "Google Gemini (Cloud)"
        else st.session_state.get("selected_ollama_model", DEFAULT_OLLAMA_MODEL)
    )

    st.markdown(
        f"""
        <div class="sidebar-card">
            <div><strong>Image Status:</strong> {status_img}</div>
            <div><strong>Engine:</strong> {provider_badge}</div>
            <div><strong>Model:</strong> <code>{active_model_name}</code></div>
            <div><strong>Messages:</strong> {msg_count}</div>
            <div><strong>Session ID:</strong> <code>{conv_id_short}</code></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Upload Specifications & Guidelines
    st.markdown("### ℹ️ Upload Guidelines")
    st.markdown(
        """
        - **Formats:** JPG, JPEG, PNG, WEBP
        - **Max File Size:** 10 MB
        - **In-Memory Processing:** Images are never permanently stored.
        - **Orientation:** Auto EXIF correction applied.
        - **Transparency:** PNG alpha composited seamlessly.
        """
    )

    # Persistent SQLite Conversation Log
    with st.expander("📜 Past Sessions (SQLite)", expanded=False):
        past_sessions = get_saved_conversations()
        if past_sessions:
            st.write(f"Found {len(past_sessions)} recorded session(s):")
            for session in past_sessions[:5]:
                st.caption(
                    f"**ID:** {session['conversation_id'][:8]}… | {session['message_count']} msgs  \n"
                    f"*{session['created_at']}*"
                )
            if st.button("Delete History DB", use_container_width=True):
                clear_history_db()
                st.success("History database cleared.")
                st.rerun()
        else:
            st.caption("No saved conversations yet.")


# -----------------------------------------------------------------------------
# Main Application Content
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="vision-header">
        <div class="vision-title">Ask Anything About Your Image</div>
        <div class="vision-subtitle">Upload a photograph and let AI understand what is inside it.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Active Model and Provider resolution
is_gemini = (st.session_state.get("selected_provider") == "Google Gemini (Cloud)")
effective_api_key = st.session_state.get("custom_api_key") or os.getenv("GEMINI_API_KEY", "")
effective_gemini_model = st.session_state.get("selected_model") or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
effective_ollama_host = st.session_state.get("custom_ollama_host") or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
effective_ollama_model = st.session_state.get("selected_ollama_model") or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

# Provider-specific upfront alerts
if is_gemini:
    if not effective_api_key or effective_api_key in ("your_api_key", "your_gemini_api_key_here"):
        st.warning(
            "⚠️ **Gemini API Key Required:** Please configure `GEMINI_API_KEY` in your `.env` file, "
            "or expand the **Provider & Model Settings** in the sidebar to enter your API key."
        )
else:
    is_online, _ = check_ollama_connection(effective_ollama_host)
    if not is_online:
        st.warning(
            f"⚠️ **Ollama Offline:** Unable to reach Ollama at `{effective_ollama_host}`. "
            "Please ensure Ollama is running on your machine, or switch provider to Google Gemini."
        )

# Layout: Split into two responsive columns when image is loaded, or centered view
if st.session_state.uploaded_image is not None:
    left_col, right_col = st.columns([4, 6], gap="large")
else:
    left_col, right_col = st.columns([1, 1], gap="large")

# -----------------------------------------------------------------------------
# Left Column: Image Upload & Preview
# -----------------------------------------------------------------------------
with left_col:
    st.subheader("📸 Photograph")

    # File uploader widget
    uploaded_file = st.file_uploader(
        "Upload your photograph",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"uploader_{st.session_state.uploader_key}",
        help="Upload a JPG, JPEG, PNG, or WEBP image up to 10 MB.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_hash = hash(file_bytes)

        # Check if user uploaded a different image
        if st.session_state.image_id != file_hash:
            try:
                processed_img, metadata = process_uploaded_image(file_bytes)
                st.session_state.uploaded_image = processed_img
                st.session_state.image_metadata = metadata
                st.session_state.image_id = file_hash

                # Analyze image clarity and run OCR if unclear
                clarity_res = analyze_image_clarity_and_ocr(
                    processed_img,
                    force_ocr=st.session_state.get("force_ocr", False),
                    auto_ocr_if_unclear=st.session_state.get("auto_ocr", True),
                )
                st.session_state.clarity_info = clarity_res

                # Reset conversation to prevent old answers from contaminating the new image
                st.session_state.messages = []
                st.session_state.conversation_id = generate_conversation_id()

                # Record new conversation session in SQLite
                save_conversation_meta(
                    st.session_state.conversation_id,
                    title=f"Chat ({metadata['format']} {metadata['current_width']}x{metadata['current_height']})",
                    metadata_str=f"{metadata['size_mb']} MB",
                )
                st.rerun()

            except ImageValidationError as e:
                st.error(f"Image Error: {str(e)}")
            except Exception as e:
                st.error(f"Failed to process image: {str(e)}")

    # Display image preview if image is active in session
    if st.session_state.uploaded_image is not None:
        meta = st.session_state.image_metadata or {}
        st.image(
            st.session_state.uploaded_image,
            caption="Uploaded Photograph Preview",
            use_container_width=True,
        )

        # Ensure clarity info is computed
        if st.session_state.clarity_info is None:
            st.session_state.clarity_info = analyze_image_clarity_and_ocr(
                st.session_state.uploaded_image,
                force_ocr=st.session_state.get("force_ocr", False),
                auto_ocr_if_unclear=st.session_state.get("auto_ocr", True),
            )

        clarity = st.session_state.clarity_info or {}
        is_unclear = clarity.get("is_unclear", False)
        c_score = clarity.get("clarity_score", 0)
        ocr_applied = clarity.get("ocr_applied", False)
        ocr_text = clarity.get("ocr_text", "")

        clarity_badge = (
            f"<span class='meta-badge' style='background:#fef3c7; color:#92400e;'>⚠️ Unclear/Blurry (Sharpness: {c_score})</span>"
            if is_unclear
            else f"<span class='meta-badge' style='background:#ecfdf5; color:#065f46;'>✅ Sharp (Score: {c_score})</span>"
        )
        if ocr_applied and ocr_text:
            clarity_badge += f"<span class='meta-badge' style='background:#ede9fe; color:#5b21b6;'>🔍 OCR Text Recovered</span>"

        # Display image metadata badges
        st.markdown(
            f"""
            <div class="meta-badge-container">
                <span class="meta-badge">Format: {meta.get('format', 'Image')}</span>
                <span class="meta-badge">Dimensions: {meta.get('current_width', '?')} × {meta.get('current_height', '?')} px</span>
                <span class="meta-badge">File Size: {meta.get('size_mb', '?')} MB</span>
                {"<span class='meta-badge' style='background:#fef3c7; color:#92400e;'>Resized</span>" if meta.get('was_resized') else ""}
                {clarity_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show OCR Extracted text if text was recovered from unclear image
        if ocr_text:
            with st.expander("🔍 OCR Extracted Text (Auto-Recovered from Unclear Image)", expanded=False):
                st.text_area("Extracted OCR Text", value=ocr_text, height=100, disabled=True, label_visibility="collapsed")

        # Action to remove image
        if st.button("🗑️ Remove Image", use_container_width=True):
            reset_conversation(st.session_state, clear_image=True)
            st.rerun()
    else:
        st.info("👆 Upload an image above to begin asking questions.")


# -----------------------------------------------------------------------------
# Right Column: Visual Question Answering Chat Interface
# -----------------------------------------------------------------------------
with right_col:
    st.subheader("💬 Vision Conversation")

    # Render conversation history
    if not st.session_state.messages:
        if st.session_state.uploaded_image is not None:
            st.markdown(
                """
                *Your photograph is ready! Ask any question below, such as:*
                - *"What objects are in this image?"*
                - *"What does the visible text say?"*
                - *"Describe the lighting and atmosphere."*
                - *"Can you solve or explain the equation/code in the photo?"*
                """
            )
        else:
            st.markdown("*Upload an image to start the visual conversation.*")

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input widget
    prompt = st.chat_input(
        "Ask a question about this photograph..."
        if st.session_state.uploaded_image is not None
        else "Upload an image first to ask questions..."
    )

    if prompt:
        # 1. Guard: Ensure an image is uploaded
        if st.session_state.uploaded_image is None:
            st.warning("⚠️ Please upload a photograph before asking a question.")
        else:
            try:
                # 2. Validate question input
                clean_question = validate_question(prompt)

                # 3. Append and render user question
                st.session_state.messages.append({"role": "user", "content": clean_question})
                with st.chat_message("user"):
                    st.markdown(clean_question)

                # Save user message to persistent DB
                save_message_to_db(
                    st.session_state.conversation_id,
                    "user",
                    clean_question,
                )

                # 4. Generate answer with AI model based on chosen provider
                with st.chat_message("assistant"):
                    prior_history = st.session_state.messages[:-1]

                    # Enrich prompt with OCR text if image was unclear and text was recovered
                    ai_question = clean_question
                    clarity_data = st.session_state.clarity_info or {}
                    if clarity_data.get("ocr_text"):
                        extracted_txt = clarity_data["ocr_text"]
                        c_score = clarity_data.get("clarity_score", 0)
                        ai_question = (
                            f"{clean_question}\n\n"
                            f"[OCR Visual Aid: This photograph was detected as low-clarity/blurry "
                            f"(Sharpness score: {c_score}). "
                            f"Automated Optical Character Recognition recovered the following text using image enhancement filters:\n"
                            f"\"\"\"{extracted_txt}\"\"\"\n"
                            f"Please incorporate this text to answer accurately.]"
                        )

                    if is_gemini:
                        with st.spinner(f"VisionQA is analyzing with Gemini ({effective_gemini_model})..."):
                            response_text = answer_image_question(
                                image=st.session_state.uploaded_image,
                                question=ai_question,
                                conversation_history=prior_history,
                                api_key=effective_api_key,
                                model_name=effective_gemini_model,
                            )
                    else:
                        with st.spinner(f"VisionQA is analyzing with Ollama ({effective_ollama_model})..."):
                            response_text = answer_image_question_ollama(
                                image=st.session_state.uploaded_image,
                                question=ai_question,
                                conversation_history=prior_history,
                                model=effective_ollama_model,
                                host=effective_ollama_host,
                            )

                    st.markdown(response_text)

                # 5. Append assistant answer to state and database
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                save_message_to_db(
                    st.session_state.conversation_id,
                    "assistant",
                    response_text,
                )

            except ValueError as e:
                st.warning(str(e))
            except (VisionServiceError, OllamaServiceError) as e:
                st.error(f"Error: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred while processing your request: {str(e)}")
