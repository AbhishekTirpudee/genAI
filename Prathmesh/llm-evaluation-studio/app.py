"""
LLM Evaluation Studio
Main Application Entry Point.
Modular architecture with Streamlit, Plotly, SQLite, and Google Gemini SDK.
"""

import streamlit as st
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import init_db, seed_sample_evaluations, get_analytics_summary
from frontend.dashboard import render_dashboard
from frontend.evaluation import render_evaluation_page
from frontend.history import render_history_page
from frontend.analytics import render_analytics_page
from frontend.settings import render_settings_page


# Streamlit Page Configuration
st.set_page_config(
    page_title="LLM Evaluation Studio",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional CSS
CUSTOM_CSS = """
<style>
    /* Global font and smoothness */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main container padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1350px;
    }

    /* Sidebar aesthetics */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Custom Radio Navigation in Sidebar */
    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    /* Metrics and cards styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2), 0 2px 4px -2px rgba(37, 99, 235, 0.2);
        font-weight: 600;
        transition: transform 0.1s ease;
    }

    button[kind="primary"]:hover {
        transform: translateY(-1px);
    }

    /* Expander borders */
    div[data-testid="stExpander"] {
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        background-color: #FFFFFF;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_app():
    """Perform application startup initialization."""
    init_db()
    
    # Auto-seed sample benchmark records if DB is completely empty on initial launch
    stats = get_analytics_summary()
    if stats["total_evaluations"] == 0:
        seed_sample_evaluations()


def main():
    """Main routing and navigation controller."""
    init_app()

    # Sidebar Navigation Branding
    with st.sidebar:
        st.markdown("""
            <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #334155; margin-bottom: 1.5rem;">
                <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em; color: #FFFFFF;">
                    ⚖️ LLM Evaluation Studio
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 2px;">
                    Model Comparison & Automated Benchmarking
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Navigation state control
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Dashboard"

        pages = [
            "Dashboard",
            "New Evaluation",
            "Evaluation History",
            "Analytics",
            "Settings"
        ]

        page_icons = {
            "Dashboard": "📊",
            "New Evaluation": "⚖️",
            "Evaluation History": "📜",
            "Analytics": "📈",
            "Settings": "⚙️"
        }

        # Page selector
        selected_page = st.radio(
            "Navigation",
            options=pages,
            index=pages.index(st.session_state["current_page"]),
            format_func=lambda p: f"{page_icons.get(p, '')}  {p}",
            label_visibility="collapsed"
        )

        st.session_state["current_page"] = selected_page

        st.markdown("<br><br>", unsafe_allow_html=True)

        # Quick summary card in sidebar footer
        stats = get_analytics_summary()
        st.markdown(f"""
            <div style="background: #1E293B; border-radius: 8px; padding: 0.9rem; font-size: 0.8rem; border: 1px solid #334155;">
                <div style="color: #94A3B8; font-weight: 600; text-transform: uppercase; font-size: 0.7rem;">Studio Status</div>
                <div style="margin-top: 4px; color: #F1F5F9;">
                    Evaluations: <b>{stats['total_evaluations']}</b><br>
                    Engine: <b>Google Gen AI</b><br>
                    Persistence: <b>SQLite DB</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Route navigation
    def navigate_to(page_name: str):
        st.session_state["current_page"] = page_name
        st.rerun()

    current = st.session_state["current_page"]
    if current == "Dashboard":
        render_dashboard(navigate_to=navigate_to)
    elif current == "New Evaluation":
        render_evaluation_page()
    elif current == "Evaluation History":
        render_history_page()
    elif current == "Analytics":
        render_analytics_page()
    elif current == "Settings":
        render_settings_page()


if __name__ == "__main__":
    main()

