# AgentFlow AI: Intelligent Multi-Agent Task Automation System

> **Generative AI Practical Examination Project**  
> Built with **LangGraph**, **Google Gemini**, **FastAPI**, and **React + Vite + Tailwind CSS**.

AgentFlow AI is a production-grade, autonomous multi-agent task automation system designed to solve complex multi-step user tasks. It features real conditional routing, structured task decomposition, dynamic step-by-step synthesis, and an automated **Self-Correction Quality Loop** that guarantees high-fidelity deliverables.

---

## Architecture Overview

```mermaid
graph TD
    Start([START]) --> Planner[Planner Agent<br/>Gemini 3.8 Flash]
    Planner --> |Decomposes into 4-6 Steps| Executor[Execution Agent<br/>Gemini 3.8 Flash]
    Executor --> |Synthesizes Comprehensive Deliverable| Reviewer[Reviewer Agent<br/>Gemini 3.8 Flash]
    
    Reviewer --> |Evaluates Completeness, Correctness, Clarity| Conditional{Quality Score >= 8?}
    
    Conditional --> |Score >= 8<br/>[APPROVED]| End([END: Final Output])
    Conditional --> |Score < 8 AND Iteration < 3<br/>[REVISE]| LoopEdge[Self-Correction Router]
    LoopEdge --> |Passes Reviewer Critique & Missing Requirements| Executor
    Conditional --> |Iteration >= 3<br/>[MAX ATTEMPTS]| End
    
    style Start fill:#f3e8ff,stroke:#7c3aed,stroke-width:2px;
    style Planner fill:#ede9fe,stroke:#6d28d9,stroke-width:2px;
    style Executor fill:#e0e7ff,stroke:#4338ca,stroke-width:2px;
    style Reviewer fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    style Conditional fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
    style End fill:#d1fae5,stroke:#059669,stroke-width:2px;
    style LoopEdge fill:#fee2e2,stroke:#dc2626,stroke-width:2px,stroke-dasharray: 5 5;
```

---

## Agent Roles & Shared State

### 1. Planner Agent (`backend/agents.py`)
- **Model**: Google Gemini (`gemini-3.8-flash`)
- **Function**: Ingests user directives, isolates core goals and quality requirements, and deconstructs the problem into 4–6 concrete, logical, sequential milestones.
- **Output**: Structured JSON containing `identified_objectives`, `target_requirements`, and `steps` (step number, title, description, and deliverable).

### 2. Execution Agent (`backend/agents.py`)
- **Model**: Google Gemini
- **Function**: Executes each planned milestone in depth, providing exhaustive solutions, structured code snippets, implementation roadmaps, or architectural guidelines.
- **Self-Correction**: On revision cycles (iteration > 1), it reads the Reviewer Agent's previous critique, missing items, and improvement suggestions to revise and elevate the solution.

### 3. Reviewer Agent (`backend/agents.py`)
- **Model**: Google Gemini
- **Function**: Serves as a strict Quality Assurance auditor evaluating outputs against:
  1. *Task Completeness* (all plan steps addressed)
  2. *Factual & Technical Correctness*
  3. *Relevance to Prompt*
  4. *Clarity, Organization & Polish*
  5. *Plan Adherence*
- **Scoring & Threshold**: 1–10 integer score. If `score >= 8`, decision is **APPROVE**. If `score < 8`, decision is **REVISE**.

### 4. Shared LangGraph State (`backend/state.py`)
```python
class AgentFlowState(TypedDict):
    user_task: str
    plan: Optional[PlanOutput]
    execution: str
    review: Optional[ReviewOutput]
    score: int                     # 1 to 10
    feedback: str                  # Constructive critique
    missing_requirements: List[str]# Specific missing elements
    improvement_suggestions: List[str] # Actionable fixes
    iteration: int                 # 1, 2, or 3
    status: str                    # PLANNING, EXECUTING, REVIEWING, APPROVED, REVISING
    execution_logs: List[LogEntry] # Progressive timeline entries
    error: Optional[str]
```

---

## Project Structure

```
agentflow-ai/
├── backend/
│   ├── main.py              # FastAPI app, SSE streaming endpoints, background worker
│   ├── agents.py            # Planner, Execution, Reviewer Gemini agents
│   ├── graph.py             # LangGraph StateGraph, conditional routing logic
│   ├── state.py             # TypedDict shared state schema
│   ├── requirements.txt     # Backend Python dependencies
│   ├── .env.example         # Template for environment variables
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx               # Header with API status & model badge
│   │   │   ├── ApiKeyModal.jsx          # Secure in-browser Gemini API key setup
│   │   │   ├── TaskInput.jsx            # Dynamic textarea, presets, validation
│   │   │   ├── WorkflowVisualization.jsx# Interactive LangGraph node graph & loop
│   │   │   ├── AgentStatusCards.jsx     # Live agent gauges, metrics & state
│   │   │   ├── PlanStepsView.jsx        # Numbered step cards & deliverables
│   │   │   ├── ExecutionLogs.jsx        # Real-time SSE telemetry log panel
│   │   │   └── FinalOutputDashboard.jsx # Formatted deliverable, audit & export
│   │   ├── services/
│   │   │   └── api.js                   # Axios client & SSE stream connector
│   │   ├── App.jsx                      # Main dashboard application
│   │   ├── index.css                    # Tailwind CSS & custom styling
│   │   └── main.jsx                     # React root mount
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
├── README.md
└── .gitignore
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

---

### Step 1: Configure Google Gemini API Key

1. Obtain a free API key from **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. In the `backend` directory, create a `.env` file from the example:
   ```bash
   cd agentflow-ai/backend
   cp .env.example .env
   ```
3. Set your API key inside `backend/.env`:
   ```ini
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   GEMINI_MODEL=gemini-3.8-flash
   HOST=0.0.0.0
   PORT=8000
   ```
*(Note: You can also enter the Gemini API key directly in the web UI via the **"Configure API Key"** button).*

---

### Step 2: Backend Setup & Execution

1. Navigate to the backend directory:
   ```bash
   cd agentflow-ai/backend
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux / macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   python main.py
   # Or with uvicorn directly:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API will be live at `http://localhost:8000`.  
   API Documentation is available at `http://localhost:8000/docs`.

---

### Step 3: Frontend Setup & Execution

1. Open a new terminal and navigate to `frontend`:
   ```bash
   cd agentflow-ai/frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## REST & SSE API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/workflow/health` | Verifies server health, active Gemini model, and API key status. |
| `POST` | `/api/workflow/run` | Accepts user task and initiates background LangGraph workflow. Returns `workflow_id`. |
| `GET` | `/api/workflow/stream/{workflow_id}` | Server-Sent Events (SSE) stream delivering real-time agent transitions, node events, and logs. |
| `GET` | `/api/workflow/status/{workflow_id}` | Polls the current snapshot of a workflow state. |

---

## Practical Examination Demonstration Instructions

Follow this step-by-step script for an outstanding practical examination demo:

### 1. Verification of System Health
- Open `http://localhost:5173`.
- Notice the **"Gemini API: Ready"** indicator in the navbar and the active model badge (`gemini-3.8-flash`).
- Click **"Configure API Key"** in the top navigation to demonstrate client-side credential configuration with secure masking.

### 2. Executing a Multi-Step Directive
- Select one of the quick example prompts, e.g.:
  > *"Create a 7-day Generative AI learning roadmap for a beginner with hands-on daily milestones and recommended resources."*
- Click **"Execute LangGraph Workflow"** (or press <kbd>Ctrl + Enter</kbd>).

### 3. Observing the Real-Time Multi-Agent Workflow
1. **Interactive Workflow Diagram**:
   - The **Planner Agent** node pulses indigo as it calls Gemini to decompose the task.
   - Once completed, the node turns green with a checkmark, and the **Planner Blueprint** displays 4–6 numbered milestone cards with explicit deliverables.
2. **Execution Agent Synthesis**:
   - The **Execution Agent** node activates. The live telemetry logs stream each stage of synthesis.
   - The formatted deliverable is generated with comprehensive depth.
3. **Reviewer Agent Quality Audit**:
   - The **Reviewer Agent** node activates to evaluate completeness, accuracy, clarity, and adherence.
   - The live score meter updates (e.g., `8/10` or `9/10` with `[APPROVED]`, or `7/10` with `[REVISE]`).

### 4. Demonstrating the Self-Correction Loop
- If the Reviewer evaluates the initial attempt with a score < 8, observe:
  - The **LangGraph Self-Correction Edge** triggers.
  - A `self_correction_triggered` event is logged in the telemetry terminal.
  - The **Execution Agent** starts **Attempt #2**, explicitly incorporating the reviewer's missing criteria and feedback to produce a superior version.

### 5. Final Report Dashboard & Deliverable Export
- Once approved (Score >= 8), a confetti animation triggers.
- Inspect the **Final Output Dashboard**:
  - Reviewer score gauge and critique analysis.
  - Formatted markdown preview.
  - Click **"Copy Solution"** to copy markdown output to clipboard.
  - Click **"Download Report"** to export an audit report text file.
  - Click **"New Task"** to reset and test another directive.
