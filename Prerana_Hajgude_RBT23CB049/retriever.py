"""
retriever.py - Retrieves top relevant chunks from ChromaDB for a given query.
"""

import os
from typing import List, Dict, Any, Optional
import chromadb

DEFAULT_COLLECTION_NAME = "tech_support_manuals"
DEFAULT_CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")


def get_relevant_chunks(
    query: str,
    n_results: int = 4,
    chroma_dir: Optional[str] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME
) -> List[Dict[str, Any]]:
    """
    Given a user query, queries ChromaDB and returns the top `n_results` (default 4) relevant chunks.
    Each result item contains:
      - text: str (the chunk document text)
      - file_name: str (source PDF name)
      - page_number: int (page number in PDF)
      - distance: float (cosine distance / similarity score)
      - id: str (chunk identifier)
    """
    if not query or not query.strip():
        return []

    if not chroma_dir:
        chroma_dir = os.environ.get("CHROMA_DIR", DEFAULT_CHROMA_DIR)

    if not os.path.exists(chroma_dir):
        print(f"Warning: ChromaDB directory '{chroma_dir}' not found.")
        return []

    try:
        client = chromadb.PersistentClient(path=chroma_dir)
        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            # Collection might not exist yet
            return []

        total_count = collection.count()
        if total_count == 0:
            return []

        actual_k = min(n_results, total_count)
        results = collection.query(
            query_texts=[query.strip()],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"]
        )

        formatted_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
            dists = results["distances"][0] if "distances" in results and results["distances"] else []
            ids = results["ids"][0] if "ids" in results and results["ids"] else []

            for i in range(len(docs)):
                meta = metas[i] if i < len(metas) and metas[i] else {}
                chunk_info = {
                    "text": docs[i],
                    "file_name": meta.get("file_name", "Unknown Manual"),
                    "page_number": meta.get("page_number", 1),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": dists[i] if i < len(dists) else 0.0,
                    "id": ids[i] if i < len(ids) else f"chunk_{i}"
                }
                formatted_chunks.append(chunk_info)

        return formatted_chunks

    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []


if __name__ == "__main__":
    import sys
    test_query = sys.argv[1] if len(sys.argv) > 1 else "My laptop fan is very loud"
    print(f"--- Querying: '{test_query}' ---")
    chunks = get_relevant_chunks(test_query, n_results=4)
    print(f"Retrieved {len(chunks)} chunks:\n")
    for idx, c in enumerate(chunks, 1):
        print(f"[{idx}] Source: {c['file_name']} (Page {c['page_number']}) | Distance: {c['distance']:.4f}")
        print(f"Text Snippet: {c['text'][:180]}...")
        print("-" * 50)

