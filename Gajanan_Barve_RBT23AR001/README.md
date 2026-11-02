---
title: K-Means vs EM vs DBSCAN
emoji: 🧩
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Interactive comparison of K-Means, EM (GMM) and DBSCAN
---

# K-Means vs EM vs DBSCAN

**Aim.** Perform clustering with K-Means, EM (Gaussian mixture) and DBSCAN, and compare the resulting clusters.

An interactive Gradio app plus a companion notebook (`analysis.ipynb`) that share the same code.

## What is in the app
1. **Shapes playground**: five synthetic 2-D datasets (round blobs, stretched blobs, varied density, moons, circles) with live controls for every algorithm's parameters, three synchronised scatter panels, a score table, and helpers for choosing *k* (elbow, silhouette), the number of EM components (BIC/AIC) and `eps` (k-distance plot).
2. **Real data**: 3,000 AG News headlines embedded with `sentence-transformers/all-MiniLM-L6-v2`, reduced with UMAP. Compare the algorithms in UMAP 10-D versus raw 384-D, see how well they agree with each other (pairwise ARI), how each cluster maps to the true topics, and what is inside each cluster (distinctive terms, most central headline).
3. **Scorecard & findings**: every algorithm on every dataset, under two protocols (auto = no labels used to tune, oracle = labels used to tune), with written conclusions. See `findings.md`.

## Procedure
| Step | Method |
|---|---|
| Algorithms | `KMeans(k-means++, n_init=10)`, `GaussianMixture` (EM; hard labels = argmax posterior), `DBSCAN` (noise = -1) |
| Choosing parameters | silhouette & elbow for *k*; BIC/AIC for EM; k-distance knee for `eps`, `min_samples = clip(2·dim, 5, 20)` |
| Internal metrics (no labels) | silhouette, Davies-Bouldin, Calinski-Harabasz (DBSCAN noise excluded, noise share reported) |
| External metrics (vs truth) | ARI, NMI, homogeneity, completeness, V-measure (DBSCAN noise counted as its own group, so it is penalised, not hidden) |
| Comparing clusterings | pairwise ARI between algorithms, true-class × cluster contingency, stability over 5 seeds, fit time |

## Reproduce
```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python precompute.py      # AG News -> embeddings -> UMAP   (writes data/)
.venv/bin/python benchmark.py       # writes data/benchmark.csv
.venv/bin/python -m pytest tests    # sanity checks of textbook behaviour
.venv/bin/python app.py             # http://127.0.0.1:7860
```

## Honest limits
* The oracle protocol uses the labels to tune and is therefore an optimistic upper bound.
* One news sample and one UMAP seed; no confidence intervals on the real-data numbers.
* Charts keep a fixed light surface so the validated colour palette always sits on the surface it was checked against; marker shapes, labels and tables carry identity redundantly (the yellow and magenta swatches are below 3:1 contrast on that surface).
* AG News text has HTML debris; it is cleaned for display and term analysis, but the embeddings were computed on the raw text.
