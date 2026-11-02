"""
Comparison and Visualization module for LLM Evaluation Studio.
Builds interactive Plotly charts, comparison matrices, and visual analytics.
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional


def create_score_comparison_df(
    eval_a: Dict[str, Any],
    eval_b: Dict[str, Any],
    model_a_name: str,
    model_b_name: str
) -> pd.DataFrame:
    """
    Construct a clean comparison DataFrame with per-metric scores, deltas, and indicators.
    """
    metrics = [
        ("Accuracy", "accuracy"),
        ("Relevance", "relevance"),
        ("Completeness", "completeness"),
        ("Clarity", "clarity"),
        ("Overall Score", "overall_score")
    ]

    rows = []
    for label, key in metrics:
        s_a = float(eval_a.get(key, 0.0))
        s_b = float(eval_b.get(key, 0.0))
        delta = round(s_a - s_b, 2)

        if abs(delta) <= 0.15:
            advantage = "🤝 Tie"
        elif delta > 0:
            advantage = f"🏆 Model A (+{delta:.2f})"
        else:
            advantage = f"🏆 Model B (+{abs(delta):.2f})"

        rows.append({
            "Evaluation Metric": label,
            f"Model A ({model_a_name})": f"{s_a:.2f} / 10",
            f"Model B ({model_b_name})": f"{s_b:.2f} / 10",
            "Difference (A - B)": f"{'+' if delta > 0 else ''}{delta:.2f}",
            "Advantage": advantage
        })

    return pd.DataFrame(rows)


def create_bar_chart(
    eval_a: Dict[str, Any],
    eval_b: Dict[str, Any],
    model_a_name: str,
    model_b_name: str
) -> go.Figure:
    """
    Generate an interactive grouped bar chart comparing scores across all rubric dimensions.
    """
    categories = ["Accuracy", "Relevance", "Completeness", "Clarity", "Overall"]
    keys = ["accuracy", "relevance", "completeness", "clarity", "overall_score"]

    scores_a = [float(eval_a.get(k, 0.0)) for k in keys]
    scores_b = [float(eval_b.get(k, 0.0)) for k in keys]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=scores_a,
        name=f"Model A ({model_a_name})",
        marker_color="#3B82F6",  # Indigo / Blue
        text=[f"{v:.1f}" for v in scores_a],
        textposition="auto",
        textfont=dict(size=12, color="white"),
        opacity=0.95
    ))

    fig.add_trace(go.Bar(
        x=categories,
        y=scores_b,
        name=f"Model B ({model_b_name})",
        marker_color="#10B981",  # Emerald / Green
        text=[f"{v:.1f}" for v in scores_b],
        textposition="auto",
        textfont=dict(size=12, color="white"),
        opacity=0.95
    ))

    fig.update_layout(
        title=dict(
            text="<b>Metric-by-Metric Score Comparison</b>",
            font=dict(size=16)
        ),
        barmode="group",
        yaxis=dict(
            title="Score (0 - 10)",
            range=[0, 10.5],
            gridcolor="rgba(150, 150, 150, 0.15)",
            dtick=2
        ),
        xaxis=dict(
            gridcolor="rgba(150, 150, 150, 0.15)"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig


def create_radar_chart(
    eval_a: Dict[str, Any],
    eval_b: Dict[str, Any],
    model_a_name: str,
    model_b_name: str
) -> go.Figure:
    """
    Generate an interactive radar/spider chart comparing the 4 core dimensions.
    """
    categories = ["Accuracy", "Relevance", "Completeness", "Clarity"]
    keys = ["accuracy", "relevance", "completeness", "clarity"]

    # Close the radar loop by repeating first value
    r_a = [float(eval_a.get(k, 0.0)) for k in keys]
    r_a.append(r_a[0])

    r_b = [float(eval_b.get(k, 0.0)) for k in keys]
    r_b.append(r_b[0])

    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=r_a,
        theta=categories_closed,
        fill="toself",
        name=f"Model A ({model_a_name})",
        line=dict(color="#3B82F6", width=2.5),
        fillcolor="rgba(59, 130, 246, 0.25)"
    ))

    fig.add_trace(go.Scatterpolar(
        r=r_b,
        theta=categories_closed,
        fill="toself",
        name=f"Model B ({model_b_name})",
        line=dict(color="#10B981", width=2.5),
        fillcolor="rgba(16, 185, 129, 0.25)"
    ))

    fig.update_layout(
        title=dict(
            text="<b>Rubric Dimensional Radar</b>",
            font=dict(size=16)
        ),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10),
                gridcolor="rgba(150, 150, 150, 0.2)"
            ),
            angularaxis=dict(
                gridcolor="rgba(150, 150, 150, 0.2)"
            )
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=360,
        paper_bgcolor="rgba(0,0,0,0)"
    )

    return fig


def create_history_trend_chart(evaluations: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Generate a historical score trend timeline for past evaluations.
    """
    if not evaluations:
        return None

    # Take chronologically ordered records
    sorted_evals = sorted(evaluations, key=lambda x: x.get("timestamp", ""))

    timestamps = [e.get("timestamp", "")[:16] for e in sorted_evals]
    scores_a = [float(e.get("overall_a", 0.0)) for e in sorted_evals]
    scores_b = [float(e.get("overall_b", 0.0)) for e in sorted_evals]
    labels_a = [f"Model A ({e.get('model_a')})" for e in sorted_evals]
    labels_b = [f"Model B ({e.get('model_b')})" for e in sorted_evals]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=scores_a,
        mode="lines+markers",
        name="Model A Score",
        line=dict(color="#3B82F6", width=2.5),
        marker=dict(size=8, symbol="circle"),
        hovertext=labels_a
    ))

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=scores_b,
        mode="lines+markers",
        name="Model B Score",
        line=dict(color="#10B981", width=2.5),
        marker=dict(size=8, symbol="diamond"),
        hovertext=labels_b
    ))

    fig.update_layout(
        title=dict(text="<b>Historical Evaluation Score Progression</b>", font=dict(size=16)),
        xaxis=dict(title="Evaluation Date & Time", gridcolor="rgba(150, 150, 150, 0.15)"),
        yaxis=dict(title="Overall Score (0 - 10)", range=[0, 10.5], gridcolor="rgba(150, 150, 150, 0.15)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig


def create_win_distribution_chart(winner_counts: Dict[str, int]) -> go.Figure:
    """
    Generate an interactive Donut chart showing win rates between models.
    """
    labels = list(winner_counts.keys())
    values = list(winner_counts.values())

    colors = {
        "Model A": "#3B82F6",
        "Model B": "#10B981",
        "Tie": "#F59E0B"
    }
    color_seq = [colors.get(l, "#6B7280") for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=color_seq),
        textinfo="label+percent",
        textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>Wins: %{value}<br>Proportion: %{percent}<extra></extra>"
    )])

    fig.update_layout(
        title=dict(text="<b>Model Win Distribution</b>", font=dict(size=16)),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=30),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)"
    )

    return fig

