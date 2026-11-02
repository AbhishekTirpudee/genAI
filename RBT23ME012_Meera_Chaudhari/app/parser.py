"""
Multi-format Resume Extraction Engine.
Supports PDF (.pdf), Microsoft Word (.docx), and plain text (.txt).
"""

import io
from typing import Tuple


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF (fitz)."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text = page.get_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from Word Document (.docx) using python-docx."""
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
    
    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                text_parts.append(" | ".join(row_text))
                
    return "\n".join(text_parts).strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from plain text file with fallback encodings."""
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            return file_bytes.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore").strip()


def extract_resume_text(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    """
    Detects format from filename and extracts plain text.
    Returns: (extracted_text, file_type)
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes), "pdf"
    elif ext in ["docx", "doc"]:
        return extract_text_from_docx(file_bytes), "docx"
    elif ext in ["txt", "md", "rtf"]:
        return extract_text_from_txt(file_bytes), "txt"
    else:
        # Fallback to text attempt
        try:
            return extract_text_from_txt(file_bytes), "unknown"
        except Exception as e:
            raise ValueError(f"Unsupported file format '.{ext}'. Please upload PDF, DOCX, or TXT.")

