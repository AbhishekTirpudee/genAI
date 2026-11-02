"""
In-Memory Dense Vector Index and Exact Nearest Neighbor Searcher.
Facilitates fast sub-millisecond retrieval of target job embeddings matching candidate resumes.
"""

from typing import List, Dict, Any, Tuple
import math


class VectorIndex:
    """
    Dense Index for managing embedded document spaces.
    Stores pre-calculated L2-normalized sentence vectors.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: List[List[float]] = []
        self.metadata: List[Dict[str, Any]] = []

    def add(self, vector: List[float], meta: Dict[str, Any]):
        """Inserts an embedding vector and associated metadata into the index."""
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(vector)}")
        self.vectors.append(vector)
        self.metadata.append(meta)

    def size(self) -> int:
        return len(self.vectors)


class CosineSimilaritySearcher:
    """
    Search engine performing exhaustive inner product calculations
    across the dense vector index to find top-k relevant job profiles.
    """

    def __init__(self, index: VectorIndex):
        self.index = index

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Executes inner product search over stored normalized vectors.
        Returns top_k tuples of (similarity_score, metadata).
        """
        if not self.index.vectors:
            return []

        scores = []
        for vec, meta in zip(self.index.vectors, self.index.metadata):
            dot_product = sum(q * v for q, v in zip(query_vector, vec))
            scores.append((dot_product, meta))

        # Sort descending by score
        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[:top_k]

