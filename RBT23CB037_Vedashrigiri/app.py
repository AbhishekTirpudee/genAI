"""
app.py
FastAPI Server for ScholarMind AI: Academic PDF RAG Assistant.
Serves both the REST API and modern web frontend.
"""

import os
import glob
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from rag_engine import AcademicRAGEngine

app = FastAPI(
    title="ScholarMind AI - Academic Notes RAG Assistant",
    description="Multi-Page Academic PDF Ingestion, Hybrid BM25/TF-IDF RRF Retrieval, Flashcards & Practice Quiz Generation",
    version="2.0.0"
)

# Global engine instance
engine = AcademicRAGEngine()

# Automatically preload sample notes if available
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_notes")
if os.path.exists(SAMPLE_DIR):
    for sample_pdf in glob.glob(os.path.join(SAMPLE_DIR, "*.pdf")):
        try:
            with open(sample_pdf, "rb") as f:
                content = f.read()
            filename = os.path.basename(sample_pdf)
            engine.add_pdf(content, filename)
            print(f"[ScholarMind] Preloaded sample note: {filename}")
        except Exception as e:
            print(f"[ScholarMind] Could not preload {sample_pdf}: {e}")

# Request / Response Schemas
class ChatRequest(BaseModel):
    question: str
    history: Optional[List[Dict[str, str]]] = None

class SettingsRequest(BaseModel):
    api_key: str


@app.get("/api/status")
def get_status():
    has_key = bool(engine.api_key and engine.gemini_client is not None)
    mode = "Google Gemini 2.5 Flash (Grounded RAG)" if has_key else "Autonomous Hybrid RAG (Offline Zero-Key Mode)"
    return {
        "status": "online",
        "documents_count": len(engine.documents),
        "chunks_count": len(engine.chunks),
        "api_key_configured": has_key,
        "engine_mode": mode,
        "total_pages": sum(d.get("total_pages", 0) for d in engine.documents.values()),
        "total_words": sum(d.get("total_words", 0) for d in engine.documents.values()),
    }


@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    results = []
    errors = []
    latest_doc_id = None
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            errors.append(f"{file.filename}: Only PDF files are supported.")
            continue
        try:
            content = await file.read()
            if len(content) == 0:
                errors.append(f"{file.filename}: Uploaded file is empty.")
                continue
            doc_meta = engine.add_pdf(content, file.filename)
            results.append(doc_meta)
            latest_doc_id = doc_meta["doc_id"]
        except Exception as e:
            errors.append(f"{file.filename}: Failed to parse ({str(e)})")

    # Generate custom starter questions strictly from the newly uploaded PDF
    suggested_questions = engine.get_suggested_questions(latest_doc_id, count=4) if latest_doc_id else []

    return {
        "uploaded": results,
        "errors": errors,
        "latest_doc_id": latest_doc_id,
        "suggested_questions": suggested_questions,
        "total_documents": len(engine.documents),
        "total_chunks": len(engine.chunks),
    }


@app.get("/api/suggested-questions")
def get_suggested_questions(doc_id: Optional[str] = None):
    questions = engine.get_suggested_questions(doc_id, count=4)
    return {"questions": questions}


@app.post("/api/load-sample")
def load_sample_notes():
    loaded = []
    latest_doc_id = None
    if os.path.exists(SAMPLE_DIR):
        for sample_pdf in glob.glob(os.path.join(SAMPLE_DIR, "*.pdf")):
            fname = os.path.basename(sample_pdf)
            # Avoid duplicate loading if already loaded
            if any(d["filename"] == fname for d in engine.documents.values()):
                continue
            with open(sample_pdf, "rb") as f:
                content = f.read()
            doc_meta = engine.add_pdf(content, fname)
            loaded.append(doc_meta)
            latest_doc_id = doc_meta["doc_id"]
    return {
        "message": f"Loaded {len(loaded)} sample academic document(s).",
        "documents": list(engine.documents.values()),
        "latest_doc_id": latest_doc_id,
        "suggested_questions": engine.get_suggested_questions(latest_doc_id),
        "total_chunks": len(engine.chunks),
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    response = engine.query(q, req.history)
    return response


@app.get("/api/documents")
def get_documents():
    return {
        "documents": list(engine.documents.values()),
        "total_chunks": len(engine.chunks),
    }


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    success = engine.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document removed from index.", "remaining_documents": len(engine.documents)}


@app.delete("/api/clear")
def clear_all_documents():
    engine.clear_all()
    return {"message": "All indexed academic notes cleared.", "total_chunks": 0}


@app.get("/api/chunks")
def get_chunks(search: Optional[str] = None, doc_id: Optional[str] = None, limit: int = 50):
    filtered = engine.chunks
    if doc_id:
        filtered = [c for c in filtered if c.doc_id == doc_id]
    if search:
        s = search.lower()
        filtered = [c for c in filtered if s in c.text.lower() or s in c.section.lower()]
    return {
        "total_matched": len(filtered),
        "chunks": [c.to_dict() for c in filtered[:limit]]
    }


@app.post("/api/flashcards")
def get_flashcards(count: int = 8, doc_id: Optional[str] = None):
    cards = engine.generate_flashcards(count=count, doc_id=doc_id)
    return {"flashcards": cards, "total": len(cards)}


@app.post("/api/quiz")
def get_quiz(count: int = 5, doc_id: Optional[str] = None):
    quiz = engine.generate_quiz(count=count, doc_id=doc_id)
    return {"quiz": quiz, "total": len(quiz)}


@app.get("/api/summary")
def get_summary():
    return engine.generate_summary()


@app.post("/api/settings")
def update_settings(req: SettingsRequest):
    key = req.api_key.strip()
    engine.set_api_key(key)
    has_key = bool(engine.gemini_client is not None)
    return {
        "status": "updated",
        "api_key_configured": has_key,
        "engine_mode": "Google Gemini 2.5 Flash (Grounded RAG)" if has_key else "Autonomous Hybrid RAG (Offline Zero-Key Mode)"
    }


# Static files mount
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "ScholarMind AI backend running. Frontend static files pending."})


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print(" 🚀 ScholarMind AI: Academic PDF RAG Assistant Server")
    print(" Running on: http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
