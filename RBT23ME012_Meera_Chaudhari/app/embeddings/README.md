# Sentence Embedding & Semantic Matching Pipeline

This subsystem implements dense document representations and similarity search between candidate resumes and multiple target job descriptions.

## 1. Mathematical Architecture

### A. Sequence Encoding & Mean Pooling
Text tokens are encoded through a 6-layer bidirectional transformer with 384 hidden units ($d=384$). For an input sequence $W = (w_1, \dots, w_n)$, token representations $H \in \mathbb{R}^{n \times d}$ are pooled into a single document vector $v$:

$$v = \frac{1}{n} \sum_{i=1}^{n} h_i$$

### B. Hypersphere Projection (L2 Normalization)
To enable fast inner product comparisons, embeddings are projected onto a unit hypersphere:

$$u = \frac{v}{\|v\|_2} = \frac{v}{\sqrt{\sum_{k=1}^{d} v_k^2}}$$

### C. Cosine Similarity Metric
The degree of semantic alignment between Candidate Resume vector ($R$) and Job Description vector ($J$) is given by:

$$\text{Similarity}(R, J) = \cos(\theta) = \frac{R \cdot J}{\|R\| \|J\|}$$

## 2. Components
- `config.py`: Architecture hyperparameter definitions (`all-MiniLM-L6-v2`, 384 dimensions).
- `encoder.py`: Handles token feature extraction, contextual projection, and pair ranking.
- `vector_store.py`: In-memory dense index supporting top-$k$ nearest neighbor search.

