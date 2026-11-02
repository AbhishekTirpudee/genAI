# 🎓 ScholarMind AI — Academic PDF RAG Assistant & Study Agent

> **An elite, state-of-the-art PDF-based Retrieval-Augmented Generation (RAG) academic chatbot designed for students and researchers to upload lecture notes, textbooks, and research papers, ask questions with exact page-level citations, practice interactive flashcards, take AI-generated exam quizzes, and view high-yield summaries.**

---

## ✨ Key Features & Unique Capabilities

1. 📄 **Multi-Page Academic PDF Ingestion**:
   - Parses multi-page lecture notes, slide decks, and textbooks using `pypdf`.
   - Semantic paragraph-aware chunking preserving chapter and section headers, page numbers, and token counts.
   - Built-in sample academic notes on **Computer Science & AI Foundations** and **Deep Learning & Optimization**.

2. ⚡ **Advanced Hybrid RAG Retrieval (BM25 + TF-IDF RRF)**:
   - **BM25 Inverted Index**: Pinpoints exact formulas, algorithms, Big-O complexities, and academic terms (e.g., "Coffman conditions", "Dijkstra", "BCNF", "Scaled Dot-Product").
   - **Vectorized TF-IDF (Unigram + Bigram)**: Captures semantic and conceptual queries.
   - **Reciprocal Rank Fusion (RRF)**: Merges keyword and semantic rankings to achieve maximum retrieval precision without heavy GPU overhead.

3. 📌 **Transparent Source Citations & Verbatim Inspector**:
   - Every response provides clickable source pills showing the source PDF filename, exact page number (e.g., `Page 1`), section header, and relevance percentage.
   - Click any citation pill to open the **Source Context Inspector** showing the verbatim note excerpt.

4. 🧠 **Dual AI Generation Engine**:
   - **Google Gemini 2.5 Flash Integration**: Generates conversational, deeply grounded explanations with LaTeX math formatting and suggested study questions.
   - **Autonomous Offline Synthesizer**: Runs 100% locally out-of-the-box without requiring an API key or internet access, ensuring high availability and zero setup friction.

5. 🗂️ **Interactive 3D Study Flashcards**:
   - Automatically extracts core concepts, definitions, formulas, and laws into 3D flippable flashcards.
   - Flip cards via click or Spacebar, navigate via arrow keys, or regenerate new card decks on demand.

6. 📝 **Practice Exam Quiz Generator**:
   - Generates university exam-style Multiple Choice Questions (MCQs) with 4 options.
   - Instant visual grading (green/red), detailed answer explanations, and source page attribution.

7. 📋 **Executive Summary & Formula Cheat Sheet**:
   - High-yield study outline, formulas table, and estimated reading time.

8. 🔬 **Semantic Chunk Explorer**:
   - Full search interface to inspect how notes were chunked, indexed, and distributed across pages.

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Installation
Ensure you have Python 3.10+ installed.

```bash
cd d:\Projects\Rule-based-FAQ-chatbot
pip install -r requirements.txt
```

### 2. Launch the Web Application (Recommended)
Launch the modern glassmorphic web dashboard:

```bash
python chatbot.py --web
```
Or:
```bash
python app.py
```

Open your browser to: **[http://localhost:8000](http://localhost:8000)**

### 3. Launch the Interactive Terminal CLI
You can also run the academic chatbot directly in your terminal:

```bash
python chatbot.py
```

**CLI Commands**:
- Ask any question: `What are the four Coffman conditions for a deadlock?`
- Upload a new PDF: `/upload path/to/lecture_notes.pdf`
- Review flashcards: `/flashcards`
- Take an exam quiz: `/quiz`
- View formulas & summary: `/summary`
- Switch to Web UI: `/web`
- Exit: `exit` or `bye`

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | Engine mode, active documents, total chunks, page count |
| `POST` | `/api/upload` | Upload and index one or multiple PDF documents |
| `POST` | `/api/load-sample` | Automatically loads bundled CS and ML study guides |
| `POST` | `/api/chat` | Submit question with conversation history for grounded answer |
| `GET` | `/api/documents` | List all active documents and their statistics |
| `DELETE` | `/api/documents/{id}` | Remove a document and update the index |
| `DELETE` | `/api/clear` | Clear all documents from index |
| `POST` | `/api/flashcards` | Generate active recall study flashcards |
| `POST` | `/api/quiz` | Generate interactive practice exam questions |
| `GET` | `/api/summary` | Generate executive notes summary & formulas table |
| `GET` | `/api/chunks` | Search and inspect indexed chunks |
| `POST` | `/api/settings` | Configure Google Gemini API key |

---

## 📁 Project Architecture

```
Rule-based-FAQ-chatbot/
│
├── app.py                      # FastAPI web server and REST API routes
├── chatbot.py                  # Interactive CLI & web launcher
├── rag_engine.py               # Core Academic RAG: BM25, TF-IDF RRF, Gemini, Flashcard/Quiz generators
├── sample_notes_generator.py   # Programmatic generator for realistic multi-page academic test notes
├── test_rag.py                 # RAG pipeline test verification suite
├── requirements.txt            # Python dependencies
├── README.md                   # Full documentation
│
├── sample_notes/               # Bundled academic test PDFs
│   ├── CS_Foundations_Notes.pdf
│   └── Deep_Learning_RAG_Notes.pdf
│
└── static/                     # Modern Glassmorphic Web Dashboard
    ├── index.html              # Accessible HTML5 structure & navigation
    ├── index.css               # Obsidian dark theme, 3D card flips & CSS tokens
    └── app.js                  # Frontend state management & async API integration
```
