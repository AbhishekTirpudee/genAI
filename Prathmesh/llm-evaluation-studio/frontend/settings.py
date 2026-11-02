"""
Settings Page for LLM Evaluation Studio.
Configures Gemini API credentials, default model selections, rubric weight defaults,
API connection testing, and sample benchmark database seeding.
"""

import streamlit as st
import os
import sys
from backend.config import (
    AVAILABLE_MODELS,
    MODEL_IDS,
    DEFAULT_MODEL_A,
    DEFAULT_MODEL_B,
    DEFAULT_JUDGE_MODEL,
    DEFAULT_RUBRIC_WEIGHTS,
    get_api_key,
    set_api_key,
    is_demo_mode,
    DB_PATH
)
from backend.database import seed_sample_evaluations, get_analytics_summary

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def render_settings_page():
    """Render the configuration and settings management interface."""
    st.markdown("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <h2 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1E293B;">
                ⚙️ Studio Settings & Configuration
            </h2>
            <p style="margin: 0.2rem 0 1rem 0; color: #64748B;">
                Manage Google Gemini API authentication, model defaults, evaluation parameters, and sample datasets.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Google Gemini API Configuration Card
    st.markdown("### 🔑 Google Gemini API Authentication")
    current_key = get_api_key()
    masked_key = (current_key[:4] + "*" * (len(current_key) - 8) + current_key[-4:]) if len(current_key) > 8 else ""

    if current_key:
        st.success(f"API Key is configured: `{masked_key}`")
    else:
        st.warning("No API key configured. Studio is currently operating in simulated Demo Mode.")

    col_key_input, col_key_btn = st.columns([3, 1])
    with col_key_input:
        new_key = st.text_input(
            "Enter Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Your key is never logged or stored in public repositories. It is persisted securely to your local .env file."
        )
    with col_key_btn:
        st.write("")
        st.write("")
        if st.button("Save API Key", use_container_width=True, type="primary"):
            if new_key.strip():
                success = set_api_key(new_key)
                if success:
                    st.success("API Key saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save API key to .env file.")
            else:
                st.warning("Please enter a valid API key.")

    # API Connection Test
    col_test, col_demo = st.columns([1, 1])
    with col_test:
        if st.button("🔌 Test API Connection", use_container_width=True):
            test_key = get_api_key()
            if not test_key:
                st.error("Cannot test: No API key found. Please enter and save an API key above.")
            elif not GENAI_AVAILABLE:
                st.error("google-genai package is not installed.")
            else:
                with st.spinner("Pinging Gemini API with lightweight probe..."):
                    try:
                        client = genai.Client(api_key=test_key)
                        res = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents="Say 'API connection verified!' in 4 words."
                        )
                        st.success(f"✅ Connection Successful! Response: {res.text.strip()}")
                    except Exception as e:
                        st.error(f"❌ Connection Failed: {str(e)}")

    with col_demo:
        demo_state = is_demo_mode()
        st.write(f"**Demo Simulation Mode:** `{'Enabled' if demo_state else 'Auto (uses live API if key is set)'}`")

    st.write("---")

    # 2. Default Models Configuration
    st.markdown("### 🤖 Default Model Selections")
    c_m1, c_m2, c_m3 = st.columns(3)

    with c_m1:
        st.selectbox(
            "Default Model A",
            options=MODEL_IDS,
            index=MODEL_IDS.index(DEFAULT_MODEL_A) if DEFAULT_MODEL_A in MODEL_IDS else 0,
            help="Default model pre-selected in Model A dropdown."
        )

    with c_m2:
        st.selectbox(
            "Default Model B",
            options=MODEL_IDS,
            index=MODEL_IDS.index(DEFAULT_MODEL_B) if DEFAULT_MODEL_B in MODEL_IDS else 1,
            help="Default model pre-selected in Model B dropdown."
        )

    with c_m3:
        st.selectbox(
            "Default Judge Model",
            options=MODEL_IDS,
            index=MODEL_IDS.index(DEFAULT_MODEL_JUDGE) if 'DEFAULT_MODEL_JUDGE' in locals() and DEFAULT_MODEL_JUDGE in MODEL_IDS else (MODEL_IDS.index(DEFAULT_JUDGE_MODEL) if DEFAULT_JUDGE_MODEL in MODEL_IDS else 1),
            help="Default model pre-selected for the LLM judge."
        )

    st.write("---")

    # 3. Sample Benchmark Data Seeding
    st.markdown("### 🗄️ Database & Benchmark Dataset")
    st.caption("Populate your local SQLite database with 5 pre-computed benchmark evaluations to immediately explore the History and Analytics tabs.")

    col_seed, col_info = st.columns([1, 2])
    with col_seed:
        if st.button("🌱 Seed Sample Benchmark Dataset", use_container_width=True):
            count = seed_sample_evaluations()
            if count > 0:
                st.success(f"Successfully seeded {count} benchmark evaluations into database!")
            else:
                st.info("Sample evaluations already exist in the database.")
            st.rerun()

    with col_info:
        stats = get_analytics_summary()
        st.markdown(f"**Database Location:** `{DB_PATH}`  \n**Current Records:** `{stats['total_evaluations']}` evaluations")

    st.write("---")

    # 4. Environment & System Information
    st.markdown("### 💻 Environment Diagnostics")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.markdown(f"""
            - **Python Version:** `{sys.version.split()[0]}`
            - **Streamlit Version:** `{st.__version__}`
            - **Google Gen AI SDK:** `{'Available' if GENAI_AVAILABLE else 'Missing'}`
        """)
    with d_col2:
        st.markdown(f"""
            - **Database Engine:** `SQLite 3`
            - **Visualization Engine:** `Plotly 7.1.0`
            - **Active OS:** `{os.name}`
        """)

