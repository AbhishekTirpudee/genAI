"""
Dashboard page for LLM Evaluation Studio.
Presents high-level metrics, recent benchmark evaluations, and quick action launchpads.
"""

import streamlit as st
import pandas as pd
from backend.database import get_analytics_summary, get_all_evaluations
from backend.config import get_api_key, is_demo_mode


def render_dashboard(navigate_to):
    """Render the main executive overview dashboard."""
    st.markdown("""
        <div style="padding: 1.5rem 0 1rem 0;">
            <h1 style="margin: 0; font-size: 2.3rem; font-weight: 700; background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                LLM Evaluation Studio
            </h1>
            <p style="margin: 0.35rem 0 0 0; color: #64748B; font-size: 1.05rem;">
                Compare Large Language Models with automated LLM-as-a-Judge benchmarking, customizable rubrics, and detailed dimensional analytics.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # API Status alert / banner
    api_key = get_api_key()
    demo = is_demo_mode() or not api_key

    if demo:
        st.info("💡 **Demo / Mock Mode Active**: You can run evaluations, test custom rubrics, and explore all analytics immediately with high-fidelity simulated responses. To use live Google Gemini API endpoints, set your API key in **Settings**.")

    # Fetch stats
    stats = get_analytics_summary()
    total_evals = stats["total_evaluations"]
    winner_counts = stats["winner_counts"]
    model_stats = stats.get("model_stats", {})

    # Top performing model
    top_model = "None yet"
    top_winrate = 0.0
    for m, mdata in model_stats.items():
        if mdata.get("appearances", 0) >= 2 and mdata.get("win_rate", 0) > top_winrate:
            top_model = m
            top_winrate = mdata.get("win_rate", 0)

    # Metric KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 12px; padding: 1.2rem; text-align: center;">
                <div style="color: #3B82F6; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Total Evaluations</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin: 0.3rem 0; color: #1E293B;">{total_evals}</div>
                <div style="font-size: 0.8rem; color: #64748B;">Evaluations in SQLite DB</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        model_a_wins = winner_counts.get("Model A", 0)
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 1.2rem; text-align: center;">
                <div style="color: #10B981; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Model A Wins</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin: 0.3rem 0; color: #1E293B;">{model_a_wins}</div>
                <div style="font-size: 0.8rem; color: #64748B;">Total victories</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        model_b_wins = winner_counts.get("Model B", 0)
        st.markdown(f"""
            <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 12px; padding: 1.2rem; text-align: center;">
                <div style="color: #8B5CF6; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Model B Wins</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin: 0.3rem 0; color: #1E293B;">{model_b_wins}</div>
                <div style="font-size: 0.8rem; color: #64748B;">Total victories</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        avg_score = stats.get("avg_overall", 0.0)
        st.markdown(f"""
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 12px; padding: 1.2rem; text-align: center;">
                <div style="color: #F59E0B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Average Score</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin: 0.3rem 0; color: #1E293B;">{avg_score:.1f}<span style="font-size: 1.1rem; color: #94A3B8;">/10</span></div>
                <div style="font-size: 0.8rem; color: #64748B;">Across all evaluated models</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Quick Launch Buttons
    col_act1, col_act2, col_act3 = st.columns([1, 1, 1])
    with col_act1:
        if st.button("🚀 Launch New Evaluation", use_container_width=True, type="primary"):
            navigate_to("New Evaluation")
    with col_act2:
        if st.button("📜 Browse Evaluation History", use_container_width=True):
            navigate_to("Evaluation History")
    with col_act3:
        if st.button("📈 View Model Analytics", use_container_width=True):
            navigate_to("Analytics")

    st.write("---")

    # Recent evaluations table
    st.markdown("### 🕒 Recent Evaluations")
    recent = get_all_evaluations(limit=5)

    if not recent:
        st.info("No evaluations found in database. Click **Launch New Evaluation** above or seed sample benchmarks in **Settings** to populate the history.")
    else:
        recent_rows = []
        for r in recent:
            recent_rows.append({
                "Date & Time": r.get("timestamp", "")[:16],
                "Question Prompt": r.get("question", "")[:60] + ("..." if len(r.get("question", "")) > 60 else ""),
                "Model A": r.get("model_a"),
                "Model B": r.get("model_b"),
                "Score A": f"{r.get('overall_a', 0.0):.2f}",
                "Score B": f"{r.get('overall_b', 0.0):.2f}",
                "Winner": r.get("winner")
            })
        df_recent = pd.DataFrame(recent_rows)
        st.dataframe(df_recent, use_container_width=True, hide_index=True)

    # Guided quick presets
    st.write("---")
    st.markdown("### 🎯 Benchmark Categories & Testing Scenarios")
    pcol1, pcol2, pcol3 = st.columns(3)

    with pcol1:
        st.markdown("""
            <div style="border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.2rem; height: 100%;">
                <h4 style="margin-top: 0; color: #1E293B;">💻 Algorithmic & Code Correctness</h4>
                <p style="font-size: 0.9rem; color: #64748B;">
                    Evaluate time & space complexities, edge-case coverage, and idiomatic implementations against canonical solutions.
                </p>
                <div style="font-size: 0.8rem; color: #3B82F6; font-weight: 600;">Recommended: Gemini 2.5 Flash vs Pro</div>
            </div>
        """, unsafe_allow_html=True)

    with pcol2:
        st.markdown("""
            <div style="border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.2rem; height: 100%;">
                <h4 style="margin-top: 0; color: #1E293B;">🩺 Domain Expertise & Truthfulness</h4>
                <p style="font-size: 0.9rem; color: #64748B;">
                    Test factual precision, absence of hallucinations, and nuanced scientific terminology with clinical ground-truth.
                </p>
                <div style="font-size: 0.8rem; color: #10B981; font-weight: 600;">Accuracy Rubric Weight: 40-50%</div>
            </div>
        """, unsafe_allow_html=True)

    with pcol3:
        st.markdown("""
            <div style="border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.2rem; height: 100%;">
                <h4 style="margin-top: 0; color: #1E293B;">🛡️ Prompt Injection Resilience</h4>
                <p style="font-size: 0.9rem; color: #64748B;">
                    Verify that candidate responses containing adversarial system overrides are safely quarantined by the untrusted-data judge.
                </p>
                <div style="font-size: 0.8rem; color: #8B5CF6; font-weight: 600;">Untrusted Data Enclosure Guardrails</div>
            </div>
        """, unsafe_allow_html=True)

