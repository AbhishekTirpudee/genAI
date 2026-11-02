# MarketMind AI

MarketMind AI is a local, evidence-first market research prototype. It uses Python, LangChain, LangGraph, OpenAI, Tavily, Streamlit, and a durable SQLite job store.

## What it does

- Seven independent Pydantic-typed agents plan, research, analyze competitors and customer insights, create a SWOT and business analysis, and write a cited report.
- Real Tavily search results and robots-aware BeautifulSoup page extraction provide the evidence. Unsupported market statistics are not generated; unverified business ideas are labeled as assumptions.
- LangGraph fans out independent analysis nodes, validates source references, and can request up to two bounded rounds of targeted additional research.
- Background worker threads persist requests, execution events, state, and reports in SQLite. Queued or interrupted runs are recovered when the application restarts.
- Streamlit provides the research form, seven-agent event monitor, research history, report, source links, evidence-coverage charts, and PDF/Markdown/JSON downloads.
- A deliberately labeled offline demo exercises the real graph and export path without fabricating sources or market findings.

## Requirements

- Python 3.11 or newer
- OpenAI API key and Tavily API key for live research

## Windows PowerShell quick start

```powershell
Set-Location 'D:\market research agent\MarketMind-AI'
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set `OPENAI_API_KEY` and `TAVILY_API_KEY` in `.env`, then start the app:

```powershell
Set-Location 'D:\market research agent\MarketMind-AI'
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open <http://localhost:8501>. If PowerShell blocks virtual-environment activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

### Start without API keys

Leave the keys unset, start Streamlit, and choose **Run clearly labeled offline demo**. Demo runs traverse the same seven-agent LangGraph, persist their actual execution events, and produce downloadable exports; they make no web calls and contain no fabricated market facts. Live research stays disabled until both keys are configured.

## Run tests

From `MarketMind-AI` with the environment activated:

```powershell
python -m pytest -q
```

Tests exercise the real LangGraph graph and bounded feedback loop using explicit test-only provider fixtures, SQLite recovery and concurrency, evidence-citation validation, and report exports. No external API keys are needed for tests.

## Local data and credentials

- `.env` contains backend-only API keys and is excluded from version control.
- SQLite history: `data\research.sqlite3`
- Per-run snapshots and report downloads: `outputs\<job-id>\`
- `MAX_RESEARCH_WORKERS`, `MAX_SEARCH_CALLS`, `MAX_UNIQUE_SOURCES`, and `MAX_RESEARCH_ITERATIONS` bound execution.

## Agent workflow

`Research Planner → Market Research → (Competitor Analysis ‖ Customer Insights) → (SWOT ‖ Financial & Business Analysis) → Source Verification → [bounded targeted research loop] → Report Generator`

The workflow, agents, data schemas, local storage, and UI live in [`MarketMind-AI`](./MarketMind-AI/). See [architecture](./docs/ARCHITECTURE.md).
