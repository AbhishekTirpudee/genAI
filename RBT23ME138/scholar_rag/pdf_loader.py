import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pypdf


class PDFDocument:
    def __init__(self, file_path: str, pages: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.file_path = str(Path(file_path).resolve())
        self.filename = Path(file_path).name
        self.pages = pages  # list of {"page_num": int, "text": str, "word_count": int}
        self.metadata = metadata
        self.total_pages = len(pages)
        self.total_words = sum(p["word_count"] for p in pages)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "total_pages": self.total_pages,
            "total_words": self.total_words,
            "metadata": self.metadata,
            "pages": self.pages,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PDFDocument":
        doc = cls(
            file_path=data["file_path"],
            pages=data["pages"],
            metadata=data.get("metadata", {}),
        )
        return doc


class PDFLoader:
    """Extracts and cleans text from academic PDF documents with page tracking."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans extracted text while preserving academic formatting."""
        if not text:
            return ""
        # Fix hyphenated line breaks (e.g., 'algo-\nrithm' -> 'algorithm')
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        # Normalize excessive newlines (more than 2 newlines to 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace non-breaking spaces and tabs
        text = text.replace('\xa0', ' ').replace('\t', ' ')
        # Remove repeated horizontal lines or underscores often used in notes
        text = re.sub(r'[-_=]{4,}', '', text)
        # Normalize multiple spaces into single space per line
        lines = [re.sub(r' {2,}', ' ', line).strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()

    @classmethod
    def load_pdf(cls, file_path: str | Path) -> PDFDocument:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {path.name}")

        pages: List[Dict[str, Any]] = []
        doc_metadata: Dict[str, Any] = {}

        try:
            reader = pypdf.PdfReader(str(path))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ValueError(f"PDF '{path.name}' is password protected and cannot be decrypted.")

            if reader.metadata:
                doc_metadata = {
                    "title": str(reader.metadata.title or path.stem),
                    "author": str(reader.metadata.author or "Unknown"),
                    "subject": str(reader.metadata.subject or ""),
                }
            else:
                doc_metadata = {"title": path.stem, "author": "Unknown"}

            for idx, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned = cls.clean_text(raw_text)
                word_count = len(cleaned.split())
                pages.append({
                    "page_num": idx + 1,
                    "text": cleaned,
                    "word_count": word_count,
                })

        except Exception as e:
            raise RuntimeError(f"Error reading PDF '{path.name}': {str(e)}")

        return PDFDocument(file_path=str(path), pages=pages, metadata=doc_metadata)

    @classmethod
    def load_directory(cls, dir_path: str | Path) -> List[PDFDocument]:
        folder = Path(dir_path).resolve()
        if not folder.is_dir():
            raise NotADirectoryError(f"Directory not found: {folder}")
        pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        documents = []
        for p in sorted(pdf_files):
            try:
                documents.append(cls.load_pdf(p))
            except Exception as e:
                print(f"[Warning] Could not load {p.name}: {e}")
        return documents
