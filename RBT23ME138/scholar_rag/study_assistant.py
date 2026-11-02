import re
from typing import List, Dict, Any, Optional
from .vector_store import vector_index
from .llm_engine import llm_engine, OfflineSynthesizer
from .text_splitter import TextChunk


class StudyAssistant:
    """Specialized academic learning tools: summaries, quizzes, and flashcards."""

    @staticmethod
    def generate_summary(doc_name: Optional[str] = None) -> str:
        """Generates structured revision summary from notes."""
        if not vector_index.chunks:
            return "No documents uploaded. Please upload a PDF first with `/upload`."

        # Filter chunks if specific document requested
        if doc_name:
            chunks = [c for c in vector_index.chunks if doc_name.lower() in c.doc_name.lower()]
            if not chunks:
                return f"Document '{doc_name}' not found in index."
        else:
            chunks = vector_index.chunks[:12]  # representative sample

        target_name = doc_name or "All Uploaded Notes"
        query = f"Provide a comprehensive academic summary of {target_name}, including core definitions, key principles, formulas, and exam takeaways."

        # Search top relevant chunks across the document
        top_chunks = vector_index.search("overview introduction definitions key concepts formulas summary", top_k=6)
        if not top_chunks and chunks:
            top_chunks = [(c, 1.0) for c in chunks[:6]]

        prov = llm_engine.get_active_provider()
        if prov != "offline":
            prompt = f"Summarize the following academic notes systematically. Structure your summary with:\n1. Core Subject Overview\n2. Key Terminology & Definitions\n3. Important Principles / Formulas\n4. High-Yield Exam Review Takeaways\nInclude page numbers where each topic was found."
            return llm_engine.ask(prompt, top_chunks)
        else:
            # Offline summary generation
            lines = [
                f"# Academic Summary: {target_name}\n",
                "> Generated via ScholarRAG Offline Synthesis. For generative summarization, connect an LLM.\n",
                "## Key Sections & Concepts Identified:",
            ]
            seen_topics = set()
            for chunk, _ in top_chunks:
                for line in chunk.text.split("\n"):
                    line = line.strip()
                    if 15 < len(line) < 120 and (line.endswith(":") or line.startswith(("#", "-", "*", "1.", "2."))):
                        clean_topic = re.sub(r'^[#\-*0-9.]+\s*', '', line)
                        if clean_topic not in seen_topics:
                            seen_topics.add(clean_topic)
                            lines.append(f"- **{clean_topic}** `[{chunk.doc_name}, p.{chunk.page_num}]`")
                            if len(seen_topics) >= 8:
                                break

            lines.append("\n## Core Notes Excerpts:")
            for chunk, _ in top_chunks[:3]:
                lines.append(f"\n### From {chunk.doc_name} (Page {chunk.page_num}):")
                lines.append(f"> {chunk.text[:400]}...")

            return "\n".join(lines)

    @staticmethod
    def generate_quiz(num_questions: int = 4, topic: Optional[str] = None) -> str:
        """Generates practice exam questions based on the uploaded notes."""
        if not vector_index.chunks:
            return "No documents uploaded. Please upload a PDF first with `/upload`."

        search_query = topic if topic else "concept theorem definition problem calculation example"
        top_chunks = vector_index.search(search_query, top_k=6)
        if not top_chunks:
            top_chunks = [(c, 1.0) for c in vector_index.chunks[:6]]

        prov = llm_engine.get_active_provider()
        if prov != "offline":
            prompt = (
                f"Generate a {num_questions}-question academic practice quiz based strictly on the provided notes.\n"
                f"For each question:\n"
                f"- State Question number and type (Multiple Choice or Conceptual)\n"
                f"- List options A, B, C, D if multiple choice\n"
                f"- Include an 'ANSWER & EXPLANATION' section with the exact document page reference citing the notes."
            )
            return llm_engine.ask(prompt, top_chunks)
        else:
            # Offline Quiz generator
            lines = [
                f"# Academic Practice Quiz ({num_questions} Questions)\n",
                "> Generated from your uploaded notes. Practice answering these to test your knowledge!\n",
            ]
            q_num = 1
            for chunk, _ in top_chunks:
                # Find sentences with definitions or statements
                sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', chunk.text) if len(s.strip()) > 40]
                if sentences and q_num <= num_questions:
                    target_s = sentences[0]
                    lines.append(f"### Question {q_num}:")
                    lines.append(f"Based on the notes on **Page {chunk.page_num}** of `{chunk.doc_name}`:")
                    lines.append(f"*Explain or evaluate the following concept:*")
                    lines.append(f"> \"{target_s}\"\n")
                    lines.append(f"<details><summary><b>Reveal Context & Page Reference</b></summary>")
                    lines.append(f"Source: `{chunk.doc_name}`, Page {chunk.page_num}\n")
                    lines.append(f"Supporting Context: {chunk.text[:250]}...\n</details>\n")
                    q_num += 1

            return "\n".join(lines)

    @staticmethod
    def generate_flashcards(count: int = 5) -> List[Dict[str, str]]:
        """Extracts flashcards (Term -> Definition) from notes."""
        if not vector_index.chunks:
            return []

        flashcards = []
        # Pattern to look for definitions: 'X is defined as...', 'X refers to...', 'X: ...'
        def_patterns = [
            r'([A-Z][a-zA-Z\s]{2,30})\s+(?:is defined as|refers to|is a|means)\s+([^.\n]{20,150})',
            r'([A-Z][a-zA-Z0-9_\s]{2,25}):\s+([^.\n]{20,150})',
        ]

        for chunk in vector_index.chunks:
            for pattern in def_patterns:
                matches = re.findall(pattern, chunk.text)
                for term, definition in matches:
                    term = term.strip()
                    definition = definition.strip()
                    if len(term.split()) <= 4 and len(definition) > 25:
                        flashcards.append({
                            "term": term,
                            "definition": definition,
                            "source": f"{chunk.doc_name} (p.{chunk.page_num})",
                        })
                        if len(flashcards) >= count:
                            return flashcards

        # If not enough regex matches, extract from headings / sentences
        for chunk in vector_index.chunks:
            paras = [p.strip() for p in chunk.text.split("\n") if p.strip()]
            for p in paras:
                if ":" in p and len(p.split(":")[0].split()) <= 4:
                    parts = p.split(":", 1)
                    flashcards.append({
                        "term": parts[0].strip(),
                        "definition": parts[1].strip(),
                        "source": f"{chunk.doc_name} (p.{chunk.page_num})",
                    })
                    if len(flashcards) >= count:
                        return flashcards

        return flashcards


study_assistant = StudyAssistant()
