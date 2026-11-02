"""
Configuration parameters for Sentence Transformer Embeddings and Vector Search.
"""

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Hyperparameters and architectural settings for the embedding pipeline."""

    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Pretrained sentence-transformer checkpoint for dense retrieval."
    )
    embedding_dimension: int = Field(
        default=384,
        description="Dimension size of the projected dense semantic vector space."
    )
    max_sequence_length: int = Field(
        default=512,
        description="Maximum token sequence length processed before truncation."
    )
    pooling_strategy: str = Field(
        default="mean_pooling",
        description="Strategy for aggregating token-level embeddings (mean_pooling or cls_token)."
    )
    normalize_embeddings: bool = Field(
        default=True,
        description="Whether L2 normalization is applied to produce unit hypersphere vectors."
    )
    batch_size: int = Field(
        default=32,
        description="Batch size for concurrent sentence tokenization and encoding."
    )
    distance_metric: str = Field(
        default="cosine",
        description="Distance metric for similarity calculation (cosine, dot_product, euclidean)."
    )


default_config = EmbeddingConfig()

