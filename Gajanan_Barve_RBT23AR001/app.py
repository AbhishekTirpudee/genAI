"""K-Means vs EM (Gaussian mixture) vs DBSCAN - interactive comparison (Gradio Space)."""
from __future__ import annotations

import warnings
from pathlib import Path

import gradio as gr
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

import viz
from clustering import (k_distance, run_dbscan, run_gmm, run_kmeans, suggest_eps, sweep_gmm, sweep_kmeans)
from data import DATA_DIR, SHAPES, NewsData, make_shape, news_available
from metrics import agreement_matrix, cluster_summary, score_table

warnings.filterwarnings("ignore")
HERE = Path(__file__).parent
ALGOS = ["K-Means", "EM (GMM)", "DBSCAN"]
COVS = ["full", "tied", "diag", "spherical"]
SHAPE_TRUE_K = {"blobs": 3, "aniso": 3, "varied": 3, "moons": 2, "circles": 2}

NEWS = NewsData() if news_available() else None
if NEWS is not None:
    RAW = np.load(DATA_DIR / "embeddings_384d.npy")
    TFIDF_V = TfidfVectorizer(stop_words="english", min_df=3, max_df=0.5, sublinear_tf=True)
    TFIDF = TFIDF_V.fit_transform(NEWS.texts)
    VOCAB = np.array(TFIDF_V.get_feature_names_out())
    HOVER = [viz.wrap(t) for t in NEWS.texts]


# --------------------------------------------------------------------------- shared helpers

def _fit_all(X, k, n_comp, cov, eps, ms):
    return [run_kmeans(X, int(k)), run_gmm(X, int(n_comp), cov), run_dbscan(X, float(eps), int(ms))]


def _titles(table: pd.DataFrame, results) -> list[str]:
    out = []
    for r in results:
        row = table.loc[r.name]
        p = ", ".join(f"{a}={b}" for a, b in r.params.items())
        extra = f" · noise {r.noise_fraction:.0%}" if r.name == "DBSCAN" else ""
        out.append(f"{r.name} · {p}<br><sup>{r.n_clusters} clusters{extra} · ARI {row['ARI']:.2f} · silhouette "
                   f"{'n/a' if pd.isna(row['silhouette']) else format(row['silhouette'], '.2f')}</sup>")
    return out


def _display(table: pd.DataFrame) -> pd.DataFrame:
    t = table.reset_index().rename(columns={"noise_fraction": "noise", "davies_bouldin": "Davies-Bouldin",
                                            "calinski_harabasz": "Calinski-Harabasz"})
    t["noise"] = (t["noise"] * 100).round(1).astype(str) + "%"
    cols = ["algorithm", "params", "clusters", "noise", "ARI", "NMI", "v_measure", "silhouette", "Davies-Bouldin", "fit_ms"]
    return t[cols].round(3)


# --------------------------------------------------------------------------- tab 1: shapes

def shapes_defaults(shape, n, seed, ms):
    X, _ = make_shape(shape, int(n), int(seed))
    k = SHAPE_TRUE_K[shape]
    return k, k, round(suggest_eps(X, int(ms)), 2)


def shapes_update(shape, n, seed, k, n_comp, cov, eps, ms):
    X, y = make_shape(shape, int(n), int(seed))
    results = _fit_all(X, k, n_comp, cov, eps, ms)
    table = score_table(X, y, results)
    fig = viz.scatter_panels(X, y, results, _titles(table, results), color_by="cluster",
                             class_names=[f"class {c}" for c in np.unique(y)], ticks=False, point_size=7, height=440)
    kd = k_distance(X, int(ms))
    helpers = (viz.kmeans_sweep_figure(sweep_kmeans(X, range(2, 9)), int(k)),
               viz.gmm_sweep_figure(sweep_gmm(X, range(1, 9), cov), int(n_comp)),
               viz.kdistance_figure(kd, int(ms), float(eps), suggest_eps(X, int(ms))))
    label, blurb = SHAPES[shape]
    note = (f"**{label}.** {blurb}  \nTrue classes: {len(np.unique(y))}. Colours are matched to the true classes "
            "(Hungarian assignment), so *the same colour means the same class in every panel*; grey open circles "
            "are extra clusters beyond the true classes, grey crosses are DBSCAN noise.")
    return (fig, _display(table), *helpers, note)


# --------------------------------------------------------------------------- tab 2: news

def news_suggest_eps(space, ms):
    X = NEWS.X_cluster if space.startswith("UMAP") else RAW
    return round(suggest_eps(X, int(ms)), 2)


def news_update(space, color_by, k, n_comp, cov, eps, ms, inspect_algo):
    umap_space = space.startswith("UMAP")
    X = NEWS.X_cluster if umap_space else RAW
    cov_used = cov if umap_space or cov != "full" else "diag"  # 384-D full covariance is singular/very slow
    results = _fit_all(X, k, n_comp, cov_used, eps, ms)
    table = score_table(X, NEWS.y, results)
    fig = viz.scatter_panels(NEWS.X_plot, NEWS.y, results, _titles(table, results), color_by=color_by,
                             class_names=NEWS.label_names, hover_text=HOVER, ticks=False, point_size=5, height=470)
    r = {x.name: x for x in results}[inspect_algo]
    summary = cluster_summary(X, NEWS.texts, r.labels, NEWS.y, NEWS.label_names, TFIDF, VOCAB)
    status = (f"Clustering runs in **{space}**; the 2-D map is a UMAP projection used only for display."
              + ("" if cov_used == cov else f"  \n⚠️ Full covariance is not usable in 384-D, so EM used `{cov_used}` instead."))
    return (fig, _display(table), viz.agreement_figure(agreement_matrix(results)),
            viz.contingency_figure(NEWS.y, results, NEWS.label_names), summary, status)


# --------------------------------------------------------------------------- tab 3: scorecard

BENCH = pd.read_csv(DATA_DIR / "benchmark.csv") if (DATA_DIR / "benchmark.csv").exists() else None
FINDINGS = (HERE / "findings.md").read_text() if (HERE / "findings.md").exists() else "_Findings not generated yet._"


def score_view(protocol):
    df = BENCH[BENCH.protocol == protocol]
    fig = viz.ari_bars(df, "Adjusted Rand Index vs ground truth (1 = perfect, 0 = chance)")
    cols = ["dataset", "algorithm", "params", "clusters", "noise_fraction", "ARI", "ARI_std", "NMI", "silhouette",
            "stability", "fit_ms"]
    t = df[cols].rename(columns={"noise_fraction": "noise"}).copy()
    t["noise"] = (t["noise"] * 100).round(1).astype(str) + "%"
    return fig, t.round(3)


# --------------------------------------------------------------------------- UI

def build() -> gr.Blocks:
    with gr.Blocks(title="K-Means vs EM vs DBSCAN") as demo:
        gr.Markdown("# K-Means vs EM vs DBSCAN\nThree clustering families, three different assumptions. "
                    "Change the data, change the knobs, and see which assumption breaks.")

        with gr.Tabs():
            # ---------------------------------------------------------------- shapes
            with gr.Tab("1 · Shapes playground"):
                with gr.Row():
                    shape = gr.Dropdown([(v[0], k) for k, v in SHAPES.items()], value="moons", label="Dataset")
                    n_pts = gr.Slider(200, 1500, value=600, step=50, label="Points")
                    seed = gr.Slider(0, 20, value=0, step=1, label="Random draw")
                with gr.Row():
                    k1 = gr.Slider(2, 8, value=2, step=1, label="K-Means · k")
                    nc1 = gr.Slider(1, 8, value=2, step=1, label="EM · components")
                    cov1 = gr.Dropdown(COVS, value="full", label="EM · covariance")
                    eps1 = gr.Slider(0.02, 1.0, value=0.15, step=0.01, label="DBSCAN · eps")
                    ms1 = gr.Slider(2, 30, value=5, step=1, label="DBSCAN · min_samples")
                note1 = gr.Markdown()
                plot1 = gr.Plot(label="Clusterings", show_label=False)
                table1 = gr.Dataframe(label="Scores", interactive=False, wrap=True)
                with gr.Accordion("Parameter helpers: how would you pick k, components and eps without labels?", open=False):
                    with gr.Row():
                        sw_k, sw_g, sw_d = gr.Plot(show_label=False), gr.Plot(show_label=False), gr.Plot(show_label=False)

                ins1 = [shape, n_pts, seed, k1, nc1, cov1, eps1, ms1]
                outs1 = [plot1, table1, sw_k, sw_g, sw_d, note1]
                shape.change(shapes_defaults, [shape, n_pts, seed, ms1], [k1, nc1, eps1]).then(shapes_update, ins1, outs1)
                for c in (n_pts, seed):
                    c.release(shapes_defaults, [shape, n_pts, seed, ms1], [k1, nc1, eps1]).then(shapes_update, ins1, outs1)
                for c in (k1, nc1, eps1, ms1):
                    c.release(shapes_update, ins1, outs1, trigger_mode="always_last")
                cov1.change(shapes_update, ins1, outs1)
                demo.load(shapes_defaults, [shape, n_pts, seed, ms1], [k1, nc1, eps1]).then(shapes_update, ins1, outs1)

            # ---------------------------------------------------------------- news
            if NEWS is not None:
                with gr.Tab("2 · Real data: news embeddings"):
                    gr.Markdown("3,000 AG News headlines (750 each of World, Sports, Business, Sci/Tech) embedded with "
                                "`all-MiniLM-L6-v2`. The true topic labels are used **only** to score the result, never to cluster.")
                    with gr.Row():
                        space = gr.Radio(["UMAP 10-D (recommended)", "Raw 384-D embeddings"], value="UMAP 10-D (recommended)",
                                         label="Space the algorithms run in")
                        color_by = gr.Radio([("Cluster (aligned to true classes)", "cluster"), ("True topic", "truth")],
                                            value="cluster", label="Colour points by")
                    with gr.Row():
                        k2 = gr.Slider(2, 8, value=4, step=1, label="K-Means · k")
                        nc2 = gr.Slider(1, 8, value=4, step=1, label="EM · components")
                        cov2 = gr.Dropdown(COVS, value="full", label="EM · covariance")
                        ms2 = gr.Slider(2, 60, value=20, step=1, label="DBSCAN · min_samples")
                        eps2 = gr.Slider(0.05, 1.6, value=round(suggest_eps(NEWS.X_cluster, 20), 2), step=0.01, label="DBSCAN · eps")
                        sug = gr.Button("Suggest eps (knee)", size="sm")
                    status2 = gr.Markdown()
                    plot2 = gr.Plot(show_label=False)
                    table2 = gr.Dataframe(label="Scores", interactive=False, wrap=True)
                    with gr.Row():
                        agree2, cont2 = gr.Plot(show_label=False), gr.Plot(show_label=False)
                    with gr.Row():
                        inspect = gr.Dropdown(ALGOS, value="K-Means", label="Inspect the clusters of")
                    summ2 = gr.Dataframe(label="What is inside each cluster?", interactive=False, wrap=True)

                    ins2 = [space, color_by, k2, nc2, cov2, eps2, ms2, inspect]
                    outs2 = [plot2, table2, agree2, cont2, summ2, status2]
                    space.change(news_suggest_eps, [space, ms2], [eps2]).then(news_update, ins2, outs2)
                    sug.click(news_suggest_eps, [space, ms2], [eps2]).then(news_update, ins2, outs2)
                    for c in (color_by, cov2, inspect):
                        c.change(news_update, ins2, outs2)
                    for c in (k2, nc2, eps2, ms2):
                        c.release(news_update, ins2, outs2, trigger_mode="always_last")
                    demo.load(news_update, ins2, outs2)

            # ---------------------------------------------------------------- scorecard
            if BENCH is not None:
                with gr.Tab("3 · Scorecard & findings"):
                    proto = gr.Radio([("Auto: no labels used to tune", "auto"), ("Oracle: labels used to tune (upper bound)", "oracle")],
                                     value="auto", label="Tuning protocol")
                    bars, tbl = gr.Plot(show_label=False), gr.Dataframe(label="Full scorecard", interactive=False, wrap=True)
                    proto.change(score_view, proto, [bars, tbl])
                    demo.load(score_view, proto, [bars, tbl])
                    gr.Markdown(FINDINGS)

        gr.Markdown("<sub>Source: scikit-learn `KMeans`, `GaussianMixture` (EM), `DBSCAN`. Metrics: ARI/NMI/V-measure "
                    "(vs ground truth), silhouette/Davies-Bouldin/Calinski-Harabasz (label-free). Chart palette validated for "
                    "colour-vision deficiency; marker shapes and labels carry identity redundantly.</sub>")
    return demo


demo = build()

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
