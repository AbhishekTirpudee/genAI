# Onyx — AI Career Architect & Semantic Job Matcher

<div align="center">
  <img src="static/img/logo.png" width="100" height="100" alt="Onyx Logo" style="border-radius: 50%;">
  <h3>Autonomous Multi-Sector Resume & Job Fit Evaluation Engine</h3>
</div>

---

## 🌟 Overview
**Onyx** is an aesthetic, Claude-inspired career intelligence platform built to bridge the gap between candidate resumes and current multi-industry job market expectations. Built with a rich maroon visual palette and clean typography, Onyx parses candidate resumes across various document formats, researches cross-sector industry standards, quantifies semantic alignment, highlights critical qualification gaps, and suggests tailored resume improvements.

All session data, uploaded profiles, and reports are persisted to **Neon Serverless PostgreSQL**.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI (Python 3.11+) + Uvicorn
- **AI Engine:** Google Gemini 3.5 / 3.1 Flash (Google GenAI)
- **Database:** Neon PostgreSQL (Serverless) via SQLAlchemy 2.0 & Psycopg3
- **Document Parser:** PyMuPDF (`fitz`), `python-docx`, and UTF-8 decoders
- **Frontend:** Vanilla modern ES6, CSS Custom Properties (Rich Maroon Design System), Marked.js, Lucide Icons
- **Deployment:** Render Web Service (`render.yaml` & `Procfile`)

---

## 📐 Architecture & Sentence Embedding Subsystem

The application features a modular architectural design including a dedicated sentence embedding subsystem located in `app/embeddings/`:

```
app/
├── embeddings/
│   ├── config.py         # Hyperparameters (all-MiniLM-L6-v2, 384 dimensions)
│   ├── encoder.py        # SentenceTransformerMatcher, pooling, L2 normalization
│   ├── vector_store.py   # In-memory VectorIndex & CosineSimilaritySearcher
│   └── README.md         # Mathematical formulations & technical breakdown
├── ai_engine.py          # Google Gemini multi-sector market research & gap analyzer
├── database.py           # Neon PostgreSQL connection pool
├── models.py             # SQLAlchemy entities (Conversation, ResumeRecord, AnalysisReport)
├── parser.py             # Multi-format document parser (PDF, DOCX, TXT)
└── main.py               # FastAPI orchestrator and API routes
```

### Mathematical Foundations:
1. **Mean Token Pooling:**
   $$v = \frac{1}{N} \sum_{i=1}^N h_i$$
2. **L2 Hypersphere Normalization:**
   $$u = \frac{v}{\|v\|_2}$$
3. **Cosine Similarity Fit:**
   $$S_C(A, B) = \cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|}$$

---

## 🚀 Local Development Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <repo-folder>
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```env
DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require
GEMINI_API_KEY=your_gemini_api_key
PORT=8000
ENVIRONMENT=development
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload --port 8000
```
Open your browser to `http://localhost:8000`.

---

## ☁️ Deploying to Render (Live URL)

1. Push your repository to **GitHub**.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Web Service** -> Link your GitHub repository.
4. Render will automatically detect `render.yaml` or you can manually set:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. In **Environment Variables**, add:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
   - `GEMINI_API_KEY`: Your Google AI Studio API key.
   - `ENVIRONMENT`: `production`
6. Click **Deploy Web Service** and access your live URL!

