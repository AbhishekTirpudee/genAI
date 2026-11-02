"""Text extraction helpers for supported resume file formats."""

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile

import fitz
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from lxml.etree import XMLSyntaxError


class ResumeFileError(ValueError):
    """Raised when a resume cannot be read or contains no extractable text."""


class UnsupportedResumeFormatError(ResumeFileError):
    """Raised when a resume is not a PDF or DOCX file."""


class ScannedResumeError(ResumeFileError):
    """Raised when a PDF has images but no extractable text."""


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF or DOCX bytes, reporting invalid files clearly."""
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise UnsupportedResumeFormatError(
            f"Unsupported resume format '{extension or '(no extension)'}'. "
            "Upload a PDF or DOCX file."
        )
    if not file_bytes:
        raise ResumeFileError("The uploaded resume is empty.")

    if extension == ".pdf":
        return _extract_pdf_text(file_bytes)
    return _extract_docx_text(file_bytes)


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            page_text = [page.get_text() for page in document]
            text = "\n".join(page_text).strip()
            if text:
                return text

            if any(page.get_images() for page in document):
                raise ScannedResumeError(
                    "This PDF contains images but no selectable text. "
                    "Use a text-based PDF or OCR the scanned resume first."
                )
            raise ResumeFileError("The PDF contains no extractable text.")
    except ScannedResumeError:
        raise
    except (fitz.FileDataError, ValueError, RuntimeError) as exc:
        raise ResumeFileError(
            "The PDF is invalid or corrupted and could not be read."
        ) from exc


def _extract_docx_text(file_bytes: bytes) -> str:
    try:
        document = Document(BytesIO(file_bytes))
    except (BadZipFile, PackageNotFoundError, XMLSyntaxError, ValueError) as exc:
        raise ResumeFileError(
            "The DOCX file is invalid or corrupted and could not be read."
        ) from exc

    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    table_rows = [
        "\t".join(cell.text for cell in row.cells)
        for table in document.tables
        for row in table.rows
    ]
    text = "\n".join(paragraphs + table_rows).strip()
    if not text:
        raise ResumeFileError("The DOCX file contains no extractable text.")
    return text
