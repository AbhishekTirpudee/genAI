import os
import re
from typing import List, Tuple, Generator, Optional
import requests

from .config import config
from .text_splitter import TextChunk

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AcademicPromptTemplates:
    SYSTEM_ACADEMIC = """You are ScholarBot, an expert academic tutor.
Answer the student's question accurately, concisely, and directly based ONLY on the provided notes.
Do NOT repeat the prompt or questions. Provide the direct factual answer with page citations (e.g. [p. 1])."""

    @staticmethod
    def build_rag_prompt(query: str, context_chunks: List[Tuple[TextChunk, float]]) -> str:
        context_parts = []
        for i, (chunk, score) in enumerate(context_chunks, 1):
            context_parts.append(
                f"--- EXCERPT {i} (Source: {chunk.doc_name}, Page: {chunk.page_num}) ---\n"
                f"{chunk.text}\n"
            )
        context_str = "\n".join(context_parts)

        prompt = f"""CONTEXT FROM NOTES:
{context_str}

QUESTION: {query}

INSTRUCTIONS:
Provide the direct, concise answer to the question using the context above. If not in the notes, state that clearly."""
        return prompt


class OfflineSynthesizer:
    """
    Direct answer extractor for academic notes.
    Extracts the exact factual answer without exercises, headers, or metadata clutter.
    """
    @staticmethod
    def is_question_or_exercise(text: str) -> bool:
        t = text.strip()
        if t.endswith("?"):
            return True
        # Common review questions in academic notes
        exercise_starters = [
            r'^(?:explain|describe|define|give|list|differentiate|compare|state|what is|how does)\b',
            r'^(?:exercise|question|review questions?|practice questions?|assignment)\b',
            r'^[0-9]+[.)]\s*(?:explain|give|what|describe|list)\b',
        ]
        for pattern in exercise_starters:
            if re.search(pattern, t, flags=re.IGNORECASE):
                return True
        return False

    @staticmethod
    def is_boilerplate(text: str) -> bool:
        t = text.lower()
        if "comprehensive academic lecture notes" in t:
            return True
        if "department of computer science" in t:
            return True
        if "sample academic notes:" in t and len(t.split()) < 8:
            return True
        return False

    @classmethod
    def synthesize(cls, query: str, chunks: List[Tuple[TextChunk, float]]) -> str:
        if not chunks:
            return "No relevant notes found for your question."

        q_lower = query.lower()
        q_tokens = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', q_lower))
        stop_words = {"what", "which", "where", "when", "how", "why", "the", "and", "explain", "describe", "define", "give", "notes", "with", "from"}
        keywords = [w for w in q_tokens if w not in stop_words]

        answers = []
        seen = set()

        for chunk, score in chunks:
            # Look through paragraphs and bullet points
            paragraphs = [p.strip() for p in re.split(r'\n{2,}|\n(?=[-*•]|\d+\.)', chunk.text) if p.strip()]
            for p in paragraphs:
                # Strip trailing practice/review question headers
                clean_p = re.sub(r'\b(?:practice|review)\s+questions?\b.*$', '', p, flags=re.IGNORECASE).strip()
                if len(clean_p) < 25 or cls.is_boilerplate(clean_p) or cls.is_question_or_exercise(clean_p):
                    continue

                p_lower = clean_p.lower()
                matches = sum(1 for kw in keywords if kw in p_lower)
                if matches > 0:
                    if clean_p not in seen:
                        seen.add(clean_p)
                        answers.append({
                            "text": clean_p,
                            "matches": matches,
                            "score": score,
                            "doc": chunk.doc_name,
                            "page": chunk.page_num,
                        })

        # If paragraphs were too broad, try individual sentences
        if not answers:
            for chunk, score in chunks:
                sentences = re.split(r'(?<=[.?!])\s+', chunk.text)
                for s in sentences:
                    s_clean = s.strip()
                    if len(s_clean) < 25 or cls.is_boilerplate(s_clean) or cls.is_question_or_exercise(s_clean):
                        continue
                    matches = sum(1 for kw in keywords if kw in s_clean.lower())
                    if matches > 0 and s_clean not in seen:
                        seen.add(s_clean)
                        answers.append({
                            "text": s_clean,
                            "matches": matches,
                            "score": score,
                            "doc": chunk.doc_name,
                            "page": chunk.page_num,
                        })

        if not answers:
            return f"The provided notes do not contain a clear answer for: '{query}'."

        # Sort by relevance and keyword matches
        answers.sort(key=lambda x: (x["matches"], x["score"]), reverse=True)

        # Assemble clean, direct answer
        top_answers = answers[:3]
        result_paragraphs = []
        for ans in top_answers:
            result_paragraphs.append(ans["text"])

        direct_answer = "\n\n".join(result_paragraphs)
        return direct_answer


class LLMEngine:
    """Unified LLM query engine supporting OpenAI, Groq, Ollama, and Offline mode."""

    def __init__(self):
        self.config = config

    def get_active_provider(self) -> str:
        prov = self.config.provider
        if prov == "openai" and not self.config.openai_api_key:
            return "offline"
        if prov == "groq" and not self.config.groq_api_key:
            return "offline"
        return prov

    def stream_answer(
        self, query: str, context_chunks: List[Tuple[TextChunk, float]]
    ) -> Generator[str, None, None]:
        prov = self.get_active_provider()

        if prov == "openai":
            prompt = AcademicPromptTemplates.build_rag_prompt(query, context_chunks)
            client = OpenAI(api_key=self.config.openai_api_key)
            response = client.chat.completions.create(
                model=self.config.model_name or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": AcademicPromptTemplates.SYSTEM_ACADEMIC},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        elif prov == "groq":
            prompt = AcademicPromptTemplates.build_rag_prompt(query, context_chunks)
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.config.groq_api_key,
            )
            response = client.chat.completions.create(
                model=self.config.model_name or "llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": AcademicPromptTemplates.SYSTEM_ACADEMIC},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        elif prov == "ollama":
            prompt = AcademicPromptTemplates.build_rag_prompt(query, context_chunks)
            url = f"{self.config.ollama_base_url}/api/chat"
            payload = {
                "model": self.config.model_name or "llama3",
                "messages": [
                    {"role": "system", "content": AcademicPromptTemplates.SYSTEM_ACADEMIC},
                    {"role": "user", "content": prompt},
                ],
                "stream": True,
            }
            try:
                with requests.post(url, json=payload, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            import json
                            data = json.loads(line.decode("utf-8"))
                            msg = data.get("message", {}).get("content", "")
                            if msg:
                                yield msg
            except Exception as e:
                yield f"\n[Ollama error: {e}]\n"
                yield OfflineSynthesizer.synthesize(query, context_chunks)

        else:
            # Direct Clean Offline Synthesis
            answer = OfflineSynthesizer.synthesize(query, context_chunks)
            yield answer

    def ask(self, query: str, context_chunks: List[Tuple[TextChunk, float]]) -> str:
        """Non-streaming query response."""
        full_response = []
        for token in self.stream_answer(query, context_chunks):
            full_response.append(token)
        return "".join(full_response)


llm_engine = LLMEngine()
