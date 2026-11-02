"""
rag_engine.py
Advanced Academic PDF RAG (Retrieval-Augmented Generation) Engine.
Features:
- Accurate PDF extraction with page-level tracking via pypdf
- Semantic paragraph chunking with sliding window overlap
- Hybrid Retrieval: BM25 keyword search + Vectorized Numpy TF-IDF (Unigram + Bigram) + Reciprocal Rank Fusion (RRF)
- Dual Generation Engine:
    1. Google Gemini Generative AI (gemini-2.5-flash) with strict academic grounding
    2. Zero-key Smart Synthesizer fallback (works 100% offline out-of-the-box)
- Academic Agent Features: Flashcard Generator, Practice Exam Quiz Generator, Executive Notes Summary
"""

import os
import re
import math
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pypdf import PdfReader
import numpy as np

# Optional Google GenAI integration
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        doc_name: str,
        page: int,
        text: str,
        section: str = ""
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.doc_name = doc_name
        self.page = page
        self.text = text.strip()
        self.section = section
        self.token_count = len(self.text.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "doc_name": self.doc_name,
            "page": self.page,
            "text": self.text,
            "section": self.section,
            "token_count": self.token_count,
        }


class BM25Index:
    """In-memory BM25 index for exact academic keyword retrieval."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lens: List[int] = []
        self.doc_freqs: Dict[str, int] = {}
        self.inverted_index: Dict[str, Dict[int, int]] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\-\.\^]{2,}\b", text.lower())

    def fit(self, documents: List[str]):
        self.corpus_size = len(documents)
        if self.corpus_size == 0:
            return
        self.doc_lens = []
        self.doc_freqs = {}
        self.inverted_index = {}
        total_len = 0

        for doc_idx, doc in enumerate(documents):
            tokens = self._tokenize(doc)
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len

            term_counts: Dict[str, int] = {}
            for token in tokens:
                term_counts[token] = term_counts.get(token, 0) + 1

            for token, count in term_counts.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = {}
                    self.doc_freqs[token] = 0
                self.inverted_index[token][doc_idx] = count
                self.doc_freqs[token] += 1

        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 1.0

    def get_scores(self, query: str) -> np.ndarray:
        scores = np.zeros(self.corpus_size, dtype=np.float32)
        if self.corpus_size == 0:
            return scores

        query_tokens = self._tokenize(query)
        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            df = self.doc_freqs[token]
            idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
            idf = max(idf, 0.05)

            for doc_idx, tf in self.inverted_index[token].items():
                doc_len = self.doc_lens[doc_idx]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                score = idf * (tf * (self.k1 + 1.0)) / denom
                scores[doc_idx] += score

        return scores


class NumpyTFIDF:
    """High-speed vectorized TF-IDF vectorizer with unigram+bigram support and cosine scoring."""
    def __init__(self, max_features: int = 6000):
        self.max_features = max_features
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.doc_vectors: np.ndarray = np.array([])

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\-\.\^]{2,}\b", text.lower())
        tokens = list(words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")
        return tokens

    def fit_transform(self, documents: List[str]) -> np.ndarray:
        if not documents:
            self.vocabulary = {}
            self.idf = np.array([])
            self.doc_vectors = np.array([])
            return np.zeros((0, 0))

        doc_tokens = [self._tokenize(doc) for doc in documents]
        df: Dict[str, int] = {}
        for tokens in doc_tokens:
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        sorted_terms = sorted(df.keys(), key=lambda t: df[t], reverse=True)[:self.max_features]
        self.vocabulary = {term: idx for idx, term in enumerate(sorted_terms)}
        V = len(self.vocabulary)
        N = len(documents)

        self.idf = np.zeros(V, dtype=np.float32)
        for term, idx in self.vocabulary.items():
            self.idf[idx] = math.log((1.0 + N) / (1.0 + df[term])) + 1.0

        self.doc_vectors = np.zeros((N, V), dtype=np.float32)
        for doc_idx, tokens in enumerate(doc_tokens):
            for t in tokens:
                if t in self.vocabulary:
                    self.doc_vectors[doc_idx, self.vocabulary[t]] += 1

            nonzero = self.doc_vectors[doc_idx] > 0
            if np.any(nonzero):
                self.doc_vectors[doc_idx, nonzero] = 1.0 + np.log(self.doc_vectors[doc_idx, nonzero])
                self.doc_vectors[doc_idx] *= self.idf
                norm = np.linalg.norm(self.doc_vectors[doc_idx])
                if norm > 0:
                    self.doc_vectors[doc_idx] /= norm

        return self.doc_vectors

    def similarity(self, query: str) -> np.ndarray:
        N = len(self.doc_vectors)
        if N == 0 or len(self.vocabulary) == 0:
            return np.zeros(0, dtype=np.float32)

        V = len(self.vocabulary)
        q_vec = np.zeros(V, dtype=np.float32)
        for t in self._tokenize(query):
            if t in self.vocabulary:
                q_vec[self.vocabulary[t]] += 1

        nonzero = q_vec > 0
        if np.any(nonzero):
            q_vec[nonzero] = 1.0 + np.log(q_vec[nonzero])
            q_vec *= self.idf
            norm = np.linalg.norm(q_vec)
            if norm > 0:
                q_vec /= norm
            return np.dot(self.doc_vectors, q_vec)

        return np.zeros(N, dtype=np.float32)


class AcademicRAGEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[DocumentChunk] = []
        self.tfidf = NumpyTFIDF()
        self.bm25_index = BM25Index()
        self.gemini_client = None
        self._init_gemini()

    def set_api_key(self, api_key: str):
        self.api_key = api_key.strip()
        self._init_gemini()

    def _init_gemini(self):
        if GEMINI_AVAILABLE and self.api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[AcademicRAGEngine] Warning: Failed to init Gemini client: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None

    def add_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Parses PDF bytes, extracts text with exact page numbers, chunks, and indexes."""
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        doc_id = str(uuid.uuid4())[:8]
        total_pages = len(reader.pages)

        extracted_chunks: List[DocumentChunk] = []
        total_words = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            cleaned = self._clean_text(raw_text)
            if not cleaned.strip():
                continue

            page_words = len(cleaned.split())
            total_words += page_words

            page_chunks = self._chunk_page(cleaned, doc_id, filename, page_num)
            extracted_chunks.extend(page_chunks)

        if not extracted_chunks:
            extracted_chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc_id}_p1_c0",
                    doc_id=doc_id,
                    doc_name=filename,
                    page=1,
                    text="Document text extraction yielded no readable characters.",
                    section="General"
                )
            )

        self.documents[doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "total_pages": total_pages,
            "total_chunks": len(extracted_chunks),
            "total_words": total_words,
        }

        self.chunks.extend(extracted_chunks)
        self._rebuild_indices()

        return {
            "doc_id": doc_id,
            "filename": filename,
            "total_pages": total_pages,
            "total_chunks": len(extracted_chunks),
            "total_words": total_words,
        }

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _chunk_page(
        self,
        page_text: str,
        doc_id: str,
        filename: str,
        page_num: int,
        target_chunk_size: int = 1200,
        overlap: int = 250
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        paragraphs = re.split(r"\n\s*\n", page_text)
        current_section = f"Page {page_num}"
        current_buffer = ""

        chunk_counter = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) < 100 and (
                re.match(r"^(section|module|chapter|\d+(\.\d+)*)\b", para, re.IGNORECASE)
                or para.isupper()
            ):
                current_section = para

            if len(current_buffer) + len(para) <= target_chunk_size:
                current_buffer += ("\n\n" if current_buffer else "") + para
            else:
                if current_buffer:
                    chunk_id = f"{doc_id}_p{page_num}_c{chunk_counter}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=doc_id,
                            doc_name=filename,
                            page=page_num,
                            text=current_buffer,
                            section=current_section
                        )
                    )
                    chunk_counter += 1

                    overlap_text = current_buffer[-overlap:] if len(current_buffer) > overlap else ""
                    current_buffer = (overlap_text + "\n\n" + para).strip()
                else:
                    for i in range(0, len(para), target_chunk_size - overlap):
                        sub_text = para[i:i + target_chunk_size]
                        chunk_id = f"{doc_id}_p{page_num}_c{chunk_counter}"
                        chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                doc_id=doc_id,
                                doc_name=filename,
                                page=page_num,
                                text=sub_text,
                                section=current_section
                            )
                        )
                        chunk_counter += 1
                    current_buffer = ""

        if current_buffer.strip():
            chunk_id = f"{doc_id}_p{page_num}_c{chunk_counter}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    doc_name=filename,
                    page=page_num,
                    text=current_buffer,
                    section=current_section
                )
            )

        return chunks

    def _rebuild_indices(self):
        if not self.chunks:
            self.tfidf = NumpyTFIDF()
            self.bm25_index = BM25Index()
            return

        corpus = [c.text for c in self.chunks]
        self.bm25_index.fit(corpus)
        self.tfidf.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:
        if not self.chunks:
            return []

        # 1. BM25 Scores
        bm25_scores = self.bm25_index.get_scores(query)
        bm25_ranked = np.argsort(-bm25_scores)

        # 2. Vectorized TF-IDF Cosine Scores
        tfidf_scores = self.tfidf.similarity(query)
        tfidf_ranked = np.argsort(-tfidf_scores)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores = np.zeros(len(self.chunks), dtype=np.float32)
        k_rrf = 60.0

        for rank, doc_idx in enumerate(bm25_ranked[:top_k * 4]):
            if bm25_scores[doc_idx] > 0:
                rrf_scores[doc_idx] += 1.0 / (k_rrf + rank + 1)

        for rank, doc_idx in enumerate(tfidf_ranked[:top_k * 4]):
            if tfidf_scores[doc_idx] > 0:
                rrf_scores[doc_idx] += 1.0 / (k_rrf + rank + 1)

        best_indices = np.argsort(-rrf_scores)[:top_k]

        results = []
        max_score = rrf_scores[best_indices[0]] if len(best_indices) > 0 and rrf_scores[best_indices[0]] > 0 else 1.0

        for idx in best_indices:
            normalized_score = float(rrf_scores[idx] / max_score)
            results.append((self.chunks[idx], round(normalized_score, 3)))

        return results

    def query(self, user_question: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        if not self.chunks:
            return {
                "answer": "No academic notes have been uploaded yet. Please upload a PDF study guide, textbook, or lecture notes first, or click **Load Sample Notes** to test the system!",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [
                    "What topics are covered in the sample notes?",
                    "How do I upload a multi-page lecture PDF?",
                    "How does citation attribution work?"
                ]
            }

        retrieved = self.retrieve(user_question, top_k=4)
        if not retrieved:
            return {
                "answer": "Could not find relevant passages in the uploaded notes for this query. Try rephrasing or asking about a topic covered in your document.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": []
            }

        citations = []
        context_blocks = []
        for chunk, score in retrieved:
            citations.append({
                "chunk_id": chunk.chunk_id,
                "doc_name": chunk.doc_name,
                "page": chunk.page,
                "section": chunk.section,
                "relevance": round(score * 100, 1),
                "snippet": chunk.text[:220] + "..." if len(chunk.text) > 220 else chunk.text
            })
            context_blocks.append(
                f"[Source: {chunk.doc_name} | Page: {chunk.page} | Section: {chunk.section}]\n{chunk.text}"
            )

        full_context = "\n\n---\n\n".join(context_blocks)

        if self.gemini_client is not None:
            try:
                return self._generate_gemini_answer(user_question, full_context, citations, history)
            except Exception as e:
                print(f"[AcademicRAGEngine] Gemini API error: {e}. Falling back to smart offline synthesizer.")
                return self._generate_local_answer(user_question, retrieved, citations)
        else:
            return self._generate_local_answer(user_question, retrieved, citations)

    def _generate_gemini_answer(
        self,
        question: str,
        context: str,
        citations: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        system_instruction = (
            "You are ScholarMind AI, an elite academic research assistant and study companion. "
            "Your goal is to answer the student's questions accurately, thoroughly, and strictly based "
            "on the provided academic note excerpts. "
            "Guidelines:\n"
            "1. Ground every claim directly in the provided context.\n"
            "2. Cite specific source pages inline using format: `[Page X]` or `(Source: doc.pdf, Page X)`.\n"
            "3. Format formulas, algorithms, Big-O notations, and equations with clear Markdown or LaTeX.\n"
            "4. Organize explanations with clean bullet points, bold key terms, and concise structural headers.\n"
            "5. If a question cannot be answered from the notes, acknowledge what IS mentioned and clarify what is missing.\n"
            "6. Conclude with 3 logical, high-yield academic follow-up questions formatted at the very end on a new line starting with: 'FOLLOW_UP: q1 | q2 | q3'"
        )

        history_prompt = ""
        if history:
            recent_turns = history[-4:]
            for h in recent_turns:
                role = "Student" if h.get("role") == "user" else "Assistant"
                history_prompt += f"{role}: {h.get('content', '')}\n"

        prompt = (
            f"{system_instruction}\n\n"
            f"=== ACADEMIC NOTES CONTEXT ===\n"
            f"{context}\n\n"
            f"=== CONVERSATION HISTORY ===\n"
            f"{history_prompt or 'None'}\n\n"
            f"=== STUDENT QUESTION ===\n"
            f"{question}\n\n"
            f"Provide a structured, beautifully formatted academic response with page citations and 3 follow-up study questions:"
        )

        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw_text = response.text or ""

        follow_ups = []
        if "FOLLOW_UP:" in raw_text:
            parts = raw_text.split("FOLLOW_UP:")
            answer_text = parts[0].strip()
            fu_line = parts[1].strip()
            follow_ups = [q.strip() for q in fu_line.split("|") if q.strip()]
        else:
            answer_text = raw_text.strip()
            follow_ups = self._extract_default_followups(question)

        return {
            "answer": answer_text,
            "citations": citations,
            "confidence": 0.95,
            "follow_up_questions": follow_ups[:3],
            "mode": "gemini-2.5-flash"
        }

    def _generate_local_answer(
        self,
        question: str,
        retrieved: List[Tuple[DocumentChunk, float]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        top_chunk, top_score = retrieved[0]
        q_lower = question.lower()

        q_words = set(re.findall(r"\b\w{3,}\b", q_lower))
        stop_words = {"what", "when", "where", "which", "who", "whom", "this", "that", "these", "those", "explain", "describe", "tell", "show"}
        keywords = [w for w in q_words if w not in stop_words]

        scored_sentences = []
        for chunk, score in retrieved:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) < 20:
                    continue
                s_lower = s_clean.lower()
                matches = sum(1 for kw in keywords if kw in s_lower)
                if any(verb in s_lower for verb in ["is ", "are ", "refers to", "defined as", "composed of", "occurs when", "condition"]):
                    matches += 1.5
                if matches > 0:
                    scored_sentences.append((s_clean, matches * score, chunk.page, chunk.doc_name))

        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = scored_sentences[:6]

        paragraphs = []
        paragraphs.append(
            f"Based on your uploaded academic notes in **{top_chunk.doc_name}** (`Page {top_chunk.page}`), "
            f"here is the synthesized answer for: **\"{question}\"**:"
        )

        if top_sentences:
            paragraphs.append("\n### 📖 Core Findings & Theoretical Concepts\n")
            seen_texts = set()
            for s, _, page, doc in top_sentences:
                clean_s = s.replace("\n", " ").strip()
                if clean_s in seen_texts:
                    continue
                seen_texts.add(clean_s)
                paragraphs.append(f"- **[Page {page}]**: {clean_s}")

        paragraphs.append("\n### 🔍 Verbatim Source Excerpt\n")
        paragraphs.append(f"> \"{top_chunk.text.replace(chr(10), ' ')}\"")
        paragraphs.append(f"\n*(Source: {top_chunk.doc_name}, Page {top_chunk.page}, {top_chunk.section})*")

        paragraphs.append(
            "\n\n> 💡 **Tip:** Add a free Google Gemini API key in **Settings** (top right) to enable conversational LLM explanations and interactive problem solving."
        )

        follow_ups = self._extract_default_followups(question)

        return {
            "answer": "\n".join(paragraphs),
            "citations": citations,
            "confidence": round(float(top_score), 2),
            "follow_up_questions": follow_ups[:3],
            "mode": "offline-hybrid-synthesizer"
        }

    def _extract_default_followups(self, query: str) -> List[str]:
        q = query.lower()
        if "deadlock" in q or "coffman" in q:
            return [
                "How does Coffman's circular wait condition differ from hold and wait?",
                "What page replacement algorithms help avoid thrashing?",
                "How does the banker's algorithm prevent deadlocks?"
            ]
        elif "dijkstra" in q or "shortest path" in q or "bellman" in q:
            return [
                "Why does Dijkstra's algorithm fail on graphs with negative edge weights?",
                "What is the space complexity difference between Dijkstra and Bellman-Ford?",
                "How does A* search improve upon Dijkstra's heuristic?"
            ]
        elif "gradient" in q or "adam" in q or "loss" in q:
            return [
                "What are the benefits of Mini-Batch Gradient Descent over full Batch GD?",
                "How does the Adam optimizer calculate exponential moving averages?",
                "What is the formula for cross-entropy loss in classification?"
            ]
        elif "transformer" in q or "attention" in q or "rag" in q:
            return [
                "Why is the dot-product divided by sqrt(d_k) in Scaled Dot-Product Attention?",
                "What are the three main phases of a modern RAG pipeline?",
                "How do Faithfulness and Answer Relevance evaluate RAG systems?"
            ]
        else:
            return [
                "Can you provide a step-by-step example from the notes?",
                "What are the key formulas or theorems associated with this topic?",
                "Generate an exam prep question based on this section."
            ]

    # --- Academic Study Agent Features ---

    def get_suggested_questions(self, doc_id: Optional[str] = None, count: int = 4) -> List[str]:
        """Generates suggested starter questions derived strictly from the uploaded document's content."""
        target_chunks = [c for c in self.chunks if c.doc_id == doc_id] if doc_id else self.chunks
        if not target_chunks:
            return [
                "What topics are covered in the uploaded notes?",
                "Can you summarize the main findings?",
                "What are the key definitions and formulas?"
            ]

        suggested = []

        # 1. Extract from section titles
        for chunk in target_chunks:
            if chunk.section and not chunk.section.startswith("Page ") and len(chunk.section) > 4:
                clean_sec = re.sub(r"^(section|module|chapter|\d+(\.\d+)*)\s*[:.\-]?\s*", "", chunk.section, flags=re.IGNORECASE).strip()
                if clean_sec and len(clean_sec) > 3:
                    q = f"Explain {clean_sec} based on the notes."
                    if q not in suggested:
                        suggested.append(q)

        # 2. Extract from definition patterns
        for chunk in target_chunks:
            matches = re.findall(r"([A-Z][a-zA-Z0-9\s\-_]{2,30})\s+(?:is defined as|refers to|is an?|are)\b", chunk.text)
            for term in matches:
                clean_term = term.strip()
                if len(clean_term) > 3 and clean_term not in ["This", "That", "These", "Those", "There", "Here"]:
                    q = f"What is {clean_term} according to Page {chunk.page}?"
                    if q not in suggested:
                        suggested.append(q)

        # 3. Extract formulas or algorithms
        for chunk in target_chunks:
            f_matches = re.findall(r"(?:[Ff]ormula|[Ee]quation|[Ll]aw|[Aa]lgorithm)\s*(?:\d+)?\s*(?:\(([^)]+)\)|:\s*([A-Za-z\s]+))", chunk.text)
            for m in f_matches:
                name = m[0] or m[1]
                if name and len(name.strip()) > 3:
                    q = f"How does the {name.strip()} work in this document?"
                    if q not in suggested:
                        suggested.append(q)

        # 4. Fallback if fewer than count
        if len(suggested) < count:
            for chunk in target_chunks[:count]:
                q = f"What are the key points in {chunk.doc_name} on Page {chunk.page}?"
                if q not in suggested:
                    suggested.append(q)

        return suggested[:count]

    def generate_flashcards(self, count: int = 8, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        target_chunks = [c for c in self.chunks if c.doc_id == doc_id] if doc_id else self.chunks
        if not target_chunks:
            return []

        if self.gemini_client:
            try:
                sample_text = "\n\n".join([f"Page {c.page}: {c.text}" for c in target_chunks[:8]])
                prompt = (
                    "You are an academic flashcard generator. From the following academic notes, extract "
                    f"{count} high-yield study flashcards for exam preparation.\n"
                    "Format each flashcard strictly as JSON array with objects containing:\n"
                    "- 'front': Concept, Term, or Question\n"
                    "- 'back': Concise definition, explanation, or formula\n"
                    "- 'category': Subject or module name\n"
                    "- 'difficulty': 'Easy', 'Medium', or 'Hard'\n"
                    "- 'page': Int page number\n\n"
                    f"Notes:\n{sample_text}\n\n"
                    "Output ONLY valid JSON without markdown quotes."
                )
                res = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                import json
                clean_json = re.sub(r"^```json\s*|\s*```$", "", res.text.strip())
                data = json.loads(clean_json)
                for idx, item in enumerate(data):
                    item["id"] = idx + 1
                return data
            except Exception as e:
                print(f"[AcademicRAGEngine] Flashcard LLM generation failed: {e}. Using rule extractor.")

        cards = []
        card_id = 1
        patterns = [
            (r"([A-Z][a-zA-Z\s]{3,30})\s*(?:is defined as|refers to|is an?|are)\s+([^.]{20,180}\.)", "Definition"),
            (r"([A-Z][a-zA-Z\s]{3,30})\s*Conditions?:\s*([^.]{20,200}\.)", "Condition"),
            (r"(Formula|Law|Theorem)\s*(?:\d+)?\s*\(([^)]+)\):\s*([^.]{15,180}\.)", "Formula")
        ]

        for chunk in target_chunks:
            for pat, cat in patterns:
                matches = re.findall(pat, chunk.text)
                for m in matches:
                    if len(m) >= 2:
                        term = m[0].strip()
                        defn = m[1].strip() if len(m) == 2 else f"{m[1]}: {m[2]}"
                        if len(term) < 5 or len(defn) < 15:
                            continue
                        cards.append({
                            "id": card_id,
                            "front": f"What is {term}?",
                            "back": defn,
                            "category": cat,
                            "difficulty": "Medium" if len(defn) > 60 else "Easy",
                            "page": chunk.page,
                            "doc_name": chunk.doc_name
                        })
                        card_id += 1
                        if len(cards) >= count:
                            return cards

        if len(cards) < 4:
            for idx, chunk in enumerate(target_chunks[:count]):
                first_sentence = chunk.text.split(".")[0].strip() + "."
                cards.append({
                    "id": card_id,
                    "front": f"Key concept from {chunk.section or f'Page {chunk.page}'}",
                    "back": first_sentence,
                    "category": "Lecture Review",
                    "difficulty": "Medium",
                    "page": chunk.page,
                    "doc_name": chunk.doc_name
                })
                card_id += 1

        return cards[:count]

    def generate_quiz(self, count: int = 5, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        target_chunks = [c for c in self.chunks if c.doc_id == doc_id] if doc_id else self.chunks
        if not target_chunks:
            return []

        # 1. If Gemini LLM is active, prompt with the actual text of target_chunks
        if self.gemini_client:
            try:
                sample_text = "\n\n".join([f"[{c.doc_name} | Page {c.page}] {c.text}" for c in target_chunks[:8]])
                prompt = (
                    f"Create {count} university-level exam Multiple Choice Questions (MCQs) strictly based on the following uploaded academic notes.\n"
                    "Requirements:\n"
                    "1. Questions must be derived directly from the provided notes content.\n"
                    "2. Exactly 4 plausible choices per question.\n"
                    "3. Cite the exact page number from the notes.\n"
                    "Output ONLY valid JSON as a list of objects with:\n"
                    "- 'id': int\n"
                    "- 'question': string\n"
                    "- 'options': list of 4 plausible answer strings\n"
                    "- 'correct_index': int (0 to 3 index of the correct answer)\n"
                    "- 'explanation': string explaining why this answer is correct based on the notes\n"
                    "- 'page': int page number\n\n"
                    f"Uploaded Academic Notes:\n{sample_text}"
                )
                res = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                import json
                clean_json = re.sub(r"^```json\s*|\s*```$", "", res.text.strip())
                return json.loads(clean_json)
            except Exception as e:
                print(f"[AcademicRAGEngine] Quiz LLM generation error: {e}. Falling back to dynamic extractor.")

        # 2. DYNAMIC OFFLINE EXTRACTOR: Extracts real MCQs strictly from the uploaded document's chunks
        import random
        rng = random.Random(42)

        fact_patterns = [
            r"([A-Z][a-zA-Z0-9\s\-_]{2,35})\s+(?:is defined as|refers to|is an?|are)\s+([^.?!;\n]{20,160})[.?!;]",
            r"([A-Z][a-zA-Z0-9\s\-_]{2,35})\s+(?:consists of|includes|involves|functions by)\s+([^.?!;\n]{20,160})[.?!;]",
            r"([A-Z][a-zA-Z0-9\s\-_]{2,30})\s*(?:Condition|Law|Rule|Theorem|Method)?\s*:\s*([^.?!;\n]{20,160})[.?!;]",
            r"([A-Z][a-zA-Z0-9\s\-_]{2,35})\s+(?:occurs when|arises when)\s+([^.?!;\n]{20,160})[.?!;]"
        ]

        extracted_facts = []
        all_subjects = []
        all_predicates = []

        for chunk in target_chunks:
            for pat in fact_patterns:
                matches = re.findall(pat, chunk.text)
                for subj, pred in matches:
                    subj = subj.strip()
                    pred = pred.strip()
                    if (3 <= len(subj.split()) <= 6) or (len(subj) >= 4 and subj[0].isupper()):
                        if len(pred) >= 20 and not pred.lower().startswith("shown in"):
                            extracted_facts.append({
                                "subject": subj,
                                "predicate": pred,
                                "page": chunk.page,
                                "doc_name": chunk.doc_name
                            })
                            all_subjects.append(subj)
                            all_predicates.append(pred)

        quiz_items = []
        for fact in extracted_facts:
            if len(quiz_items) >= count:
                break

            subj = fact["subject"]
            pred = fact["predicate"]
            page = fact["page"]
            doc_name = fact["doc_name"]

            other_preds = [p for p in all_predicates if p != pred and len(p) > 15]
            if len(other_preds) >= 3:
                distractors = rng.sample(other_preds, 3)
                options = [pred] + distractors
                rng.shuffle(options)
                correct_idx = options.index(pred)
                q_text = f"According to the notes ({doc_name}, Page {page}), what is {subj}?"
                exp_text = f"As noted on Page {page}: '{subj} is {pred}.'"
            else:
                other_subjs = [s for s in all_subjects if s != subj]
                if len(other_subjs) >= 3:
                    distractors = rng.sample(other_subjs, 3)
                    options = [subj] + distractors
                    rng.shuffle(options)
                    correct_idx = options.index(subj)
                    q_text = f"Which concept in {doc_name} (Page {page}) is described as: \"{pred[:90]}...\"?"
                    exp_text = f"'{subj}' is the concept described on Page {page}."
                else:
                    continue

            quiz_items.append({
                "id": len(quiz_items) + 1,
                "question": q_text,
                "options": options,
                "correct_index": correct_idx,
                "explanation": exp_text,
                "page": page,
                "doc_name": doc_name
            })

        # 3. Sentence-level completion if facts are sparse
        if len(quiz_items) < count:
            for chunk in target_chunks:
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk.text) if 35 < len(s.strip()) < 140]
                for sentence in sentences:
                    if len(quiz_items) >= count:
                        break
                    words = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{3,}\b", sentence)
                    if words and words[0] not in ["This", "That", "There", "When", "What", "Here", "Note", "Also", "Module", "Page"]:
                        target_word = words[0]
                        masked = sentence.replace(target_word, "________", 1)
                        other_words = list(set([w for c in target_chunks for w in re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{3,}\b", c.text) if w != target_word and w not in ["This", "That", "There", "When", "What", "Here", "Note", "Also", "Module", "Page"]]))
                        if len(other_words) >= 3:
                            distractors = rng.sample(other_words, 3)
                            options = [target_word] + distractors
                            rng.shuffle(options)
                            quiz_items.append({
                                "id": len(quiz_items) + 1,
                                "question": f"Based on {chunk.doc_name} (Page {chunk.page}), fill in the blank: \"{masked}\"",
                                "options": options,
                                "correct_index": options.index(target_word),
                                "explanation": f"The full statement from Page {chunk.page} is: \"{sentence}\"",
                                "page": chunk.page,
                                "doc_name": chunk.doc_name
                            })

        return quiz_items[:count]

    def generate_summary(self) -> Dict[str, Any]:
        if not self.chunks:
            return {
                "title": "No Notes Uploaded",
                "overview": "Upload your PDF notes to generate an executive study guide.",
                "modules": [],
                "formulas": []
            }

        total_pages = sum(d.get("total_pages", 0) for d in self.documents.values())
        total_words = sum(d.get("total_words", 0) for d in self.documents.values())
        est_read_time = math.ceil(total_words / 200)

        formulas = []
        for chunk in self.chunks:
            f_matches = re.findall(r"(?:[Ff]ormula|[Ee]quation|[Ll]aw)\s*(?:\d+)?\s*(?:\([^)]+\))?:\s*([^.\n]+)", chunk.text)
            for fm in f_matches:
                if len(fm) > 10:
                    formulas.append({
                        "name": fm.split("=")[0].strip() if "=" in fm else "Key Relationship",
                        "formula": fm.strip(),
                        "page": chunk.page
                    })

        modules = []
        seen_sections = set()
        for chunk in self.chunks:
            if chunk.section and chunk.section not in seen_sections and len(chunk.section) > 3:
                seen_sections.add(chunk.section)
                preview = chunk.text[:180].replace("\n", " ").strip() + "..."
                modules.append({
                    "title": chunk.section,
                    "page": chunk.page,
                    "doc_name": chunk.doc_name,
                    "summary": preview
                })

        return {
            "title": "Academic Executive Summary & Study Guide",
            "stats": {
                "total_documents": len(self.documents),
                "total_pages": total_pages,
                "total_chunks": len(self.chunks),
                "total_words": total_words,
                "est_read_time_minutes": est_read_time
            },
            "overview": (
                f"Synthesized from {len(self.documents)} academic document(s) encompassing {total_pages} pages "
                f"and {len(self.chunks)} semantic chunks. Designed for rapid exam review and high-yield retention."
            ),
            "modules": modules[:8],
            "formulas": formulas[:6]
        }

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.chunks = [c for c in self.chunks if c.doc_id != doc_id]
            self._rebuild_indices()
            return True
        return False

    def clear_all(self):
        self.documents.clear()
        self.chunks.clear()
        self._rebuild_indices()
