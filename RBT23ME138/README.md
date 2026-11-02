# 🎓 ScholarRAG: Academic Notes PDF RAG Chatbot (CLI)

An intelligent, terminal-native Retrieval-Augmented Generation (RAG) chatbot designed specifically for students, researchers, and self-learners. Upload PDF academic notes, textbooks, lecture slides, or study guides, and ask questions with **exact page-level citations**, generate **practice exam quizzes**, create **revision summaries**, and extract **active recall flashcards**.

Works **100% offline out-of-the-box** with smart local extractive ranking, and seamlessly integrates with **OpenAI (GPT-4o)**, **Groq (Llama-3.3)**, or **local Ollama** when an LLM is connected.

---

## 🌟 Key Features

- **Academic PDF Parser & Cleaner**: Extracts text page-by-page using `pypdf`, eliminates hyphenation noise, strips redundant headers, and retains exact page metadata.
- **Academic Context Chunker**: Splits notes into semantically coherent sections with configurable overlap and prepends source metadata tags (`[Document: Notes.pdf | Page: 3]`).
- **Hybrid Retrieval Engine**: Blends **BM25 lexical scoring** (for exact technical jargon, theorems, formulas) with **TF-IDF cosine similarity** to ensure maximum precision on academic queries.
- **Persistent Local Index**: Embeddings and chunk metadata are saved in `.scholar_cache/`, eliminating the need to re-parse PDFs across sessions.
- **Multi-Backend Intelligence**:
  - **Offline Extractive Synthesis**: Zero API key required! Extracts core propositions, matching equations, and page citations directly on your machine.
  - **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5 with streaming responses.
  - **Groq**: Ultra-fast Llama-3.3-70b and Mixtral.
  - **Ollama**: Connect to local LLMs (`llama3`, `mistral`, `phi3`, `qwen`) on `http://localhost:11434`.
- **Academic Study Tools**:
  - `/summary [doc]`: High-yield key takeaway notes and core concepts.
  - `/quiz [n] [topic]`: Practice exam questions based strictly on your notes.
  - `/flashcards [n]`: Active recall cards with terms and definitions.
  - `/export [file]`: Export your Q&A study session to clean Markdown (`study_session_notes.md`).
- **Rich Terminal UI**: Beautiful ANSI styling with status cards, tables, spinners, and markdown formatting powered by `rich`.

---

## 🚀 Quick Start

### 1. Installation

Clone or open the project directory and install the requirements:

```bash
pip install -r requirements.txt
```

### 2. Generate or Add Academic Notes

You can use the built-in sample academic lecture notes generator for testing:

```bash
python sample_data/create_sample_pdf.py
```
This generates `sample_data/Machine_Learning_Lecture_Notes.pdf` (a 4-page CS study guide on Supervised Learning, Loss Functions, Gradient Descent, Regularization, and Neural Networks).

### 3. Launch Interactive Chatbot

Simply run:

```bash
python cli.py
```

Inside the interactive shell:
```
ScholarBot > /upload sample_data/Machine_Learning_Lecture_Notes.pdf
ScholarBot > What is the difference between L1 and L2 regularization?
ScholarBot > /summary
ScholarBot > /quiz 4
ScholarBot > /flashcards 5
ScholarBot > /sources
ScholarBot > /export
```

---

## ⚡ Command Line Subcommands (One-Shot Mode)

ScholarRAG can also be executed directly from scripts or CI pipelines without entering the interactive shell:

```bash
# 1. Ingest a PDF or entire folder of notes
python cli.py upload "path/to/my_notes.pdf"
python cli.py upload "path/to/notes_folder/"

# 2. Ask a question directly
python cli.py ask "Explain the Cross-Entropy loss formula"

# 3. List all indexed documents & statistics
python cli.py docs

# 4. Generate an academic summary of indexed notes
python cli.py summary

# 5. Generate a practice quiz
python cli.py quiz --num 5 --topic "Regularization"
```

---

## 🛠️ Interactive Shell Commands

| Command | Description | Example |
|---|---|---|
| `/upload <path>` | Ingest a single PDF file or folder of notes | `/upload lecture1.pdf` |
| `/docs` | List all uploaded documents, page counts & chunks | `/docs` |
| `/remove <file>` | Remove a document from the index | `/remove lecture1.pdf` |
| `/summary [doc]` | Generate academic summary & key takeaways | `/summary` |
| `/quiz [n] [topic]` | Generate practice exam questions with page references | `/quiz 4 gradient descent` |
| `/flashcards [n]` | Extract term-definition active recall flashcards | `/flashcards 5` |
| `/sources` | View the exact excerpts & relevance scores from last query | `/sources` |
| `/provider <name>` | Switch provider (`offline`, `openai`, `groq`, `ollama`) | `/provider groq` |
| `/key <api_key>` | Set API key for OpenAI or Groq | `/key gsk_...` |
| `/model <name>` | Change model name (e.g. `gpt-4o-mini`) | `/model gpt-4o-mini` |
| `/export [file]` | Export study session notes to Markdown | `/export my_exam_prep.md` |
| `/clear` | Clear conversation history or wipe document index | `/clear` |
| `/help` | Display interactive command manual | `/help` |
| `/exit` | Exit the CLI | `/exit` |

---

## ⚙️ Configuration & API Keys

ScholarRAG does **not** force you to pay for API keys. It runs 100% offline by default!

If you want generative answers, you can supply your key in any of three ways:

1. **Inside the interactive CLI:**
   ```
   ScholarBot > /key gsk_your_groq_key_here
   # or
   ScholarBot > /key sk-proj-your_openai_key_here
   ```
2. **Via environment variable:**
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY = "sk-..."
   $env:GROQ_API_KEY = "gsk_..."
   ```
3. **Via `.env` file:**
   Copy `.env.example` to `.env` and fill in your keys.

---

## 📁 Project Architecture

```
Practical/
├── cli.py                     # Primary CLI executable (Interactive & Subcommands)
├── requirements.txt           # Project dependencies
├── .env.example               # Configuration template
├── README.md                  # Comprehensive documentation
├── sample_data/
│   ├── create_sample_pdf.py   # Academic PDF generator for testing
│   └── Machine_Learning_Lecture_Notes.pdf
└── scholar_rag/
    ├── __init__.py
    ├── config.py              # Configuration & settings persistence
    ├── pdf_loader.py          # PDF parser with page tracking and text normalization
    ├── text_splitter.py       # Academic context-aware paragraph chunker
    ├── vector_store.py        # Persistent Hybrid Index (BM25 + TF-IDF Cosine)
    ├── llm_engine.py          # Unified Multi-Provider Engine (OpenAI, Groq, Ollama, Offline)
    ├── study_assistant.py     # Academic tools: summaries, quizzes, flashcards
    └── ui.py                  # Rich terminal styling, tables, panels, and citations
```
