"""
=============================================================================
Project: Local AI Email Drafting Assistant Using Ollama
Model: Llama 3.2 (1B)
Framework: Streamlit & Python Requests
Description: A beginner-friendly local AI application to draft professional,
             customized emails using an open-source LLM running locally.
=============================================================================
"""

import streamlit as st
import requests
import json
import pyperclip

# =============================================================================
# 1. APPLICATION CONFIGURATION & CONSTANTS
# =============================================================================
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
DEFAULT_MODEL = "llama3.2:1b"
REQUEST_TIMEOUT = 60  # seconds


# =============================================================================
# 2. HELPER FUNCTIONS: OLLAMA STATUS, PROMPT BUILDER & API CLIENT
# =============================================================================
def check_ollama_status() -> tuple[bool, list[str]]:
    """
    Checks if the local Ollama service is reachable and retrieves the list
    of downloaded models.
    
    Returns:
        tuple (is_online: bool, models_available: list[str])
    """
    # Try 127.0.0.1 first, then localhost fallback
    for url in [OLLAMA_TAGS_URL, "http://localhost:11434/api/tags"]:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return True, models
        except Exception:
            continue
    return False, []


def construct_prompt(subject: str, key_points: str, tone: str, recipient: str = "") -> str:
    """
    Constructs an effective, constraint-bound prompt for Llama 3.2 (1B).
    Instructs the model to follow specific rules:
    - Include subject, greeting, well-structured body, and closing.
    - Strictly adhere to the chosen tone.
    - Avoid inventing unmentioned facts (prevent hallucinations).
    - Output only the email without meta-commentary or explanations.
    """
    recipient_instruction = (
        f"Address the email specifically to '{recipient.strip()}'."
        if recipient.strip()
        else "Use an appropriate generic professional salutation (e.g., 'Dear Sir/Madam,' or 'Hello,')."
    )

    prompt = f"""You are an expert AI email drafting assistant. Your task is to draft a complete, polished, and natural email based strictly on the user's inputs.

Follow these strict instructions:
1. Tone: Maintain a strictly {tone} tone throughout the email.
2. Salutation / Greeting: {recipient_instruction}
3. Subject Line: Include a clear Subject line at the beginning matching: "{subject}".
4. Body Paragraphs:
   - Structure the body into well-formed sentences and paragraphs based on these key points:
{key_points}
   - Improve grammar, readability, and sentence flow.
   - Do NOT invent facts, dates, names, or promises not mentioned in the key points.
5. Sign-off / Closing:
   - Provide an appropriate closing based on the {tone} tone (e.g., 'Sincerely,', 'Best regards,', 'Warm regards,').
   - Include a placeholder signature line: '[Your Name]'.
6. Output Restriction:
   - Output ONLY the email (Subject, Salutation, Body, and Closing).
   - Do NOT include any introductory chit-chat, explanations, preamble, or meta-notes.

Email Draft:"""
    return prompt


def generate_email_with_ollama(prompt: str, model: str = DEFAULT_MODEL) -> tuple[bool, str]:
    """
    Sends a synchronous POST request to Ollama's /api/generate endpoint.
    
    Args:
        prompt (str): The structured prompt.
        model (str): Target Ollama model name (e.g., 'llama3.2:1b').
        
    Returns:
        tuple (success: bool, result_or_error_message: str)
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,  # As required: single complete response
        "options": {
            "temperature": 0.4,  # Lower temperature reduces hallucinations & improves formality
            "top_p": 0.9
        }
    }

    # Attempt connection with fallback between 127.0.0.1 and localhost
    endpoints = [OLLAMA_API_URL, "http://localhost:11434/api/generate"]
    last_error = None

    for endpoint in endpoints:
        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            # HTTP 200 OK
            if response.status_code == 200:
                data = response.json()
                email_text = data.get("response", "").strip()
                if email_text:
                    return True, email_text
                else:
                    return False, "Ollama returned an empty response. Please check your prompt and try again."

            # Model not found on Ollama (HTTP 404)
            elif response.status_code == 404:
                return False, (
                    f"Model '{model}' was not found in your Ollama installation.\n"
                    f"Please open your terminal and download it by running:\n"
                    f"    ollama pull {model}"
                )

            # Other HTTP errors
            else:
                return False, f"Ollama API error (Status Code: {response.status_code}): {response.text}"

        except requests.exceptions.ConnectionError as ce:
            last_error = ce
            continue

        except requests.exceptions.Timeout:
            return False, (
                f"The request timed out after {REQUEST_TIMEOUT} seconds.\n"
                "The model may be busy loading into memory. Please try again."
            )

        except Exception as e:
            return False, f"An unexpected error occurred while communicating with Ollama: {str(e)}"

    # If all connection attempts failed:
    return False, (
        "Cannot connect to Ollama server at http://localhost:11434 or http://127.0.0.1:11434.\n"
        "Please ensure that:\n"
        "1. Ollama is installed on your computer.\n"
        "2. Ollama is running in the background. Start it by running 'ollama serve' in your terminal."
    )


# =============================================================================
# 3. STREAMLIT USER INTERFACE APPLICATION
# =============================================================================
def main():
    # Configure Streamlit page settings
    st.set_page_config(
        page_title="AI Email Drafting Assistant",
        page_icon="✉️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for modern styling
    st.markdown("""
    <style>
        .main-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            font-size: 1.05rem;
            color: #4B5563;
            margin-bottom: 1.5rem;
        }
        .section-header {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1F2937;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #E5E7EB;
            margin-bottom: 1rem;
        }
        .status-badge-online {
            background-color: #DEF7EC;
            color: #03543F;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
        }
        .status-badge-offline {
            background-color: #FDE8E8;
            color: #9B1C1C;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
        }
    </style>
    """, unsafe_allow_html=True)

    # Session State Initialization
    if "subject" not in st.session_state:
        st.session_state.subject = ""
    if "recipient" not in st.session_state:
        st.session_state.recipient = ""
    if "key_points" not in st.session_state:
        st.session_state.key_points = ""
    if "tone" not in st.session_state:
        st.session_state.tone = "Professional"
    if "generated_email" not in st.session_state:
        st.session_state.generated_email = ""

    def clear_inputs():
        """Reset all inputs and generated content in session state."""
        st.session_state.subject = ""
        st.session_state.recipient = ""
        st.session_state.key_points = ""
        st.session_state.tone = "Professional"
        st.session_state.generated_email = ""

    # Sidebar: Status & Instructions
    with st.sidebar:
        st.markdown("### ⚙️ System Status")
        
        is_online, installed_models = check_ollama_status()
        
        if is_online:
            st.markdown(
                '<div><span class="status-badge-online">● Ollama Service Online</span></div>',
                unsafe_allow_html=True
            )
            st.caption("Connected to `http://localhost:11434`")
            
            has_target_model = any(DEFAULT_MODEL in m for m in installed_models)
            if has_target_model:
                st.success(f"Model `{DEFAULT_MODEL}` is ready.")
            else:
                st.warning(f"Model `{DEFAULT_MODEL}` not detected. Available: {installed_models if installed_models else 'None'}")
                st.code(f"ollama pull {DEFAULT_MODEL}", language="bash")
        else:
            st.markdown(
                '<div><span class="status-badge-offline">● Ollama Service Offline</span></div>',
                unsafe_allow_html=True
            )
            st.error("Ollama is not running. Please start it locally.")
            st.code("ollama serve", language="bash")

        st.divider()

        st.markdown("### 📋 Quick Guide")
        st.markdown("""
        1. **Enter Subject**: What the email is about.
        2. **Recipient (Optional)**: Person or entity you are writing to.
        3. **Select Tone**: Choose Formal, Professional, Friendly, or Polite.
        4. **Add Key Points**: Mention all important details.
        5. **Generate**: Click **Generate Email** to draft.
        6. **Edit & Copy**: Refine in the editor and copy to clipboard.
        """)

        st.divider()
        st.caption("🔒 100% Private & Local AI. No cloud APIs or data leakage.")

    # Main Page Headers
    st.markdown('<div class="main-title">✉️ AI Email Drafting Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Generate polished, professional emails locally using Ollama and Llama 3.2 (1B).</div>',
        unsafe_allow_html=True
    )

    # Two-column layout
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown('<div class="section-header">📝 Email Details</div>', unsafe_allow_html=True)

        # 1. Subject Input
        subject = st.text_input(
            "Email Subject *",
            placeholder="e.g., Request for Leave, Follow-up on Project Proposal",
            key="subject",
            help="Provide a concise summary of the email topic."
        )

        # 2. Recipient Name (Optional)
        recipient = st.text_input(
            "Recipient Name (Optional)",
            placeholder="e.g., Dr. Smith, Professor Sharma, HR Manager",
            key="recipient",
            help="Optional name or title to personalize the greeting."
        )

        # 3. Email Tone Dropdown
        tone_options = ["Professional", "Formal", "Friendly", "Polite"]
        tone = st.selectbox(
            "Select Email Tone *",
            options=tone_options,
            key="tone",
            help="Choose the style and formality of the email."
        )

        # 4. Key Points Multiline Text Area
        key_points = st.text_area(
            "Key Points to Include *",
            placeholder=(
                "Enter key points or bullet notes, for example:\n"
                "- Unable to attend college tomorrow\n"
                "- Have an important family event\n"
                "- Request one day of casual leave\n"
                "- Will catch up on missed notes immediately"
            ),
            height=180,
            key="key_points",
            help="List all important facts and requests. The AI will weave these into cohesive paragraphs."
        )

        # Action Buttons: Generate & Clear
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            generate_clicked = st.button("🚀 Generate Email", type="primary", use_container_width=True)
        with col_btn2:
            st.button("🗑️ Clear", on_click=clear_inputs, use_container_width=True)

    # Generation Trigger & Validation
    if generate_clicked:
        if not subject.strip():
            st.error("⚠️ Please enter an email subject before generating.")
        elif not key_points.strip():
            st.error("⚠️ Please provide key points to include in the email body.")
        else:
            prompt = construct_prompt(
                subject=subject.strip(),
                key_points=key_points.strip(),
                tone=tone,
                recipient=recipient.strip()
            )

            with st.spinner("🤖 Ollama is drafting your email using Llama 3.2 (1B)..."):
                success, result = generate_email_with_ollama(prompt, model=DEFAULT_MODEL)

                if success:
                    st.session_state.generated_email = result
                    st.success("✅ Email generated successfully!")
                else:
                    st.error(result)

    # Output Column
    with col_output:
        st.markdown('<div class="section-header">📄 Generated Email</div>', unsafe_allow_html=True)

        if st.session_state.generated_email:
            edited_email = st.text_area(
                "Review & Edit Draft:",
                value=st.session_state.generated_email,
                height=320,
                key="email_editor",
                help="You can edit the generated draft directly before copying or sending."
            )

            st.session_state.generated_email = edited_email

            word_count = len(edited_email.split())
            char_count = len(edited_email)
            st.caption(f"📊 Words: **{word_count}** | Characters: **{char_count}** | Tone: **{st.session_state.tone}**")

            col_copy1, col_copy2 = st.columns([1, 1])
            with col_copy1:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    try:
                        pyperclip.copy(st.session_state.generated_email)
                        st.toast("Email copied to clipboard!", icon="📋")
                    except Exception:
                        st.info("Tip: You can also use the copy button in the code preview below or select all text.")

            with st.expander("🔍 Formatted Code Block Preview (One-Click Copy)", expanded=True):
                st.code(st.session_state.generated_email, language=None)

        else:
            st.info("👈 Fill in the email details on the left and click **'Generate Email'** to preview your draft here.")
            st.markdown("""
            <div style="background-color: #F3F4F6; border: 2px dashed #D1D5DB; border-radius: 8px; height: 260px; display: flex; align-items: center; justify-content: center; color: #9CA3AF; text-align: center; padding: 1.5rem;">
                <div>
                    <p style="font-size: 2rem; margin: 0;">✉️</p>
                    <p style="font-weight: 500; margin: 0.5rem 0 0 0;">No email generated yet</p>
                    <small>Your generated draft will appear here ready to review, edit, and copy.</small>
                </div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
