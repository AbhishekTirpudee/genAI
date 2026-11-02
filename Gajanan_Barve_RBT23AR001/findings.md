## Findings

*All numbers come from `benchmark.py` (shapes: mean of 5 random draws of 600 points; news: one fixed sample of 3,000 headlines). ARI = Adjusted Rand Index against the true labels. **Oracle** uses the labels to tune (an optimistic upper bound); **auto** uses none.*

**1. Each algorithm's assumption shows up exactly where theory says it should.**
- On round blobs all three score ARI ≈ 1.0.
- On stretched (anisotropic) blobs EM reaches 1.00 because it learns each cluster's covariance; K-Means, which assumes round clusters, reaches 0.95 even when given the correct *k*.
- On two moons and concentric circles **only DBSCAN works** (ARI 0.999 and 1.000 tuned). K-Means and EM score about 0.5 on moons and 0.00 on circles, because no centroid or Gaussian can separate a ring from the ring inside it.
- Varied density did **not** break anything at the contrast used here: all three scored ≥ 0.99 when tuned.

**2. Label-free quality metrics can prefer the wrong answer.** On concentric circles DBSCAN is perfect (ARI 1.00) yet has silhouette 0.11 and Davies-Bouldin 599, while K-Means is no better than chance (ARI −0.00) yet scores silhouette 0.35 and Davies-Bouldin 1.18. Silhouette, Davies-Bouldin and Calinski-Harabasz all reward compact, convex clusters, so they cannot judge DBSCAN fairly on ring-shaped data.

**3. Choosing the parameters mattered as much as choosing the algorithm.** Without labels, silhouette picked *k* = 2 on the anisotropic blobs (ARI 0.57 vs 0.95 at the true *k* = 3) and *k* = 2 on the news data (0.29 vs 0.65 at *k* = 4). BIC picked 8 components for EM on the news data (0.44 vs 0.63 at 4). On the news data the ranking even flips: tuned with labels, K-Means (0.65) > EM (0.63) > DBSCAN (0.57); tuned without labels, DBSCAN (0.49) > EM (0.44) > K-Means (0.29). A coarser 2-cluster split is not necessarily "wrong"; it just disagrees with a 4-topic labelling.

**4. High dimensions break DBSCAN, not K-Means or EM.** In raw 384-D embedding space DBSCAN returned one giant cluster for every `eps` tried (ARI 0.00), because distances between points concentrate and no density threshold separates anything. K-Means and EM still worked there (0.58 and 0.57) but trailed their UMAP 10-D scores (0.65 and 0.63). Reducing dimensionality first helped every algorithm. (The UMAP was fitted without labels; silhouette values are **not comparable** between the two spaces: 0.55 vs 0.04.)

**5. On real text no algorithm recovers the four topics cleanly.** The best ARI is 0.65. Sports (96% of its headlines in one K-Means cluster) and World (91%) separate well, but Sci/Tech (73%) and Business (80%) blur: 95 Business headlines landed in the Sci/Tech cluster and 129 Sci/Tech headlines landed with World (see the contingency heatmap in tab 2). Part of this is plausibly label ambiguity (tech-business stories fit both topics), though I did not test that. DBSCAN did not merge topics in UMAP space; it *fragmented* them into 6-7 clusters while labelling only 2-5% of points as noise.

**6. Stability and cost.** K-Means and EM were perfectly repeatable when the data matched their assumptions, but became seed-dependent when it did not (circles: stability 0.60 and 0.52). DBSCAN's stability of 1.0 only reflects that it is deterministic, not that it is right. EM was 1.5-10× slower than K-Means (typically 2-3×; it runs several initialisations). DBSCAN was faster than K-Means on all five 2-D datasets but about 1.3× slower on the 10-D news data. EM is the only one of the three that also gives soft assignments (a confidence per point).

**Caveats.** One news sample and one UMAP seed (no confidence intervals); five draws for the shapes; oracle numbers are optimistic by construction; all datasets are small, so timings are indicative only.

**When to use which (from this evidence).** K-Means: fast baseline when clusters are roughly round and *k* is known. EM: when clusters are elliptical or you need probabilities, and you can afford model selection with BIC. DBSCAN: when clusters have arbitrary shape and outliers matter, in **low-dimensional** data, with `eps` chosen carefully.
