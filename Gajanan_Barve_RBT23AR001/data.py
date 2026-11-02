"""Datasets for the clustering comparison.

Two families:
  * synthetic 2-D "shapes" whose geometry exposes each algorithm's assumptions
  * a real text dataset (AG News) that is embedded offline by ``precompute.py``
    and loaded here from the shipped ``data/`` folder.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs, make_circles, make_moons
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path(__file__).parent / "data"

# name -> (label shown in the UI, one-line description of what it tests)
SHAPES = {
    "blobs": ("Spherical blobs", "Equal-size round clusters: the home turf of K-Means."),
    "aniso": ("Anisotropic blobs", "Stretched/rotated elliptical clusters: needs covariance (EM)."),
    "varied": ("Varied density", "Blobs with different spreads: a test of one global eps / one shared variance. "
                                 "At this moderate contrast all three cope; push 'Random draw' to see how stable that is."),
    "moons": ("Two moons", "Non-convex interleaved crescents: needs density connectivity."),
    "circles": ("Concentric circles", "A ring around a ring: no centroid can separate them."),
}


_CENTERS = np.array([[-5.0, -3.0], [0.0, 5.0], [6.0, -2.0]])


def make_shape(name: str, n: int = 600, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Return a standardised 2-D dataset ``X`` and its ground-truth labels ``y``."""
    # Fixed centres (not random) so the blob-based sets are not accidentally overlapping:
    # an unlucky random draw puts the ceiling for *any* algorithm below ARI 0.9.
    if name == "blobs":
        X, y = make_blobs(n_samples=n, centers=_CENTERS, cluster_std=0.9, random_state=seed)
    elif name == "aniso":
        X, y = make_blobs(n_samples=n, centers=_CENTERS, cluster_std=0.8, random_state=seed)
        X = X @ np.array([[0.6, -0.64], [-0.4, 0.85]])
    elif name == "varied":
        X, y = make_blobs(
            n_samples=n, centers=_CENTERS, cluster_std=[0.5, 1.8, 0.9], random_state=seed
        )
    elif name == "moons":
        X, y = make_moons(n_samples=n, noise=0.07, random_state=seed)
    elif name == "circles":
        X, y = make_circles(n_samples=n, noise=0.05, factor=0.5, random_state=seed)
    else:
        raise ValueError(f"unknown shape {name!r}; choose from {list(SHAPES)}")
    return StandardScaler().fit_transform(X), y


def clean_text(t: str) -> str:
    """Strip AG News' HTML debris (``#39;``, ``&lt;b&gt;``, ``lt;``) for display and TF-IDF only.
    The embeddings were computed on the raw text, so clustering is unaffected."""
    t = html.unescape(t)
    t = re.sub(r"\s?#(\d{2,3});", lambda m: chr(int(m.group(1))), t)  # "Can #39;t" -> "Can't"
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\b(?:lt|gt|quot|amp);", " ", t)
    return re.sub(r"\s+", " ", t).strip()


class NewsData:
    """Precomputed AG News embeddings (see ``precompute.py``)."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.meta = pd.read_parquet(data_dir / "meta.parquet")
        self.meta["text"] = self.meta["text"].map(clean_text)
        self.X_cluster = np.load(data_dir / "umap_10d.npy")  # space the algorithms run in
        self.X_plot = np.load(data_dir / "umap_2d.npy")      # space used only for display
        self.y = self.meta["label"].to_numpy()
        self.label_names = list(
            self.meta.drop_duplicates("label").sort_values("label")["label_name"]
        )
        self.texts = self.meta["text"].tolist()


def news_available(data_dir: Path = DATA_DIR) -> bool:
    return all((data_dir / f).exists() for f in ("meta.parquet", "umap_10d.npy", "umap_2d.npy"))
