"""Metrics for judging and comparing clusterings."""
from __future__ import annotations

from itertools import combinations
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import (
    adjusted_rand_score, calinski_harabasz_score, completeness_score,
    davies_bouldin_score, homogeneity_score, normalized_mutual_info_score,
    silhouette_score, v_measure_score,
)

from clustering import NOISE, ClusterResult


def internal_metrics(X: np.ndarray, labels: np.ndarray) -> dict:
    """Label-free quality scores. Noise points are excluded (they belong to no cluster);
    the share of excluded points is reported so DBSCAN is not flattered by dropping hard cases."""
    mask = labels != NOISE
    out = {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan,
           "noise_fraction": float(1 - mask.mean())}
    if mask.sum() > 2 and len(set(labels[mask].tolist())) >= 2:
        Xm, lm = X[mask], labels[mask]
        out["silhouette"] = float(silhouette_score(Xm, lm))
        out["davies_bouldin"] = float(davies_bouldin_score(Xm, lm))
        out["calinski_harabasz"] = float(calinski_harabasz_score(Xm, lm))
    return out


def external_metrics(y_true: np.ndarray, labels: np.ndarray) -> dict:
    """Agreement with ground truth. DBSCAN noise (-1) is kept as its own group, so leaving
    points unclustered is penalised rather than hidden."""
    return {
        "ARI": float(adjusted_rand_score(y_true, labels)),
        "NMI": float(normalized_mutual_info_score(y_true, labels)),
        "homogeneity": float(homogeneity_score(y_true, labels)),
        "completeness": float(completeness_score(y_true, labels)),
        "v_measure": float(v_measure_score(y_true, labels)),
    }


def score_table(X: np.ndarray, y_true: np.ndarray | None, results: list[ClusterResult]) -> pd.DataFrame:
    """One row per algorithm: internal + (optional) external metrics, cluster count and fit time."""
    rows = []
    for r in results:
        row = {"algorithm": r.name, "params": ", ".join(f"{k}={v}" for k, v in r.params.items()),
               "clusters": r.n_clusters, "fit_ms": round(r.fit_time * 1000, 1)}
        row.update(internal_metrics(X, r.labels))
        if y_true is not None:
            row.update(external_metrics(y_true, r.labels))
        rows.append(row)
    return pd.DataFrame(rows).set_index("algorithm")


def agreement_matrix(results: list[ClusterResult]) -> pd.DataFrame:
    """Pairwise ARI between the algorithms' labelings: do they even find the same structure?"""
    names = [r.name for r in results]
    m = pd.DataFrame(np.eye(len(results)), index=names, columns=names)
    for a, b in combinations(results, 2):
        v = adjusted_rand_score(a.labels, b.labels)
        m.loc[a.name, b.name] = m.loc[b.name, a.name] = v
    return m


def contingency(y_true: np.ndarray, labels: np.ndarray, class_names=None) -> pd.DataFrame:
    """Rows = true class, columns = discovered cluster (noise shown as 'noise')."""
    ct = pd.crosstab(pd.Series(y_true, name="true"), pd.Series(labels, name="cluster"))
    ct.columns = ["noise" if c == NOISE else f"C{c}" for c in ct.columns]
    if class_names is not None:
        ct.index = [class_names[i] for i in ct.index]
    return ct


def cluster_summary(X, texts, labels, y_true, class_names, tfidf, vocab, max_clusters=12, n_terms=6) -> pd.DataFrame:
    """Describe each discovered cluster: size, majority true class + purity, the terms that make it
    distinctive (cluster mean TF-IDF minus corpus mean) and the headline nearest its centre."""
    labels, y_true = np.asarray(labels), np.asarray(y_true)
    corpus_mean = np.asarray(tfidf.mean(axis=0)).ravel()
    ids = sorted(set(labels.tolist()) - {NOISE}, key=lambda c: -int(np.sum(labels == c)))[:max_clusters]
    if (labels == NOISE).any():
        ids.append(NOISE)
    rows = []
    for c in ids:
        idx = np.where(labels == c)[0]
        maj = int(np.bincount(y_true[idx]).argmax())
        terms = vocab[np.argsort(np.asarray(tfidf[idx].mean(axis=0)).ravel() - corpus_mean)[::-1][:n_terms]]
        nearest = idx[np.argmin(((X[idx] - X[idx].mean(axis=0)) ** 2).sum(axis=1))]
        rows.append({"cluster": "noise" if c == NOISE else f"C{c}", "size": len(idx),
                     "majority class": str(class_names[maj]), "purity": f"{np.mean(y_true[idx] == maj):.0%}",
                     "distinctive terms": ", ".join(terms), "most central headline": texts[nearest][:110]})
    return pd.DataFrame(rows)


def stability(fit: Callable[[int], ClusterResult], seeds=range(5)) -> float:
    """Mean pairwise ARI of the same algorithm re-run with different random seeds.
    1.0 = always the same partition; low = result depends on initialisation."""
    labs = [fit(s).labels for s in seeds]
    return float(np.mean([adjusted_rand_score(a, b) for a, b in combinations(labs, 2)]))
