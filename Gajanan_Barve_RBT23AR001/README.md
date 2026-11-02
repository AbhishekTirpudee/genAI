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

# K-Means vs EM vs DBSCAN: what the clusters tell us

**Aim.** Cluster the same data with K-Means, EM (Gaussian mixture) and DBSCAN, and compare the clusters they produce.

**Live app:** https://huggingface.co/spaces/thebenmerlin/kmeans-vs-em-vs-dbscan · **Notebook:** `analysis.ipynb` · **Full write-up:** `findings.md`

> **Headline.** No algorithm is best everywhere. Each wins exactly where its assumption holds, and *how the parameters are chosen* matters as much as which algorithm is used.

## Scorecard

Adjusted Rand Index (ARI) against the true labels: 1 = perfect, 0 = chance. Best per row in **bold**.
Shapes are the mean of 5 random draws of 600 points; the news data is one fixed sample of 3,000 headlines.

**Tuned with labels** (oracle: an optimistic upper bound)

| Dataset | K-Means | EM (GMM) | DBSCAN |
|---|---:|---:|---:|
| Spherical blobs | **1.00** | **1.00** | **1.00** |
| Anisotropic blobs | 0.95 | **1.00** | **1.00** |
| Varied density | 0.99 | **1.00** | **1.00** |
| Two moons | 0.48 | 0.50 | **1.00** |
| Concentric circles | 0.00 | 0.00 | **1.00** |
| News · UMAP 10-D | **0.65** | 0.63 | 0.57 |
| News · raw 384-D | **0.58** | 0.57 | 0.01 |

**Tuned without labels** (auto: silhouette for k, BIC for EM, k-distance knee for eps)

| Dataset | K-Means | EM (GMM) | DBSCAN |
|---|---:|---:|---:|
| Spherical blobs | **1.00** | **1.00** | 0.94 |
| Anisotropic blobs | 0.57 | **1.00** | 0.94 |
| Varied density | 0.99 | **1.00** | 0.95 |
| Two moons | 0.35 | 0.25 | **0.93** |
| Concentric circles | 0.00 | 0.13 | **0.71** |
| News · UMAP 10-D | 0.29 | 0.44 | **0.49** |
| News · raw 384-D | **0.54** | 0.36 | 0.00 |

## Findings

1. **Each algorithm's assumption shows up where theory says it should.** On round blobs all three score about 1.0. On stretched (elliptical) blobs EM wins because it learns each cluster's covariance, while K-Means falls to 0.95 even with the right k. On moons and circles **only DBSCAN works**; K-Means and EM score about 0.5 and 0.0, because no centroid or Gaussian can separate a ring from the ring inside it.
2. **Label-free metrics can prefer the wrong answer.** On concentric circles DBSCAN is perfect (ARI 1.00) yet has silhouette 0.11, while K-Means is at chance (ARI 0.00) yet scores silhouette 0.35. Silhouette, Davies-Bouldin and Calinski-Harabasz all reward compact, convex clusters.
3. **Choosing the parameters mattered as much as choosing the algorithm.** Without labels, silhouette picked k = 2 on the stretched blobs (ARI 0.57 vs 0.95 at the true k = 3) and on the news data (0.29 vs 0.65 at k = 4). On the news data the ranking even flips: with labels K-Means > EM > DBSCAN, without labels DBSCAN > EM > K-Means.
4. **High dimensions break DBSCAN, not K-Means or EM.** In raw 384-D embedding space DBSCAN returned one giant cluster for every `eps` tried (ARI 0.00), because distances concentrate and no density threshold separates anything. K-Means and EM still worked (0.58 and 0.57) but trailed their UMAP 10-D scores (0.65 and 0.63).
5. **On real text no method recovers the four topics cleanly** (best ARI 0.65). Sports (96%) and World (91%) separate well, but Sci/Tech (73%) and Business (80%) blur. DBSCAN did not merge topics; it fragmented them into 6-7 clusters and flagged only 2-5% of points as noise.
6. **Stability and cost.** K-Means and EM were repeatable when the data matched their assumptions and became seed-dependent when it did not. EM was typically 2-3x slower than K-Means (it runs several initialisations). EM is the only one of the three that also gives soft assignments (a probability per point).

## When to use which

| | Use it when | Avoid it when |
|---|---|---|
| **K-Means** | clusters are roughly round and k is known; you want a fast baseline | clusters are elongated or non-convex |
| **EM (GMM)** | clusters are elliptical, or you need probabilities | the data is high-dimensional with few samples (use a diagonal covariance) |
| **DBSCAN** | clusters have arbitrary shape and outliers matter, in low dimension | the data is high-dimensional (shown above); very different cluster densities can also hurt, though the moderate contrast tested here did not |

## Caveats
- Oracle numbers use the labels to tune, so they are optimistic by construction.
- One news sample and one UMAP seed: no confidence intervals on the real-data numbers.
- All datasets are small, so timings are indicative only.
- Part of the Business / Sci/Tech blur is plausibly label ambiguity; this was not tested.

## Method
- **Data:** five synthetic 2-D shapes (round blobs, stretched blobs, varied density, moons, circles) and 3,000 AG News headlines (750 per topic) embedded with `all-MiniLM-L6-v2`, then reduced with UMAP (10-D to cluster in, 2-D to display). The topic labels are used only to score, never to cluster.
- **Algorithms:** scikit-learn `KMeans` (k-means++), `GaussianMixture` (EM; hard label = most probable component), `DBSCAN` (noise = -1).
- **Metrics:** ARI, NMI, homogeneity, completeness and V-measure against the truth (DBSCAN noise counts as its own group, so it is penalised, not hidden); silhouette, Davies-Bouldin and Calinski-Harabasz without labels (noise excluded, noise share reported); pairwise agreement between algorithms; stability over 5 seeds; fit time.

## Reproduce
```bash
pip install -r requirements-dev.txt
python precompute.py      # AG News -> embeddings -> UMAP   (writes data/)
python benchmark.py       # writes data/benchmark.csv
python -m pytest tests    # 10 sanity checks of textbook behaviour
python app.py             # interactive app at http://127.0.0.1:7860
```

## Files
`app.py` Gradio app · `analysis.ipynb` notebook · `data.py`, `clustering.py`, `metrics.py`, `viz.py` shared code · `benchmark.py` scorecard · `precompute.py` embeddings · `findings.md` full write-up · `data/` precomputed embeddings and results · `tests/` sanity checks
