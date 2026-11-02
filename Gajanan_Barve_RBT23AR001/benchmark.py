"""Scorecard: all three algorithms on every dataset, under two honest tuning protocols.

  auto    uses NO labels: K-Means k = best silhouette (2-8), EM components = lowest BIC (1-8),
          DBSCAN eps = knee of the k-distance curve, min_samples = clip(2*dim, 5, 20).
  oracle  USES the labels to tune (k = true #classes; DBSCAN eps/min_samples = best ARI on a grid).
          This is an upper bound on what tuning can buy, not something you can do on unlabelled data.

Shapes are averaged over several random draws; the news data is one fixed sample.
    python benchmark.py   ->   data/benchmark.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from clustering import (ClusterResult, k_distance, run_dbscan, run_gmm, run_kmeans, suggest_eps,
                        sweep_gmm, sweep_kmeans)
from data import DATA_DIR, SHAPES, NewsData, make_shape, news_available
from metrics import score_table, stability

N_SHAPE_SEEDS = 5
MS_GRID = (5, 10, 20)


def _oracle_dbscan(X, y) -> tuple[float, int]:
    best = (-2.0, 0.0, 5)
    for ms in MS_GRID:
        for eps in np.unique(np.quantile(k_distance(X, ms), np.linspace(0.3, 0.99, 25))):
            if eps <= 0:
                continue
            a = adjusted_rand_score(y, run_dbscan(X, eps, ms).labels)
            if a > best[0]:
                best = (a, float(eps), ms)
    return best[1], best[2]


def evaluate(X: np.ndarray, y: np.ndarray, dim: int, covariance: str = "full") -> pd.DataFrame:
    """Return one row per (protocol, algorithm) for a single dataset."""
    k_true = len(np.unique(y))
    ms_auto = min(max(5, 2 * dim), 20)  # 2*dim rule of thumb, capped: 2*384 = 768 neighbours is degenerate

    sk = sweep_kmeans(X, range(2, 9))
    k_auto = sk["k"][int(np.nanargmax(sk["silhouette"]))]
    sg = sweep_gmm(X, range(1, 9), covariance)
    n_auto = sg["components"][int(np.argmin(sg["bic"]))]
    eps_o, ms_o = _oracle_dbscan(X, y)

    plans = {
        "auto": [("k", k_auto), ("n", n_auto), (suggest_eps(X, ms_auto), ms_auto)],
        "oracle": [("k", k_true), ("n", k_true), (eps_o, ms_o)],
    }
    frames = []
    for protocol, (km, gm, db) in plans.items():
        results: list[ClusterResult] = [run_kmeans(X, km[1]), run_gmm(X, gm[1], covariance), run_dbscan(X, db[0], db[1])]
        t = score_table(X, y, results)
        t["stability"] = [stability(lambda s, r=r: (run_kmeans(X, r.params["k"], s) if r.name == "K-Means"
                                                    else run_gmm(X, r.params["components"], covariance, s)))
                          if r.name != "DBSCAN" else 1.0 for r in results]
        t.insert(0, "protocol", protocol)
        frames.append(t.reset_index())
    return pd.concat(frames, ignore_index=True)


def run_benchmark() -> pd.DataFrame:
    parts = []
    for name, (label, _) in SHAPES.items():
        runs = []
        for seed in range(N_SHAPE_SEEDS):
            X, y = make_shape(name, seed=seed)
            r = evaluate(X, y, dim=2)
            r["seed"] = seed
            runs.append(r)
        allr = pd.concat(runs)
        parts.append(_aggregate(allr, label))
    if news_available():
        d = NewsData()
        parts.append(_aggregate(evaluate(d.X_cluster, d.y, dim=d.X_cluster.shape[1]).assign(seed=0), "News · UMAP 10-D"))
        raw = np.load(DATA_DIR / "embeddings_384d.npy")
        parts.append(_aggregate(evaluate(raw, d.y, dim=raw.shape[1], covariance="diag").assign(seed=0), "News · raw 384-D"))
    return pd.concat(parts, ignore_index=True)


def _aggregate(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    keys = ["protocol", "algorithm"]
    num = ["clusters", "fit_ms", "silhouette", "davies_bouldin", "calinski_harabasz", "noise_fraction",
           "ARI", "NMI", "homogeneity", "completeness", "v_measure", "stability"]
    g = df.groupby(keys, sort=False)
    out = g[num].mean(numeric_only=True)
    out["ARI_std"] = g["ARI"].std(ddof=0)
    out["params"] = g["params"].first()  # parameters from the first draw, for illustration
    out = out.reset_index()
    out.insert(0, "dataset", dataset)
    out["clusters"] = out["clusters"].round(1)
    return out


if __name__ == "__main__":
    df = run_benchmark()
    df.to_csv(DATA_DIR / "benchmark.csv", index=False)
    pd.set_option("display.width", 200, "display.max_columns", 30)
    for proto in ("auto", "oracle"):
        print(f"\n=== {proto} ===")
        print(df[df.protocol == proto].pivot(index="dataset", columns="algorithm", values="ARI").round(3)
              .reindex([v[0] for v in SHAPES.values()] + ["News · UMAP 10-D", "News · raw 384-D"]))
    print("\nsaved", DATA_DIR / "benchmark.csv")
