"""
Evaluation History page for LLM Evaluation Studio.
Search, inspect, filter, delete, and export past model evaluations.
"""

import streamlit as st
import pandas as pd
from backend.database import (
    get_all_evaluations,
    get_evaluation_by_id,
    delete_evaluation,
    clear_all_evaluations
)
from utils.export import export_to_csv, export_to_json


def render_history_page():
    """Render the evaluation log and historical inspection interface."""
    st.markdown("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <h2 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1E293B;">
                📜 Evaluation History & Records
            </h2>
            <p style="margin: 0.2rem 0 1rem 0; color: #64748B;">
                Inspect past benchmark evaluations stored in SQLite, analyze qualitative judge notes, and export datasets.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Search and Filter Toolbar
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search Prompt or Model", placeholder="Filter by prompt keyword, model name...", label_visibility="collapsed")
    with f_col2:
        winner_filter = st.selectbox("Filter Winner", options=["All", "Model A", "Model B", "Tie"], index=0, label_visibility="collapsed")
    with f_col3:
        record_limit = st.selectbox("Display Limit", options=[10, 25, 50, 100], index=1, label_visibility="collapsed")

    # Fetch records
    evaluations = get_all_evaluations(
        limit=record_limit,
        search=search_query if search_query.strip() else None,
        winner_filter=winner_filter
    )

    if not evaluations:
        st.info("No matching evaluation records found. Try adjusting your search or run a new evaluation.")
        return

    # Export toolbar
    e_col1, e_col2, e_col3 = st.columns([1, 1, 2])
    with e_col1:
        csv_data = export_to_csv(evaluations)
        st.download_button(
            label="📥 Export as CSV",
            data=csv_data,
            file_name="llm_evaluations.csv",
            mime="text/csv",
            use_container_width=True
        )
    with e_col2:
        json_data = export_to_json(evaluations)
        st.download_button(
            label="📥 Export as JSON",
            data=json_data,
            file_name="llm_evaluations.json",
            mime="application/json",
            use_container_width=True
        )

    st.write("")

    # Historical Records List
    st.markdown(f"**Showing {len(evaluations)} evaluation runs**")

    for rec in evaluations:
        eval_id = rec.get("id")
        ts = rec.get("timestamp", "")
        q_snippet = rec.get("question", "")[:90] + ("..." if len(rec.get("question", "")) > 90 else "")
        model_a = rec.get("model_a", "")
        model_b = rec.get("model_b", "")
        winner = rec.get("winner", "Tie")
        score_a = rec.get("overall_a", 0.0)
        score_b = rec.get("overall_b", 0.0)

        # Winner badge color
        if winner == "Model A":
            badge = f'<span style="background: #DBEAFE; color: #1E40AF; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;">Model A Won ({score_a:.2f} vs {score_b:.2f})</span>'
        elif winner == "Model B":
            badge = f'<span style="background: #D1FAE5; color: #065F46; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;">Model B Won ({score_b:.2f} vs {score_a:.2f})</span>'
        else:
            badge = f'<span style="background: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;">Tie ({score_a:.2f} vs {score_b:.2f})</span>'

        with st.expander(f"🔹 [{ts}] {model_a} vs {model_b} — {q_snippet}", expanded=False):
            st.markdown(f"**Evaluation ID:** `{eval_id}` | **Judge Model:** `{rec.get('judge_model')}` | **Result:** {badge}", unsafe_allow_html=True)
            st.write("")

            # Prompt & Reference
            st.markdown(f"**Question:**\n> {rec.get('question')}")
            st.markdown(f"**Reference Answer:**\n> {rec.get('reference_answer')}")

            # Score Summary Table
            col_sc_a, col_sc_b = st.columns(2)
            with col_sc_a:
                st.markdown(f"""
                    <div style="background: rgba(59, 130, 246, 0.05); border: 1px solid #BFDBFE; border-radius: 8px; padding: 1rem;">
                        <h4 style="margin: 0; color: #1E40AF;">Model A: {model_a}</h4>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #2563EB;">{score_a:.2f}<span style="font-size: 0.9rem; color: #64748B;">/10</span></div>
                        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #475569;">
                            Acc: <b>{rec.get('accuracy_a', 0):.1f}</b> | Rel: <b>{rec.get('relevance_a', 0):.1f}</b> | Comp: <b>{rec.get('completeness_a', 0):.1f}</b> | Clar: <b>{rec.get('clarity_a', 0):.1f}</b>
                        </p>
                        <div style="font-size: 0.8rem; color: #64748B;">Latency: {rec.get('latency_a', 0):.2f}s | Tokens: {rec.get('tokens_a', 0)}</div>
                    </div>
                """, unsafe_allow_html=True)

            with col_sc_b:
                st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid #A7F3D0; border-radius: 8px; padding: 1rem;">
                        <h4 style="margin: 0; color: #065F46;">Model B: {model_b}</h4>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #059669;">{score_b:.2f}<span style="font-size: 0.9rem; color: #64748B;">/10</span></div>
                        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #475569;">
                            Acc: <b>{rec.get('accuracy_b', 0):.1f}</b> | Rel: <b>{rec.get('relevance_b', 0):.1f}</b> | Comp: <b>{rec.get('completeness_b', 0):.1f}</b> | Clar: <b>{rec.get('clarity_b', 0):.1f}</b>
                        </p>
                        <div style="font-size: 0.8rem; color: #64748B;">Latency: {rec.get('latency_b', 0):.2f}s | Tokens: {rec.get('tokens_b', 0)}</div>
                    </div>
                """, unsafe_allow_html=True)

            # Generated responses
            st.write("")
            tab_a, tab_b = st.tabs([f"Response A ({model_a})", f"Response B ({model_b})"])
            with tab_a:
                st.markdown(rec.get("response_a", ""))
            with tab_b:
                st.markdown(rec.get("response_b", ""))

            # Judge qualitative breakdown
            st.write("")
            st.markdown(f"**Judge Summary:** {rec.get('judge_summary')}")
            
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                st.markdown(f"**Model A Strengths:** {rec.get('strengths_a')}")
                st.markdown(f"**Model A Weaknesses:** {rec.get('weaknesses_a')}")
            with q_col2:
                st.markdown(f"**Model B Strengths:** {rec.get('strengths_b')}")
                st.markdown(f"**Model B Weaknesses:** {rec.get('weaknesses_b')}")

            # Delete button for single record
            st.write("")
            d_col1, d_col2 = st.columns([5, 1])
            with d_col2:
                if st.button("🗑️ Delete", key=f"del_{eval_id}", help="Delete this single evaluation record"):
                    delete_evaluation(eval_id)
                    st.toast(f"Record {eval_id} deleted.")
                    st.rerun()

    # Clear All Records button with confirmation
    st.write("---")
    with st.expander("⚠️ Danger Zone: Clear History"):
        st.warning("This will permanently delete all evaluation records from the SQLite database.")
        if st.button("🚨 Clear All Evaluations", type="secondary"):
            clear_all_evaluations()
            st.success("All evaluation records cleared from database.")
            st.rerun()

