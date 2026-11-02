"""Plotly figures shared by the Space and the notebook.

Colour decisions (checked with the dataviz skill's ``validate_palette.js --pairs all``):
  * Scatter marks may touch any other mark, so the all-pairs test applies. Of the 70 possible
    4-colour subsets of the documented categorical palette only two pass in both light and dark
    mode; blue / yellow / magenta / green is used here. No 5-colour set passes, so a figure shows
    at most four colour-coded groups and folds every further cluster into a grey "other" group.
  * Light-mode contrast of yellow (2.1:1) and magenta (2.6:1) is below 3:1, and dark-mode
    green/yellow sit in the CVD warning band. Relief channels shipped: a distinct marker *shape*
    per group, direct labels on each group, a legend, and score tables next to every chart.
  * Noise (DBSCAN label -1) is never a category colour: it is a muted grey cross.
  * Charts carry their own fixed light surface so the validated colours always sit on the surface
    they were validated against, whatever theme the page uses.
"""
from __future__ import annotations

import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import linear_sum_assignment

from clustering import NOISE, ClusterResult

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = ["#2a78d6", "#eda100", "#e87ba4", "#008300"]          # blue, yellow, magenta, green
SYMBOLS = ["circle", "square", "diamond", "triangle-up"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # blue 100..700
FONT = dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=INK2, size=12)
OTHER, NOISE_G, N_SLOTS = 4, 5, 4  # group ids: 0..3 colour slots, 4 = other clusters, 5 = noise


# ----------------------------------------------------------------------------- grouping

def assign_groups(labels, y_true, color_by: str, class_names) -> tuple[np.ndarray, dict]:
    """Map each point to a display group.

    ``color_by="truth"``   : group = true class (first four classes; more are folded into 'other').
    ``color_by="cluster"`` : each cluster is matched one-to-one to a true class with the Hungarian
        algorithm, so *the same colour means the same class in every panel* and disagreement is
        visible at a glance. Unmatched clusters fold into 'other clusters'; DBSCAN noise stays noise.
    """
    labels = np.asarray(labels)
    y_true = np.asarray(y_true)
    classes = list(np.unique(y_true))
    names = {i: str(class_names[c]) for i, c in enumerate(classes[:N_SLOTS])}
    names[OTHER] = "other clusters" if color_by == "cluster" else "other classes"
    names[NOISE_G] = "noise"
    if color_by == "truth":
        slot = {c: i for i, c in enumerate(classes[:N_SLOTS])}
        return np.array([slot.get(c, OTHER) for c in y_true]), names

    names = {i: f"≈ {n}" for i, n in names.items() if i < N_SLOTS} | {OTHER: names[OTHER], NOISE_G: "noise"}
    clusters = [c for c in np.unique(labels) if c != NOISE]
    group_of = {c: OTHER for c in clusters}
    if clusters:
        cmat = np.array([[np.sum((y_true == k) & (labels == c)) for c in clusters] for k in classes[:N_SLOTS]])
        rows, cols = linear_sum_assignment(-cmat)
        for r, c in zip(rows, cols):
            if cmat[r, c] > 0:
                group_of[clusters[c]] = r
    return np.array([NOISE_G if l == NOISE else group_of[l] for l in labels]), names


def _style(g: int) -> dict:
    if g < N_SLOTS:
        return dict(symbol=SYMBOLS[g], color=SERIES[g], opacity=0.8, line=dict(width=0.5, color=SURFACE))
    if g == OTHER:
        return dict(symbol="circle-open", color=MUTED, opacity=0.85, line=dict(width=1.3, color=MUTED))
    return dict(symbol="x", color=MUTED, opacity=0.7, line=dict(width=1.3, color=MUTED))


def _axes(fig, ticks: bool):
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, linecolor=AXIS, showticklabels=ticks, ticks="")
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, linecolor=AXIS, showticklabels=ticks, ticks="")


def _base(fig, height, **kw):
    fig.update_layout(paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font=FONT, height=height,
                      margin=dict(l=40, r=20, t=70, b=20), hoverlabel=dict(bgcolor=SURFACE, font=dict(color=INK)), **kw)


# ----------------------------------------------------------------------------- scatter

def wrap(text: str, width: int = 55, lines: int = 3) -> str:
    return "<br>".join(textwrap.wrap(str(text), width)[:lines])


def scatter_panels(X2, y_true, results: list[ClusterResult], titles: list[str], color_by="cluster",
                   class_names=None, hover_text=None, ticks=True, point_size=6, height=470) -> go.Figure:
    """Side-by-side scatter, one panel per algorithm, shared (zoom-synchronised) axes, one legend."""
    X2 = np.asarray(X2)
    class_names = class_names if class_names is not None else [f"class {c}" for c in np.unique(y_true)]
    n = len(results)
    fig = make_subplots(rows=1, cols=n, subplot_titles=titles, shared_xaxes=True, shared_yaxes=True,
                        horizontal_spacing=0.02)
    fig.update_annotations(font=dict(size=13, color=INK))  # panel titles only (labels are added below)
    per_panel = [assign_groups(r.labels, y_true, color_by, class_names) for r in results]
    names = per_panel[0][1]
    present = sorted(set().union(*[set(np.unique(g).tolist()) for g, _ in per_panel]))

    for p, (r, (g, _)) in enumerate(zip(results, per_panel), start=1):
        for gi in present:
            m = g == gi
            if not m.any() and p > 1:
                continue
            label = names[gi]
            if hover_text is not None:
                text = [f"<b>{label}</b> · cluster {'noise' if l == NOISE else l}<br>{hover_text[i]}"
                        for i, l in zip(np.where(m)[0], r.labels[m])]
            else:
                text = [f"<b>{label}</b> · cluster {'noise' if l == NOISE else l}" for l in r.labels[m]]
            fig.add_trace(go.Scatter(
                x=X2[m, 0], y=X2[m, 1], mode="markers", name=label, legendgroup=label,
                showlegend=(p == 1), text=text, hovertemplate="%{text}<extra></extra>",
                marker=dict(size=point_size, **_style(gi)),
            ), row=1, col=p)
        for gi in present:  # direct label at the median of each colour-coded group
            m = g == gi
            if gi < N_SLOTS and m.sum() >= 8:
                fig.add_annotation(x=float(np.median(X2[m, 0])), y=float(np.median(X2[m, 1])), text=f"<b>{names[gi]}</b>",
                                   showarrow=False, font=dict(size=10, color=INK), bgcolor="rgba(252,252,251,0.82)",
                                   borderpad=1, row=1, col=p)
    _axes(fig, ticks)
    _base(fig, height, legend=dict(orientation="h", y=-0.04, x=0.5, xanchor="center", yanchor="top",
                                   itemsizing="constant", font=dict(size=12, color=INK2)))
    return fig


# ----------------------------------------------------------------------------- heatmaps

def agreement_figure(m: pd.DataFrame, height=360) -> go.Figure:
    """Pairwise ARI between algorithms' labelings (1 = identical partitions, 0 = chance)."""
    fig = go.Figure(go.Heatmap(
        z=m.values.clip(0, 1), x=list(m.columns), y=list(m.index), zmin=0, zmax=1, colorscale=_scale(),
        text=np.round(m.values, 2), texttemplate="%{text}", textfont=dict(size=13),
        hovertemplate="%{y} vs %{x}<br>ARI %{text}<extra></extra>", colorbar=dict(title="ARI", thickness=10, len=0.8),
        xgap=2, ygap=2))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False)
    _base(fig, height, title=dict(text="Do the algorithms agree with each other? (pairwise ARI)", font=dict(size=13, color=INK), x=0.01))
    fig.update_layout(margin=dict(l=90, r=20, t=50, b=40))
    return fig


def _scale():
    return [[i / (len(SEQ) - 1), c] for i, c in enumerate(SEQ)]


def contingency_figure(y_true, results: list[ClusterResult], class_names, max_cols=8, height=360) -> go.Figure:
    """True class (rows) × discovered cluster (columns). Colour = share of the class; text = count."""
    n = len(results)
    fig = make_subplots(rows=1, cols=n, subplot_titles=[r.name for r in results], horizontal_spacing=0.07)
    fig.update_annotations(font=dict(size=13, color=INK))
    rows = [str(class_names[c]) for c in np.unique(y_true)]
    for p, r in enumerate(results, start=1):
        ct = pd.crosstab(pd.Series(y_true), pd.Series(r.labels))
        order = ct.drop(columns=[NOISE], errors="ignore").sum().sort_values(ascending=False).index.tolist()
        keep, rest = order[:max_cols], order[max_cols:]
        cols, heads = [], []
        if NOISE in ct.columns:
            cols.append(ct[NOISE]); heads.append("noise")
        for c in keep:
            cols.append(ct[c]); heads.append(f"C{c}")
        if rest:
            cols.append(ct[rest].sum(axis=1)); heads.append(f"+{len(rest)} more")
        counts = np.column_stack([c.to_numpy() for c in cols])
        share = counts / counts.sum(axis=1, keepdims=True).clip(1)
        fig.add_trace(go.Heatmap(
            z=share, x=heads, y=rows, zmin=0, zmax=1, colorscale=_scale(), showscale=(p == n),
            text=counts, texttemplate="%{text}", textfont=dict(size=11), xgap=2, ygap=2,
            hovertemplate="class %{y} → %{x}<br>%{text} items (%{z:.0%} of class)<extra></extra>",
            colorbar=dict(title="share of class", thickness=10, len=0.8)), row=1, col=p)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, tickangle=-45)
    _base(fig, height)
    fig.update_layout(margin=dict(l=70, r=20, t=50, b=70))
    return fig


# ----------------------------------------------------------------------------- model-selection helpers

def _line(fig, x, y, name, color, row=None, col=None, dash=None):
    trace = go.Scatter(x=x, y=y, mode="lines+markers", name=name, line=dict(color=color, width=2, dash=dash),
                       marker=dict(size=8, color=color, line=dict(width=2, color=SURFACE)),
                       hovertemplate=f"{name}<br>%{{x}} → %{{y:.3f}}<extra></extra>")
    if row is None:  # plain go.Figure() has no subplot grid to address
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)


def kmeans_sweep_figure(sw: dict, k_now: int | None = None, height=300) -> go.Figure:
    """Elbow (inertia) and silhouette as two separate panels - never a dual axis."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Inertia (look for the elbow)", "Silhouette (higher is better)"])
    fig.update_annotations(font=dict(size=12, color=INK))
    _line(fig, sw["k"], sw["inertia"], "inertia", SERIES[0], row=1, col=1)
    _line(fig, sw["k"], sw["silhouette"], "silhouette", SERIES[0], row=1, col=2)
    if k_now:
        for c in (1, 2):
            fig.add_vline(x=k_now, line=dict(color=MUTED, width=1, dash="dot"), row=1, col=c)
    fig.update_xaxes(title_text="k", dtick=1)
    _axes(fig, True); fig.update_xaxes(title_text="k", dtick=1, ticks="")
    _base(fig, height, showlegend=False)
    fig.update_layout(margin=dict(l=50, r=20, t=50, b=40))
    return fig


def gmm_sweep_figure(sw: dict, n_now: int | None = None, height=300) -> go.Figure:
    fig = go.Figure()
    _line(fig, sw["components"], sw["bic"], "BIC", SERIES[0])
    _line(fig, sw["components"], sw["aic"], "AIC", SERIES[1], dash="dash")
    if n_now:
        fig.add_vline(x=n_now, line=dict(color=MUTED, width=1, dash="dot"))
    _axes(fig, True)
    fig.update_xaxes(title_text="components", dtick=1, ticks="")
    _base(fig, height, title=dict(text="Information criteria (lower is better)", font=dict(size=12, color=INK), x=0.01),
          legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"))
    fig.update_layout(margin=dict(l=60, r=20, t=50, b=40))
    return fig


def kdistance_figure(d: np.ndarray, k: int, eps: float, eps_suggested: float, height=300) -> go.Figure:
    fig = go.Figure()
    _line(fig, np.arange(len(d)), d, f"{k}-NN distance", SERIES[0])
    fig.data[0].update(mode="lines", hovertemplate="rank %{x}<br>distance %{y:.3f}<extra></extra>")
    fig.add_hline(y=eps, line=dict(color=INK2, width=1.5), annotation_text=f"eps = {eps:.2f}",
                  annotation_position="top left", annotation_font=dict(size=11, color=INK))
    fig.add_hline(y=eps_suggested, line=dict(color=MUTED, width=1, dash="dot"), annotation_text=f"knee ≈ {eps_suggested:.2f}",
                  annotation_position="bottom right", annotation_font=dict(size=11, color=INK2))
    _axes(fig, True)
    fig.update_xaxes(title_text="points, sorted by distance", ticks=""); fig.update_yaxes(title_text=f"distance to {k}-th neighbour")
    _base(fig, height, showlegend=False,
          title=dict(text="k-distance plot: pick eps near the knee", font=dict(size=12, color=INK), x=0.01))
    fig.update_layout(margin=dict(l=60, r=20, t=50, b=40))
    return fig


def ari_bars(df: pd.DataFrame, title: str, height=340) -> go.Figure:
    """Grouped bars: ARI per dataset (x) per algorithm (series). Values are printed on the bars."""
    fig = go.Figure()
    algos = list(dict.fromkeys(df["algorithm"]))
    for i, a in enumerate(algos):
        s = df[df["algorithm"] == a]
        fig.add_trace(go.Bar(x=s["dataset"], y=s["ARI"], name=a, marker=dict(color=SERIES[i], line=dict(width=2, color=SURFACE)),
                             text=[f"{v:.2f}" for v in s["ARI"]], textposition="outside", textfont=dict(size=11, color=INK2),
                             hovertemplate=f"{a}<br>%{{x}}<br>ARI %{{y:.3f}}<extra></extra>"))
    _axes(fig, True)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(range=[0, 1.12], title_text="Adjusted Rand Index")
    _base(fig, height, barmode="group", bargap=0.25, title=dict(text=title, font=dict(size=13, color=INK), x=0.01),
          legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"))
    fig.update_layout(margin=dict(l=60, r=20, t=60, b=40))
    return fig
