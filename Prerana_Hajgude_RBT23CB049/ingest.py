"""
ingest.py - Ingests hardware manuals (PDFs) into ChromaDB with chunking and metadata.
"""

import os
import re
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
import chromadb
from chromadb.config import Settings

DEFAULT_COLLECTION_NAME = "tech_support_manuals"
DEFAULT_CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
DEFAULT_MANUALS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manuals")


def chunk_text_by_tokens(
    text: str,
    target_token_count: int = 800,
    overlap_token_count: int = 100
) -> List[str]:
    """
    Splits text into chunks of approximately `target_token_count` tokens (1 token ~ 0.75 words, ~4 chars)
    with `overlap_token_count` tokens overlap, preserving word boundaries.
    """
    clean_text = re.sub(r'\s+', ' ', text).strip()
    if not clean_text:
        return []

    words = clean_text.split(' ')
    # 800 tokens ~ 600 words
    target_words = max(50, int(target_token_count * 0.75))
    overlap_words = max(10, int(overlap_token_count * 0.75))
    step = max(1, target_words - overlap_words)

    if len(words) <= target_words:
        return [clean_text]

    chunks = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + target_words]
        chunk_str = " ".join(chunk_words).strip()
        if chunk_str:
            chunks.append(chunk_str)
        if i + target_words >= len(words):
            break

    return chunks


def load_and_chunk_pdf(pdf_path: str, target_token_count: int = 800) -> List[Dict[str, Any]]:
    """
    Reads a single PDF file page by page, splits text into ~800-token chunks,
    and returns a list of dictionaries with text and metadata.
    """
    records = []
    file_name = os.path.basename(pdf_path)

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return []

    for page_idx, page in enumerate(reader.pages):
        page_number = page_idx + 1
        page_text = page.extract_text() or ""
        page_text = page_text.strip()

        if not page_text:
            continue

        chunks = chunk_text_by_tokens(page_text, target_token_count=target_token_count)
        for chunk_idx, chunk in enumerate(chunks):
            record = {
                "id": f"{file_name}_p{page_number}_c{chunk_idx}",
                "text": chunk,
                "metadata": {
                    "file_name": file_name,
                    "page_number": int(page_number),
                    "chunk_index": int(chunk_idx)
                }
            }
            records.append(record)

    return records


def ingest_manuals(
    manuals_dir: Optional[str] = None,
    chroma_dir: Optional[str] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    target_token_count: int = 800,
    clear_existing: bool = True
) -> Dict[str, Any]:
    """
    Loads all PDFs from manuals_dir, chunks them, and stores in ChromaDB.
    """
    # Resolve manuals_dir
    if not manuals_dir:
        manuals_dir = os.environ.get("MANUALS_DIR", DEFAULT_MANUALS_DIR)

    # If relative path does not exist, check /manuals or relative to cwd
    if not os.path.exists(manuals_dir):
        alt_paths = ["manuals", "/manuals", os.path.join(os.getcwd(), "manuals")]
        for alt in alt_paths:
            if os.path.exists(alt):
                manuals_dir = alt
                break

    if not chroma_dir:
        chroma_dir = os.environ.get("CHROMA_DIR", DEFAULT_CHROMA_DIR)

    os.makedirs(manuals_dir, exist_ok=True)
    os.makedirs(chroma_dir, exist_ok=True)

    print(f"Ingesting PDFs from: {manuals_dir}")
    print(f"ChromaDB storage at: {chroma_dir}")

    # Initialize Chroma persistent client
    client = chromadb.PersistentClient(path=chroma_dir)

    if clear_existing:
        try:
            client.delete_collection(name=collection_name)
            print(f"Cleared existing collection: {collection_name}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    pdf_files = [
        os.path.join(manuals_dir, f)
        for f in os.listdir(manuals_dir)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"No PDF files found in {manuals_dir}")
        return {
            "pdf_count": 0,
            "chunk_count": 0,
            "files": [],
            "status": "No PDF files found."
        }

    total_chunks = 0
    all_docs = []
    all_metadatas = []
    all_ids = []
    processed_files = []

    for pdf_path in sorted(pdf_files):
        records = load_and_chunk_pdf(pdf_path, target_token_count=target_token_count)
        if records:
            for rec in records:
                all_ids.append(rec["id"])
                all_docs.append(rec["text"])
                all_metadatas.append(rec["metadata"])
            processed_files.append(os.path.basename(pdf_path))
            total_chunks += len(records)
            print(f"Processed '{os.path.basename(pdf_path)}': {len(records)} chunks")

    # Upsert/Add to collection in batches of 100
    batch_size = 100
    for i in range(0, len(all_ids), batch_size):
        b_ids = all_ids[i : i + batch_size]
        b_docs = all_docs[i : i + batch_size]
        b_meta = all_metadatas[i : i + batch_size]
        collection.upsert(ids=b_ids, documents=b_docs, metadatas=b_meta)

    result = {
        "pdf_count": len(processed_files),
        "chunk_count": total_chunks,
        "files": processed_files,
        "status": f"Successfully indexed {total_chunks} chunks from {len(processed_files)} PDFs."
    }
    print(result["status"])
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest PDF manuals into ChromaDB")
    parser.add_argument("--manuals", default=DEFAULT_MANUALS_DIR, help="Path to manuals directory")
    parser.add_argument("--chroma", default=DEFAULT_CHROMA_DIR, help="Path to ChromaDB directory")
    args = parser.parse_args()

    ingest_manuals(manuals_dir=args.manuals, chroma_dir=args.chroma)

