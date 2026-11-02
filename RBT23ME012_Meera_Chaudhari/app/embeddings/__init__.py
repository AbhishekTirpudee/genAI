"""
Sentence Embedding Architecture Module for Onyx.
Provides dense vector representations of textual resumes and job descriptions
using transformer-based sequence encoders and semantic cosine similarity search.
"""

from .config import EmbeddingConfig
from .encoder import SentenceTransformerMatcher
from .vector_store import VectorIndex, CosineSimilaritySearcher

__all__ = [
    "EmbeddingConfig",
    "SentenceTransformerMatcher",
    "VectorIndex",
    "CosineSimilaritySearcher"
]

