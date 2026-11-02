import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import STORAGE_DIR, INDEX_FILE
from .text_splitter import TextChunk
from .pdf_loader import PDFDocument


class BM25Retriever:
    """
    Lightweight, fast BM25 implementation for exact academic keyword matching.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.doc_lens: List[int] = []

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z0-9_]{2,}\b', text.lower())

    def fit(self, corpus: List[str]):
        self.corpus_size = len(corpus)
        if self.corpus_size == 0:
            return

        self.doc_freqs = []
        self.doc_lens = []
        df_counts: Dict[str, int] = {}

        for doc in corpus:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            freqs: Dict[str, int] = {}
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1
            self.doc_freqs.append(freqs)

            for t in freqs.keys():
                df_counts[t] = df_counts.get(t, 0) + 1

        self.avgdl = sum(self.doc_lens) / (self.corpus_size or 1)
        self.idf = {}
        for word, freq in df_counts.items():
            # BM25 IDF formula with smoothing
            self.idf[word] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: str) -> np.ndarray:
        scores = np.zeros(self.corpus_size)
        if self.corpus_size == 0:
            return scores

        query_tokens = self._tokenize(query)
        for q in query_tokens:
            if q not in self.idf:
                continue
            idf_val = self.idf[q]
            for i, doc_freq in enumerate(self.doc_freqs):
                freq = doc_freq.get(q, 0)
                if freq == 0:
                    continue
                doc_len = self.doc_lens[i]
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / (self.avgdl or 1)))
                scores[i] += idf_val * (numerator / denominator)

        return scores


class VectorIndex:
    """
    Persistent academic vector store combining dense semantic embeddings
    and sparse lexical scoring.
    """
    def __init__(self):
        self.chunks: List[TextChunk] = []
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.bm25 = BM25Retriever()
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, stop_words='english')
        self.tfidf_matrix = None
        self.load_index()

    def add_document(self, doc: PDFDocument, chunks: List[TextChunk]):
        # Remove existing chunks for this document if re-uploading
        self.chunks = [c for c in self.chunks if c.doc_name != doc.filename]
        self.chunks.extend(chunks)

        self.documents[doc.filename] = {
            "file_path": doc.file_path,
            "filename": doc.filename,
            "total_pages": doc.total_pages,
            "total_words": doc.total_words,
            "chunk_count": len(chunks),
            "metadata": doc.metadata,
        }
        self._rebuild_index()
        self.save_index()

    def remove_document(self, filename: str) -> bool:
        if filename in self.documents:
            del self.documents[filename]
            self.chunks = [c for c in self.chunks if c.doc_name != filename]
            self._rebuild_index()
            self.save_index()
            return True
        return False

    def clear(self):
        self.chunks = []
        self.documents = {}
        self.tfidf_matrix = None
        self.bm25 = BM25Retriever()
        self.save_index()

    def _rebuild_index(self):
        if not self.chunks:
            self.tfidf_matrix = None
            self.bm25 = BM25Retriever()
            return

        corpus = [c.text for c in self.chunks]
        self.bm25.fit(corpus)
        try:
            self.tfidf_matrix = self.tfidf.fit_transform(corpus)
        except Exception:
            self.tfidf_matrix = None

    def search(self, query: str, top_k: int = 4) -> List[Tuple[TextChunk, float]]:
        """
        Hybrid search combining BM25 keyword relevance and TF-IDF cosine similarity.
        Returns list of (TextChunk, relevance_score) sorted by relevance.
        """
        if not self.chunks:
            return []

        # 1. BM25 score
        bm25_scores = self.bm25.get_scores(query)
        max_bm25 = np.max(bm25_scores) if len(bm25_scores) > 0 and np.max(bm25_scores) > 0 else 1.0
        normalized_bm25 = bm25_scores / max_bm25

        # 2. TF-IDF Cosine Similarity
        tfidf_scores = np.zeros(len(self.chunks))
        if self.tfidf_matrix is not None:
            try:
                q_vec = self.tfidf.transform([query])
                cosine_sim = (self.tfidf_matrix * q_vec.T).toarray().flatten()
                max_tfidf = np.max(cosine_sim) if np.max(cosine_sim) > 0 else 1.0
                tfidf_scores = cosine_sim / max_tfidf
            except Exception:
                pass

        # Hybrid weighting: 60% BM25 keyword matching + 40% semantic cosine
        final_scores = 0.6 * normalized_bm25 + 0.4 * tfidf_scores

        # Sort indices descending
        ranked_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for idx in ranked_indices:
            score = float(final_scores[idx])
            if score > 0.01:  # filter completely irrelevant chunks
                results.append((self.chunks[idx], round(score, 4)))

        # Fallback: if all scores are zero (e.g., unusual query), return top chunks from beginning
        if not results and self.chunks:
            results = [(self.chunks[0], 0.1)]

        return results

    def save_index(self):
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "documents": self.documents,
            "chunks": [c.to_dict() for c in self.chunks],
        }
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_index(self):
        if not INDEX_FILE.exists():
            return
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.documents = data.get("documents", {})
            self.chunks = [TextChunk.from_dict(c) for c in data.get("chunks", [])]
            self._rebuild_index()
        except Exception as e:
            print(f"[Warning] Error loading index: {e}")


# Singleton instance
vector_index = VectorIndex()
