"""
Electronic Component Catalogue RAG Engine
==========================================
Implements Hybrid Retrieval (BM25 / Keyword + Dense Semantic Vector Search)
with strict domain grounding for electronic components specifications,
applications, and pricing.
"""

import json
import re
import math
import os
from collections import Counter
from typing import List, Dict, Any, Tuple

# Optional LLM integration
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class ComponentRAGEngine:
    def __init__(self, catalogue_path: str = "electronic_components_catalogue.json"):
        self.catalogue_path = catalogue_path
        self.components: List[Dict[str, Any]] = []
        self.chunks: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.chunk_vectors: List[Dict[str, float]] = []
        self.api_key: str = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        
        self.load_and_index()

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase alphanumeric tokens, preserving part-number hyphens."""
        return [t.lower() for t in re.findall(r'[a-zA-Z0-9_\-\./]+', text) if len(t) > 1]

    def load_and_index(self):
        """Loads catalogue and builds both Sparse (BM25-style) and Dense (TF-IDF vector) indices."""
        if not os.path.exists(self.catalogue_path):
            raise FileNotFoundError(f"Catalogue not found at: {self.catalogue_path}")

        with open(self.catalogue_path, "r", encoding="utf-8") as f:
            self.components = json.load(f)

        self.chunks = []
        for comp in self.components:
            specs_str = ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in comp.get("specifications", {}).items()])
            apps_str = "; ".join(comp.get("applications", []))
            pricing = comp.get("pricing", {})
            price_str = f"Qty 1: ${pricing.get('qty_1', '-')}, Qty 10: ${pricing.get('qty_10', '-')}, Qty 100: ${pricing.get('qty_100', '-')}, Qty 1000: ${pricing.get('qty_1000', '-')}"

            chunk_text = (
                f"Part Number: {comp['part_number']}\n"
                f"Category: {comp.get('category', 'Uncategorized')}\n"
                f"Description: {comp.get('description', '')}\n"
                f"Specifications: {specs_str}\n"
                f"Applications: {apps_str}\n"
                f"Pricing: {price_str}\n"
                f"Stock: {comp.get('stock_status', 'Unknown')}\n"
                f"Catalogue Page: {comp.get('page_number', 'N/A')}"
            )

            self.chunks.append({
                "part_number": comp["part_number"],
                "category": comp.get("category", ""),
                "page_number": comp.get("page_number", 1),
                "component_data": comp,
                "text": chunk_text,
                "tokens": self.tokenize(chunk_text)
            })

        # Calculate TF-IDF index
        n_docs = len(self.chunks)
        doc_freq = Counter()
        for chunk in self.chunks:
            unique_tokens = set(chunk["tokens"])
            for token in unique_tokens:
                doc_freq[token] += 1

        self.idf = {token: math.log((n_docs + 1) / (df + 1)) + 1.0 for token, df in doc_freq.items()}

        self.chunk_vectors = []
        for chunk in self.chunks:
            tf = Counter(chunk["tokens"])
            total_tokens = len(chunk["tokens"]) or 1
            vec = {}
            norm_sq = 0.0
            for token, count in tf.items():
                tfidf = (count / total_tokens) * self.idf.get(token, 1.0)
                vec[token] = tfidf
                norm_sq += tfidf ** 2
            norm = math.sqrt(norm_sq) or 1.0
            self.chunk_vectors.append({t: v / norm for t, v in vec.items()})

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Hybrid Search:
        Combines exact Part Number boost + Keyword BM25-style frequency + Cosine Similarity.
        """
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return [(chunk, 1.0) for chunk in self.chunks[:top_k]]

        # Query vector
        q_tf = Counter(query_tokens)
        q_vec = {}
        norm_sq = 0.0
        for token, count in q_tf.items():
            tfidf = (count / len(query_tokens)) * self.idf.get(token, 1.0)
            q_vec[token] = tfidf
            norm_sq += tfidf ** 2
        norm = math.sqrt(norm_sq) or 1.0
        q_vec = {t: v / norm for t, v in q_vec.items()}

        scores = []
        query_lower = query.lower()

        for idx, chunk in enumerate(self.chunks):
            # 1. Dense Semantic Cosine Similarity
            doc_vec = self.chunk_vectors[idx]
            cosine_sim = sum(q_vec.get(t, 0.0) * doc_vec.get(t, 0.0) for t in q_vec)

            # 2. Exact Part Number / MPN Match Boost (Crucial for Electronics!)
            pn_lower = chunk["part_number"].lower()
            pn_clean = re.sub(r'[^a-z0-9]', '', pn_lower)
            q_clean = re.sub(r'[^a-z0-9]', '', query_lower)

            exact_match_boost = 0.0
            if pn_lower in query_lower or (len(pn_clean) >= 4 and pn_clean in q_clean):
                exact_match_boost = 2.5
            elif any(part.lower() in pn_lower for part in query_tokens if len(part) >= 3):
                exact_match_boost = 0.8

            # 3. Category & Keyword Coverage
            keyword_overlap = sum(1 for t in query_tokens if t in doc_vec) / len(query_tokens)

            final_score = (0.5 * cosine_sim) + (0.3 * keyword_overlap) + exact_match_boost
            scores.append((chunk, final_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def generate_response(self, query: str, api_key: str = None) -> Dict[str, Any]:
        """Retrieves top context and generates a grounded response."""
        retrieved_results = self.search(query, top_k=3)
        key_to_use = api_key or self.api_key

        # Build grounded context
        context_blocks = []
        citations = []
        for chunk, score in retrieved_results:
            context_blocks.append(chunk["text"])
            citations.append({
                "part_number": chunk["part_number"],
                "category": chunk["category"],
                "page": chunk["page_number"],
                "relevance_score": round(score, 3)
            })

        context_str = "\n\n====================\n\n".join(context_blocks)

        system_prompt = (
            "You are an expert Electronic Components Technical Assistant.\n"
            "Answer the user's question accurately and strictly based on the provided catalogue context.\n\n"
            "Format your answer with:\n"
            "1. Clear Markdown tables for specifications\n"
            "2. Practical applications\n"
            "3. Price tiers (Qty 1, 10, 100, 1000)\n"
            "4. Citation of the catalogue page\n\n"
            f"Context from Catalogue:\n{context_str}\n\n"
            f"User Question: {query}"
        )

        # Attempt to call Gemini API if key is present
        if HAS_GEMINI and key_to_use:
            try:
                genai.configure(api_key=key_to_use)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(system_prompt)
                return {
                    "answer": response.text,
                    "citations": citations,
                    "mode": "Gemini 1.5 Flash (Live LLM)"
                }
            except Exception as e:
                # Fallback to local synthesizer if API fails (e.g., quota or network)
                pass

        # Intelligent Deterministic RAG Synthesizer (Works 100% offline without API key)
        top_chunk = retrieved_results[0][0]
        comp = top_chunk["component_data"]
        q_lower = query.lower()

        # Check for comparison query
        if "compare" in q_lower and len(retrieved_results) >= 2:
            c1 = retrieved_results[0][0]["component_data"]
            c2 = retrieved_results[1][0]["component_data"]
            answer = (
                f"### Component Comparison: {c1['part_number']} vs {c2['part_number']}\n\n"
                f"| Feature | {c1['part_number']} | {c2['part_number']} |\n"
                f"| :--- | :--- | :--- |\n"
                f"| **Category** | {c1.get('category')} | {c2.get('category')} |\n"
                f"| **Operating Voltage** | {c1['specifications'].get('operating_voltage', c1['specifications'].get('input_voltage', 'N/A'))} | {c2['specifications'].get('operating_voltage', c2['specifications'].get('input_voltage', 'N/A'))} |\n"
                f"| **Package** | {c1['specifications'].get('package', 'N/A')} | {c2['specifications'].get('package', 'N/A')} |\n"
                f"| **Price (1 pc)** | ${c1['pricing'].get('qty_1')} | ${c2['pricing'].get('qty_1')} |\n"
                f"| **Price (100 pcs)** | ${c1['pricing'].get('qty_100')} | ${c2['pricing'].get('qty_100')} |\n"
                f"| **Catalogue Page** | Page {c1.get('page_number')} | Page {c2.get('page_number')} |\n\n"
                f"**Applications Summary:**\n"
                f"- **{c1['part_number']}**: {', '.join(c1.get('applications', []))}\n"
                f"- **{c2['part_number']}**: {', '.join(c2.get('applications', []))}\n"
            )
        else:
            # Single or multi-component grounded answer
            specs_table = "| Specification | Rating / Value |\n| :--- | :--- |\n"
            for k, v in comp.get("specifications", {}).items():
                specs_table += f"| **{k.replace('_', ' ').title()}** | {v} |\n"

            pricing = comp.get("pricing", {})
            price_table = (
                f"| Qty Break | Unit Price (USD) |\n| :--- | :--- |\n"
                f"| 1 pc | ${pricing.get('qty_1', '-')} |\n"
                f"| 10 pcs | ${pricing.get('qty_10', '-')} |\n"
                f"| 100 pcs | ${pricing.get('qty_100', '-')} |\n"
                f"| 1000 pcs | ${pricing.get('qty_1000', '-')} |\n"
            )

            apps_list = "\n".join([f"- {app}" for app in comp.get("applications", [])])

            answer = (
                f"### {comp['part_number']} ({comp.get('category')})\n\n"
                f"{comp.get('description')}\n\n"
                f"#### Technical Specifications\n{specs_table}\n"
                f"#### Target Applications\n{apps_list}\n\n"
                f"#### Volume Pricing & Stock\n{price_table}\n"
                f"- **Stock Status:** {comp.get('stock_status', 'In Stock')}\n"
                f"- **Source Reference:** Catalogue Page {comp.get('page_number')}\n"
            )

        return {
            "answer": answer,
            "citations": citations,
            "mode": "Deterministic Hybrid RAG Engine (Ground-Truth Synthesizer)"
        }


if __name__ == "__main__":
    import sys
    engine = ComponentRAGEngine()
    test_query = sys.argv[1] if len(sys.argv) > 1 else "What are the specs and price of ESP32?"
    print(f"\nUser Query: {test_query}\n" + "="*50)
    result = engine.generate_response(test_query)
    print(result["answer"])
    print("\nCitations:", json.dumps(result["citations"], indent=2))
