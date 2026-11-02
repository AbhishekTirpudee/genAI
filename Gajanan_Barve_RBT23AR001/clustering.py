"""Thin, uniform wrappers around K-Means, EM (Gaussian mixture) and DBSCAN."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import NearestNeighbors

NOISE = -1  # DBSCAN's label for points that belong to no cluster


@dataclass
class ClusterResult:
    name: str
    labels: np.ndarray
    fit_time: float
    params: dict
    confidence: np.ndarray | None = None  # EM only: max posterior probability per point
    centers: np.ndarray | None = None     # K-Means / EM component means
    extra: dict = field(default_factory=dict)

    @property
    def n_clusters(self) -> int:
        return len(set(self.labels.tolist()) - {NOISE})

    @property
    def noise_fraction(self) -> float:
        return float(np.mean(self.labels == NOISE))


def run_kmeans(X: np.ndarray, k: int, seed: int = 0) -> ClusterResult:
    t = time.perf_counter()
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=seed).fit(X)
    return ClusterResult(
        "K-Means", km.labels_, time.perf_counter() - t, {"k": k},
        centers=km.cluster_centers_, extra={"inertia": float(km.inertia_), "n_iter": int(km.n_iter_)},
    )


def run_gmm(X: np.ndarray, n_components: int, covariance_type: str = "full", seed: int = 0) -> ClusterResult:
    """EM for a Gaussian mixture. Hard labels = argmax posterior; confidence = max posterior."""
    t = time.perf_counter()
    gm = GaussianMixture(
        n_components=n_components, covariance_type=covariance_type, n_init=5,
        random_state=seed, reg_covar=1e-5,
    ).fit(X)
    post = gm.predict_proba(X)
    return ClusterResult(
        "EM (GMM)", post.argmax(axis=1), time.perf_counter() - t,
        {"components": n_components, "covariance": covariance_type},
        confidence=post.max(axis=1), centers=gm.means_,
        extra={"bic": float(gm.bic(X)), "aic": float(gm.aic(X)), "converged": bool(gm.converged_),
               "n_iter": int(gm.n_iter_)},
    )


def run_dbscan(X: np.ndarray, eps: float, min_samples: int) -> ClusterResult:
    t = time.perf_counter()
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    return ClusterResult(
        "DBSCAN", db.labels_, time.perf_counter() - t,
        {"eps": round(float(eps), 4), "min_samples": min_samples},
    )


# ---------------------------------------------------------------- model selection

def k_distance(X: np.ndarray, k: int) -> np.ndarray:
    """Sorted distance of every point to its k-th nearest neighbour (for the eps 'knee')."""
    nn = NearestNeighbors(n_neighbors=k + 1).fit(X)  # +1: each point is its own neighbour
    d, _ = nn.kneighbors(X)
    return np.sort(d[:, -1])


def suggest_eps(X: np.ndarray, min_samples: int) -> float:
    """Knee of the k-distance curve = point farthest from the chord joining its endpoints."""
    d = k_distance(X, min_samples)
    n = len(d)
    x = np.linspace(0, 1, n)
    y = (d - d[0]) / max(d[-1] - d[0], 1e-12)
    return float(d[np.argmax(x - y)])  # curve lies below the chord; max gap = knee


def sweep_kmeans(X: np.ndarray, ks, seed: int = 0) -> dict:
    inertia, sil = [], []
    for k in ks:
        r = run_kmeans(X, k, seed)
        inertia.append(r.extra["inertia"])
        sil.append(silhouette_score(X, r.labels) if k > 1 else np.nan)
    return {"k": list(ks), "inertia": inertia, "silhouette": sil}


def sweep_gmm(X: np.ndarray, ns, covariance_type: str = "full", seed: int = 0) -> dict:
    bic, aic = [], []
    for n in ns:
        r = run_gmm(X, n, covariance_type, seed)
        bic.append(r.extra["bic"])
        aic.append(r.extra["aic"])
    return {"components": list(ns), "bic": bic, "aic": aic}
