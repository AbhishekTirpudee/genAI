import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Generator
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .config import config
from .pdf_loader import PDFLoader, PDFDocument
from .text_splitter import AcademicTextSplitter, TextChunk
from .vector_store import vector_index
from .llm_engine import llm_engine
from .ui import console


class RAGEngine:
    def __init__(self):
        self.loader = PDFLoader()
        self.splitter = AcademicTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        self.index = vector_index
        self.llm = llm_engine
        self.last_retrieved_chunks: List[Tuple[TextChunk, float]] = []
        self.chat_history: List[Dict[str, str]] = []

    def ingest_path(self, path_str: str) -> Dict[str, Any]:
        """Ingests a single PDF or all PDFs in a directory."""
        path = Path(path_str).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path_str}")

        docs_to_process: List[Path] = []
        if path.is_dir():
            docs_to_process = list(path.glob("*.pdf")) + list(path.glob("*.PDF"))
            if not docs_to_process:
                raise ValueError(f"No PDF files found in directory: {path}")
        elif path.is_file():
            if path.suffix.lower() != ".pdf":
                raise ValueError(f"File must be a PDF: {path.name}")
            docs_to_process = [path]

        total_pages = 0
        total_chunks = 0
        processed_docs = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Ingesting {len(docs_to_process)} document(s)...", total=len(docs_to_process))

            for pdf_path in docs_to_process:
                progress.update(task, description=f"[cyan]Parsing {pdf_path.name}...")
                doc = self.loader.load_pdf(pdf_path)
                
                progress.update(task, description=f"[cyan]Chunking {pdf_path.name}...")
                chunks = self.splitter.split_document(doc)
                
                progress.update(task, description=f"[cyan]Indexing {pdf_path.name}...")
                self.index.add_document(doc, chunks)

                total_pages += doc.total_pages
                total_chunks += len(chunks)
                processed_docs.append(doc.filename)
                progress.advance(task)

        return {
            "processed_docs": processed_docs,
            "total_pages": total_pages,
            "total_chunks": total_chunks,
        }

    def ask(self, query: str, top_k: Optional[int] = None) -> Generator[str, None, None]:
        """Performs RAG search and streams the answer."""
        k = top_k or config.top_k
        self.last_retrieved_chunks = self.index.search(query, top_k=k)

        if not self.last_retrieved_chunks:
            yield "No notes currently indexed. Please upload a PDF first with `/upload <file>`."
            return

        full_answer = []
        for token in self.llm.stream_answer(query, self.last_retrieved_chunks):
            full_answer.append(token)
            yield token

        # Store in session history
        self.chat_history.append({
            "query": query,
            "answer": "".join(full_answer),
            "sources": [
                f"{c.doc_name} (p.{c.page_num}, score: {s:.2f})"
                for c, s in self.last_retrieved_chunks
            ],
        })

    def export_history(self, file_path: str = "study_session_notes.md") -> str:
        """Exports the chat session and RAG answers into a formatted Markdown document."""
        if not self.chat_history:
            return "No Q&A history to export."

        out_path = Path(file_path).resolve()
        lines = [
            "# 🎓 ScholarRAG Study Session Notes\n",
            f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
            f"*Indexed Documents: {', '.join(self.index.documents.keys())}*\n",
            "---\n",
        ]

        for i, item in enumerate(self.chat_history, 1):
            lines.append(f"## Q{i}: {item['query']}\n")
            lines.append(f"{item['answer']}\n")
            lines.append(f"**Sources Consulted:** {', '.join(item['sources'])}\n")
            lines.append("---\n")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(out_path)


rag_engine = RAGEngine()
