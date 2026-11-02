import re
from typing import List, Dict, Any
from .pdf_loader import PDFDocument


class TextChunk:
    def __init__(
        self,
        chunk_id: str,
        text: str,
        doc_name: str,
        file_path: str,
        page_num: int,
        chunk_index: int,
        metadata: Dict[str, Any] = None,
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.doc_name = doc_name
        self.file_path = file_path
        self.page_num = page_num
        self.chunk_index = chunk_index
        self.metadata = metadata or {}

    @property
    def cited_text(self) -> str:
        """Text with citation header prefix for LLM grounding."""
        return f"[Document: {self.doc_name} | Page {self.page_num}]\n{self.text}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "doc_name": self.doc_name,
            "file_path": self.file_path,
            "page_num": self.page_num,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextChunk":
        return cls(
            chunk_id=data["chunk_id"],
            text=data["text"],
            doc_name=data["doc_name"],
            file_path=data["file_path"],
            page_num=data["page_num"],
            chunk_index=data["chunk_index"],
            metadata=data.get("metadata", {}),
        )


class AcademicTextSplitter:
    """
    Intelligent chunker designed specifically for academic lecture notes,
    textbooks, and study guides. Respects paragraph boundaries, bullet points,
    and headings.
    """

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_document(self, doc: PDFDocument) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        global_chunk_idx = 0

        for page in doc.pages:
            page_num = page["page_num"]
            raw_text = page["text"]
            if not raw_text.strip():
                continue

            # Split the page text into natural segments (paragraphs / sections)
            page_chunks = self._chunk_page_text(raw_text)

            for p_idx, text_segment in enumerate(page_chunks):
                if len(text_segment.strip()) < 30:
                    # Skip trivial fragments unless it's the only text
                    if len(page_chunks) > 1:
                        continue

                chunk_id = f"{doc.filename}_p{page_num}_c{p_idx}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        text=text_segment.strip(),
                        doc_name=doc.filename,
                        file_path=doc.file_path,
                        page_num=page_num,
                        chunk_index=global_chunk_idx,
                        metadata={
                            "title": doc.metadata.get("title", doc.filename),
                            "word_count": len(text_segment.split()),
                        },
                    )
                )
                global_chunk_idx += 1

        return chunks

    def _chunk_page_text(self, text: str) -> List[str]:
        # Split into paragraphs first
        paragraphs = re.split(r'\n{2,}', text)
        result_chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If single paragraph is larger than chunk_size, split by sentences
            if len(para) > self.chunk_size:
                sentences = re.split(r'(?<=[.?!])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            result_chunks.append(current_chunk)
                            # Apply overlap from the tail of current_chunk
                            overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                            current_chunk = f"{overlap_text} {sentence}".strip()
                        else:
                            # Sentence itself is longer than chunk_size, hard break
                            for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                                result_chunks.append(sentence[i:i + self.chunk_size])
                            current_chunk = ""
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk = f"{current_chunk}\n\n{para}"
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        result_chunks.append(current_chunk)
                        overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                        current_chunk = f"{overlap_text}\n\n{para}".strip()
                    else:
                        result_chunk = para
                        result_chunks.append(result_chunk)
                        current_chunk = ""

        if current_chunk and current_chunk.strip():
            result_chunks.append(current_chunk.strip())

        return result_chunks
