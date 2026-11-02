# ElectroRAG: Electronic Component Catalogue RAG Chatbot
> **End Semester Examination (ESE) Lab Project — Generative AI**  
> An intelligent, strictly grounded Retrieval-Augmented Generation (RAG) system for querying electronic component specifications, practical applications, package dimensions, and tiered volume pricing.

---

## 🌟 Key Highlights

- **Domain-Specific Grounding**: Solves common RAG issues with electrical datasheets where naive chunkers destroy tabular specifications (voltages, current ratings, pinouts).
- **Hybrid Retrieval Engine**:
  - **Sparse / Lexical Matching**: Exact Part Number (MPN) boost for components like `ESP32-WROOM-32`, `LM358`, `AMS1117-3.3`, `IRFZ44N`.
  - **Dense / Semantic Vector Search**: Cosine similarity for conceptual queries ("find a low-voltage sensor for weather station").
- **Table & Pricing Breakdown**: Retains volume quantity discount tiers (1, 10, 100, 1000 units).
- **Accurate Citations**: Every answer cites the exact catalogue page number and relevance score.
- **Dual Execution Mode**:
  1. **Google Gemini Live LLM**: Connects with `gemini-1.5-flash` or `gemini-2.0` when an API key is provided.
  2. **Offline Deterministic Grounded Synthesizer**: Works 100% offline without any API key or external network—ideal for lab demonstrations!

---

## 🏗️ Architecture

```
                                 [ Uploaded Catalogue ]
                              (JSON / CSV / Multi-page PDF)
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                INGESTION & INDEXING                                    │
│  - Document Parser: Preserves tabular rows & column relationships                      │
│  - Metadata Enrichment: Part Number (MPN), Category, Page #, Package, Pinout          │
│  - Dual Index: TF-IDF Vector Space (Dense) + BM25 Lexical Token Index (Sparse)         │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              HYBRID RETRIEVAL PIPELINE                                 │
│  User Query: "What is the operating voltage and price of LM358 in 100 qty?"           │
│                                           │                                            │
│   ├── Lexical Part Number Matching (Boost = 2.5x if MPN found)                         │
│   └── Dense Cosine Similarity (Semantic alignment of specifications)                   │
│                                           │                                            │
│   Weighted Fusion Score: S = 0.5 * Sim_Dense + 0.3 * Overlap_Lexical + MPN_Boost       │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              GROUNDED GENERATION LAYER                                 │
│  - Assembles prompt with strict domain constraints (no hallucinated pinouts/ratings)   │
│  - Synthesizes formatted Markdown tables (Specs & Pricing Breaks)                      │
│  - Emits Page Citations & Stock Availability                                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 How to Run the Project

This project uses Python's built-in networking library, meaning **no pip installation delays or virtualenv issues are required to start the web app**.

### 1. Launch the Server
In PowerShell / Command Prompt inside this folder:
```powershell
python app.py
```

### 2. Open in Browser
Visit:
👉 **[http://localhost:8501](http://localhost:8501)**

### 3. Upload and query a catalogue
Use **Upload Catalogue** in the sidebar to select a JSON or CSV catalogue. Once indexing succeeds, ask questions in the chat about the uploaded components' specifications, applications, or quantity-based prices. CSV files should include a part-number column; quoted fields containing commas are supported.

---

## 💻 CLI / Terminal Mode (Alternative)
You can also run standalone queries directly from your terminal:
```powershell
# Query specs and prices
python rag_engine.py "What are the specs and price of ESP32?"

# Compare two components
python rag_engine.py "Compare ESP32-WROOM-32 vs STM32F401"

# Query voltage regulators
python rag_engine.py "What is the dropout voltage and package of AMS1117-3.3?"
```

---

## 📂 Project Structure

```
ese lab genai/
├── app.py                             # Lightweight HTTP server & RAG REST API endpoints
├── rag_engine.py                      # Core Hybrid RAG engine (indexing, search, generation)
├── index.html                         # High-tech Cyber-industrial Web UI
├── style.css                          # Modern glassmorphism & responsive dark theme styles
├── app.js                             # Client controller, chat streaming & live catalogue parser
├── electronic_components_catalogue.json # 14+ full component datasheets with specs & prices
├── electronic_components_catalogue.csv  # Spreadsheet-formatted catalogue
├── electronic_components_catalogue.pdf  # Generated multi-page PDF catalogue
├── generate_catalogue_pdf.py          # Script to generate printable/evaluable PDF
└── README.md                          # Project report & documentation
```

---

## 🧪 Sample Queries to Demonstrate in Lab

| Query Type | Sample Question | Expected Grounded Output |
| :--- | :--- | :--- |
| **Exact Spec** | *"What is the operating voltage and package of LM358?"* | 3.0V to 32V (Single), ±1.5V to ±16V (Dual), DIP-8/SOIC-8, Page 6 |
| **Component Comparison** | *"Compare ESP32-WROOM-32 vs STM32F401"* | Side-by-side spec comparison table (Clock, Flash, RAM, Price) |
| **Application Filter** | *"Suggest a sensor for measuring humidity & temperature"* | Retrieves DHT22 (AM2302) and BME280 with temperature and humidity accuracy |
| **Volume Pricing** | *"What are the volume pricing breaks for NE555 for 1000 pcs?"* | $0.14 for 1000 pcs, $0.35 for 1 pc (Page 7) |
| **Power Constraint** | *"Find a 3.3V LDO regulator under $0.50"* | Retrieves AMS1117-3.3 ($0.32 for 1 pc, 1.1V dropout) |

---

## 🎓 Viva Questions & Answers for GenAI Lab

**Q1: Why is standard RAG chunking insufficient for electronic datasheets?**  
*Answer:* Standard character chunking (e.g., slicing every 500 characters) cuts across tables, severing the link between a pin/feature and its numerical value. In our project, table rows are formatted into structured markdown and tagged with component metadata (`part_number`, `page_number`).

**Q2: What is Hybrid Search and why is it important here?**  
*Answer:* Semantic vector search maps meanings to vectors. For similar part numbers (e.g. `LM7805` vs `LM7812`), vector embeddings are nearly identical. Hybrid search combines lexical/BM25 matching (which rewards exact alphanumeric part numbers) with dense cosine similarity (which handles conceptual queries like "low dropout regulator").

**Q3: How do you prevent hallucinations of electrical ratings?**  
*Answer:* By enforcing strict context grounding in the system prompt: if a parameter (such as max junction temperature) is absent from the retrieved chunk, the system is explicitly constrained to state that it is not specified in the catalogue rather than estimating it.
