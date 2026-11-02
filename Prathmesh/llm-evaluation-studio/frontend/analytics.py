"""
Analytics Page for LLM Evaluation Studio.
Presents aggregate performance metrics, model win rates, dimensional radars, and trade-off charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from backend.database import get_analytics_summary, get_all_evaluations
from backend.comparison import create_win_distribution_chart, create_history_trend_chart


def render_analytics_page():
    """Render the aggregate statistical intelligence dashboard."""
    st.markdown("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <h2 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1E293B;">
                📈 Evaluation Analytics & Benchmarks
            </h2>
            <p style="margin: 0.2rem 0 1rem 0; color: #64748B;">
                Aggregate cross-model intelligence, win rates, dimensional radars, and latency-accuracy trade-offs.
            </p>
        </div>
    """, unsafe_allow_html=True)

    stats = get_analytics_summary()
    total_evals = stats["total_evaluations"]

    if total_evals == 0:
        st.info("No evaluation data available yet. Run a few evaluations or seed sample data in Settings to view analytics.")
        return

    # Top KPI Metrics Row
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        st.metric("Total Evaluations", total_evals)
    with m_col2:
        st.metric("Avg Accuracy", f"{stats['avg_accuracy']:.2f}/10")
    with m_col3:
        st.metric("Avg Relevance", f"{stats['avg_relevance']:.2f}/10")
    with m_col4:
        st.metric("Avg Completeness", f"{stats['avg_completeness']:.2f}/10")
    with m_col5:
        st.metric("Avg Clarity", f"{stats['avg_clarity']:.2f}/10")

    st.write("---")

    # Visualizations Row 1: Win Distribution Donut & Model Average Score Ranking
    c_col1, c_col2 = st.columns(2)

    with c_col1:
        fig_win = create_win_distribution_chart(stats["winner_counts"])
        st.plotly_chart(fig_win, use_container_width=True)

    with c_col2:
        # Model average score ranking
        model_stats = stats.get("model_stats", {})
        if model_stats:
            m_names = list(model_stats.keys())
            m_scores = [model_stats[m]["avg_score"] for m in m_names]
            m_wins = [model_stats[m]["wins"] for m in m_names]
            m_apps = [model_stats[m]["appearances"] for m in m_names]

            fig_ranking = go.Figure(data=[
                go.Bar(
                    x=m_scores,
                    y=m_names,
                    orientation="h",
                    marker=dict(color="#3B82F6"),
                    text=[f"{s:.2f} (n={a})" for s, a in zip(m_scores, m_apps)],
                    textposition="auto"
                )
            ])
            fig_ranking.update_layout(
                title=dict(text="<b>Average Score by Model</b>", font=dict(size=16)),
                xaxis=dict(title="Average Score (0-10)", range=[0, 10.5]),
                yaxis=dict(title=""),
                margin=dict(l=40, r=20, t=50, b=30),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_ranking, use_container_width=True)

    # Detailed Model Performance Table
    st.write("---")
    st.markdown("### 🏆 Model Leaderboard & Win Percentages")
    if model_stats:
        leaderboard_rows = []
        for m, mdata in sorted(model_stats.items(), key=lambda x: x[1]["avg_score"], reverse=True):
            leaderboard_rows.append({
                "Model Identifier": m,
                "Evaluations Participated": mdata.get("appearances", 0),
                "Total Wins": mdata.get("wins", 0),
                "Win Rate (%)": f"{mdata.get('win_rate', 0.0):.1f}%",
                "Average Score": f"{mdata.get('avg_score', 0.0):.2f} / 10"
            })
        df_lb = pd.DataFrame(leaderboard_rows)
        st.dataframe(df_lb, use_container_width=True, hide_index=True)

    # Latency vs Quality Trade-off & Score Trend
    st.write("---")
    st.markdown("### ⚡ Latency vs Score Quality Trade-off")

    all_evals = get_all_evaluations(limit=100)
    if all_evals:
        scatter_points = []
        for e in all_evals:
            scatter_points.append({
                "Model": e.get("model_a"),
                "Latency (s)": e.get("latency_a", 0.0),
                "Overall Score": e.get("overall_a", 0.0),
                "Evaluation": f"ID: {e.get('id')}"
            })
            scatter_points.append({
                "Model": e.get("model_b"),
                "Latency (s)": e.get("latency_b", 0.0),
                "Overall Score": e.get("overall_b", 0.0),
                "Evaluation": f"ID: {e.get('id')}"
            })

        df_scatter = pd.DataFrame(scatter_points)
        fig_scatter = px.scatter(
            df_scatter,
            x="Latency (s)",
            y="Overall Score",
            color="Model",
            hover_data=["Evaluation"],
            title="<b>Generation Latency vs Overall Evaluation Score</b>"
        )
        fig_scatter.update_layout(
            yaxis=dict(range=[0, 10.5]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Historical score trend
    st.write("---")
    st.markdown("### 📉 Chronological Evaluation Score Progression")
    trend_chart = create_history_trend_chart(all_evals)
    if trend_chart:
        st.plotly_chart(trend_chart, use_container_width=True)

