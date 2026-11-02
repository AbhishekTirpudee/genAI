"""Offline step: AG News -> sentence embeddings -> UMAP (10-D for clustering, 2-D for display).

Run once; the outputs in ``data/`` ship with the Space so it never needs to run a model.

    python precompute.py [--per-class 750] [--seed 0]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "data"
DATASETS = ["fancyzhx/ag_news", "ag_news"]  # Hub id moved from the bare name to the org
LABELS = ["World", "Sports", "Business", "Sci/Tech"]  # AG News class ids 0..3
MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_balanced(per_class: int, seed: int) -> pd.DataFrame:
    from datasets import load_dataset

    last = None
    for repo in DATASETS:
        try:
            df = load_dataset(repo, split="train").to_pandas()
            print(f"loaded {repo}: {len(df):,} rows")
            break
        except Exception as e:  # noqa: BLE001 - try the next candidate id
            last = e
    else:
        raise RuntimeError(f"could not load any of {DATASETS}") from last
    # explicit per-class sampling (pandas >= 3 drops the grouping column inside groupby.apply)
    df = (pd.concat([df[df["label"] == c].sample(per_class, random_state=seed)
                     for c in sorted(df["label"].unique())])
            .sample(frac=1, random_state=seed).reset_index(drop=True))
    df["label_name"] = df["label"].map(dict(enumerate(LABELS)))
    return df[["text", "label", "label_name"]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=750)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    import umap
    from sentence_transformers import SentenceTransformer

    OUT.mkdir(exist_ok=True)
    df = load_balanced(a.per_class, a.seed)

    model = SentenceTransformer(MODEL)
    emb = model.encode(df["text"].tolist(), batch_size=64, show_progress_bar=True,
                       normalize_embeddings=True)
    print("embeddings:", emb.shape)

    # 10-D keeps enough structure for clustering while escaping the curse of dimensionality that
    # makes DBSCAN's distance threshold meaningless in 384-D. 2-D is for display only.
    z10 = umap.UMAP(n_components=10, n_neighbors=15, min_dist=0.0, metric="cosine",
                    random_state=a.seed).fit_transform(emb)
    z2 = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric="cosine",
                   random_state=a.seed).fit_transform(emb)

    df.to_parquet(OUT / "meta.parquet", index=False)
    np.save(OUT / "umap_10d.npy", z10.astype(np.float32))
    np.save(OUT / "umap_2d.npy", z2.astype(np.float32))
    np.save(OUT / "embeddings_384d.npy", emb.astype(np.float32))  # kept for the raw-space ablation
    print("saved to", OUT)


if __name__ == "__main__":
    main()
