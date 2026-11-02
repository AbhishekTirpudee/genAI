"""
Database module for LLM Evaluation Studio.
Manages SQLite storage, querying, schema initialization, and sample data seeding.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Create a database connection with dict-like row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite database schema if not present."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        question TEXT NOT NULL,
        reference_answer TEXT NOT NULL,
        model_a TEXT NOT NULL,
        model_b TEXT NOT NULL,
        judge_model TEXT NOT NULL,
        response_a TEXT NOT NULL,
        response_b TEXT NOT NULL,
        latency_a REAL DEFAULT 0.0,
        latency_b REAL DEFAULT 0.0,
        tokens_a INTEGER DEFAULT 0,
        tokens_b INTEGER DEFAULT 0,
        accuracy_a REAL NOT NULL,
        relevance_a REAL NOT NULL,
        completeness_a REAL NOT NULL,
        clarity_a REAL NOT NULL,
        overall_a REAL NOT NULL,
        accuracy_b REAL NOT NULL,
        relevance_b REAL NOT NULL,
        completeness_b REAL NOT NULL,
        clarity_b REAL NOT NULL,
        overall_b REAL NOT NULL,
        winner TEXT NOT NULL,
        strengths_a TEXT DEFAULT '',
        weaknesses_a TEXT DEFAULT '',
        strengths_b TEXT DEFAULT '',
        weaknesses_b TEXT DEFAULT '',
        reasoning_a TEXT DEFAULT '',
        reasoning_b TEXT DEFAULT '',
        judge_summary TEXT DEFAULT '',
        rubric_weights TEXT DEFAULT '{}',
        is_blinded INTEGER DEFAULT 0
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_timestamp ON evaluations(timestamp DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_winner ON evaluations(winner);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_models ON evaluations(model_a, model_b);")
    conn.commit()
    conn.close()


def save_evaluation(record: Dict[str, Any]) -> str:
    """
    Persist an evaluation record into SQLite.
    Returns the generated evaluation ID.
    """
    eval_id = record.get("id") or str(uuid.uuid4())[:8]
    ts = record.get("timestamp") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    rubric_json = record.get("rubric_weights", {})
    if isinstance(rubric_json, (dict, list)):
        rubric_json = json.dumps(rubric_json)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evaluations (
            id, timestamp, question, reference_answer,
            model_a, model_b, judge_model,
            response_a, response_b,
            latency_a, latency_b, tokens_a, tokens_b,
            accuracy_a, relevance_a, completeness_a, clarity_a, overall_a,
            accuracy_b, relevance_b, completeness_b, clarity_b, overall_b,
            winner,
            strengths_a, weaknesses_a, strengths_b, weaknesses_b,
            reasoning_a, reasoning_b, judge_summary,
            rubric_weights, is_blinded
        ) VALUES (
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?
        )
    """, (
        eval_id, ts, record.get("question", ""), record.get("reference_answer", ""),
        record.get("model_a", ""), record.get("model_b", ""), record.get("judge_model", ""),
        record.get("response_a", ""), record.get("response_b", ""),
        float(record.get("latency_a", 0.0)), float(record.get("latency_b", 0.0)),
        int(record.get("tokens_a", 0)), int(record.get("tokens_b", 0)),
        float(record.get("accuracy_a", 0.0)), float(record.get("relevance_a", 0.0)),
        float(record.get("completeness_a", 0.0)), float(record.get("clarity_a", 0.0)),
        float(record.get("overall_a", 0.0)),
        float(record.get("accuracy_b", 0.0)), float(record.get("relevance_b", 0.0)),
        float(record.get("completeness_b", 0.0)), float(record.get("clarity_b", 0.0)),
        float(record.get("overall_b", 0.0)),
        record.get("winner", "Tie"),
        record.get("strengths_a", ""), record.get("weaknesses_a", ""),
        record.get("strengths_b", ""), record.get("weaknesses_b", ""),
        record.get("reasoning_a", ""), record.get("reasoning_b", ""),
        record.get("judge_summary", ""),
        rubric_json,
        1 if record.get("is_blinded") else 0
    ))
    conn.commit()
    conn.close()
    return eval_id


def get_all_evaluations(limit: int = 100, search: Optional[str] = None, winner_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve evaluations with optional filtering and search."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM evaluations WHERE 1=1"
    params: List[Any] = []

    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (question LIKE ? OR model_a LIKE ? OR model_b LIKE ? OR judge_summary LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    if winner_filter and winner_filter != "All":
        query += " AND winner = ?"
        params.append(winner_filter)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("rubric_weights"), str):
            try:
                d["rubric_weights"] = json.loads(d["rubric_weights"])
            except Exception:
                d["rubric_weights"] = {}
        results.append(d)
    return results


def get_evaluation_by_id(eval_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single evaluation record by its unique ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evaluations WHERE id = ?", (eval_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    d = dict(row)
    if isinstance(d.get("rubric_weights"), str):
        try:
            d["rubric_weights"] = json.loads(d["rubric_weights"])
        except Exception:
            d["rubric_weights"] = {}
    return d


def delete_evaluation(eval_id: str) -> bool:
    """Delete an evaluation record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluations WHERE id = ?", (eval_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def clear_all_evaluations() -> bool:
    """Delete all evaluation records from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluations")
    conn.commit()
    conn.close()
    return True


def get_analytics_summary() -> Dict[str, Any]:
    """Calculate aggregate statistics across all saved evaluations."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM evaluations")
    total_evals = cursor.fetchone()[0]

    if total_evals == 0:
        conn.close()
        return {
            "total_evaluations": 0,
            "model_stats": {},
            "winner_counts": {"Model A": 0, "Model B": 0, "Tie": 0},
            "avg_accuracy": 0.0,
            "avg_relevance": 0.0,
            "avg_completeness": 0.0,
            "avg_clarity": 0.0,
            "avg_overall": 0.0,
            "recent_records": []
        }

    # Aggregate metric averages
    cursor.execute("""
        SELECT
            AVG((accuracy_a + accuracy_b) / 2.0) as avg_accuracy,
            AVG((relevance_a + relevance_b) / 2.0) as avg_relevance,
            AVG((completeness_a + completeness_b) / 2.0) as avg_completeness,
            AVG((clarity_a + clarity_b) / 2.0) as avg_clarity,
            AVG((overall_a + overall_b) / 2.0) as avg_overall
        FROM evaluations
    """)
    avg_row = cursor.fetchone()

    # Winners distribution
    cursor.execute("SELECT winner, COUNT(*) FROM evaluations GROUP BY winner")
    winner_rows = cursor.fetchall()
    winner_counts = {"Model A": 0, "Model B": 0, "Tie": 0}
    for w, count in winner_rows:
        if w in winner_counts:
            winner_counts[w] = count
        else:
            winner_counts[w] = count

    # Per-model breakdown
    cursor.execute("SELECT model_a, model_b, overall_a, overall_b, winner FROM evaluations")
    all_runs = cursor.fetchall()

    model_stats: Dict[str, Dict[str, Any]] = {}
    for r in all_runs:
        mA, mB, scoreA, scoreB, win = r[0], r[1], r[2], r[3], r[4]

        # Init stats for model A
        if mA not in model_stats:
            model_stats[mA] = {"appearances": 0, "wins": 0, "total_score": 0.0, "scores": []}
        model_stats[mA]["appearances"] += 1
        model_stats[mA]["total_score"] += scoreA
        model_stats[mA]["scores"].append(scoreA)
        if win == "Model A":
            model_stats[mA]["wins"] += 1

        # Init stats for model B
        if mB not in model_stats:
            model_stats[mB] = {"appearances": 0, "wins": 0, "total_score": 0.0, "scores": []}
        model_stats[mB]["appearances"] += 1
        model_stats[mB]["total_score"] += scoreB
        model_stats[mB]["scores"].append(scoreB)
        if win == "Model B":
            model_stats[mB]["wins"] += 1

    # Compute averages and win rates
    for m, data in model_stats.items():
        data["avg_score"] = round(data["total_score"] / data["appearances"], 2) if data["appearances"] else 0.0
        data["win_rate"] = round((data["wins"] / data["appearances"]) * 100, 1) if data["appearances"] else 0.0

    conn.close()

    return {
        "total_evaluations": total_evals,
        "model_stats": model_stats,
        "winner_counts": winner_counts,
        "avg_accuracy": round(avg_row["avg_accuracy"] or 0.0, 2),
        "avg_relevance": round(avg_row["avg_relevance"] or 0.0, 2),
        "avg_completeness": round(avg_row["avg_completeness"] or 0.0, 2),
        "avg_clarity": round(avg_row["avg_clarity"] or 0.0, 2),
        "avg_overall": round(avg_row["avg_overall"] or 0.0, 2)
    }


def seed_sample_evaluations() -> int:
    """
    Populate the SQLite database with 6 realistic benchmark evaluations.
    Returns the count of seeded evaluations.
    """
    init_db()

    sample_data = [
        {
            "id": "sample-01",
            "timestamp": "2026-11-01 10:15:22",
            "question": "Implement an LRU (Least Recently Used) cache in Python with O(1) get and put time complexity. Explain the data structures used.",
            "reference_answer": "Use a hash map paired with a doubly linked list (or collections.OrderedDict). The hash map maps keys to node pointers for O(1) lookup, while the doubly linked list allows O(1) insertion, deletion, and relocation of recently accessed nodes.",
            "model_a": "gemini-2.5-flash",
            "model_b": "gemini-2.5-pro",
            "judge_model": "gemini-2.5-pro",
            "response_a": "```python\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.capacity = capacity\n        self.cache = {}\n\n    def get(self, key: int) -> int:\n        if key not in self.cache:\n            return -1\n        val = self.cache.pop(key)\n        self.cache[key] = val\n        return val\n\n    def put(self, key: int, value: int) -> None:\n        if key in self.cache:\n            self.cache.pop(key)\n        elif len(self.cache) >= self.capacity:\n            oldest = next(iter(self.cache))\n            del self.cache[oldest]\n        self.cache[key] = value\n```\nThis uses Python 3.7+ dict ordering where keys maintain insertion order.",
            "response_b": "Here is an optimal LRU Cache implementation using a custom Doubly Linked List and Hash Map to strictly guarantee O(1) operations across all Python versions:\n\n```python\nclass Node:\n    def __init__(self, key=0, value=0):\n        self.key = key\n        self.value = value\n        self.prev = None\n        self.next = None\n\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.capacity = capacity\n        self.cache = {}  # key -> Node\n        self.head = Node()\n        self.tail = Node()\n        self.head.next = self.tail\n        self.tail.prev = self.head\n\n    def _remove(self, node):\n        prev_node = node.prev\n        next_node = node.next\n        prev_node.next = next_node\n        next_node.prev = prev_node\n\n    def _add_to_tail(self, node):\n        node.prev = self.tail.prev\n        node.next = self.tail\n        self.tail.prev.next = node\n        self.tail.prev = node\n\n    def get(self, key: int) -> int:\n        if key not in self.cache:\n            return -1\n        node = self.cache[key]\n        self._remove(node)\n        self._add_to_tail(node)\n        return node.value\n\n    def put(self, key: int, value: int) -> None:\n        if key in self.cache:\n            self._remove(self.cache[key])\n        node = Node(key, value)\n        self._add_to_tail(node)\n        self.cache[key] = node\n        if len(self.cache) > self.capacity:\n            lru = self.head.next\n            self._remove(lru)\n            del self.cache[lru.key]\n```\n**Complexity Analysis:**\n- `get(key)`: O(1) time complexity via hash map lookup and constant pointer updates.\n- `put(key, value)`: O(1) time complexity for eviction and node insertion.",
            "latency_a": 0.85,
            "latency_b": 2.15,
            "tokens_a": 280,
            "tokens_b": 640,
            "accuracy_a": 8.5,
            "relevance_a": 9.5,
            "completeness_a": 7.0,
            "clarity_a": 9.0,
            "overall_a": 8.35,
            "accuracy_b": 9.8,
            "relevance_b": 10.0,
            "completeness_b": 9.8,
            "clarity_b": 9.5,
            "overall_b": 9.82,
            "winner": "Model B",
            "strengths_a": "Concise implementation relying on Python's native dict ordering; easy to read.",
            "weaknesses_a": "Does not explain the classical computer science data structures (Doubly Linked List + Hash Map) as thoroughly.",
            "strengths_b": "Complete classical implementation with explicit Node structure, dummy head/tail pointers, and thorough O(1) complexity analysis.",
            "weaknesses_b": "Slightly more verbose code compared to standard library shortcuts.",
            "reasoning_a": "Model A provided a working implementation using dict ordering, but left out the doubly linked list explanation.",
            "reasoning_b": "Model B satisfied every requirement comprehensively, providing clean modular helper methods and exact algorithmic justifications.",
            "judge_summary": "Model B (Gemini 2.5 Pro) provided a superior computer-science grounded solution with clean pointer mechanics.",
            "rubric_weights": {"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10},
            "is_blinded": 1
        },
        {
            "id": "sample-02",
            "timestamp": "2026-11-01 11:40:05",
            "question": "What is the primary pathophysiological difference between Type 1 and Type 2 Diabetes Mellitus?",
            "reference_answer": "Type 1 Diabetes is an autoimmune disorder characterized by destruction of pancreatic beta cells leading to absolute insulin deficiency. Type 2 Diabetes involves progressive insulin resistance in peripheral tissues coupled with relative secretory defect.",
            "model_a": "gemini-2.5-pro",
            "model_b": "gemini-1.5-flash",
            "judge_model": "gemini-2.5-pro",
            "response_a": "The primary pathophysiological distinction lies in the underlying etiology and insulin availability:\n\n1. **Type 1 Diabetes Mellitus (T1DM)**:\n   - **Mechanism**: Autoimmune-mediated destruction of pancreatic islet β-cells (typically via autoantibodies like GAD65, IA-2, ZnT8).\n   - **Insulin Status**: **Absolute deficiency** of endogenous insulin.\n   - **Onset**: Typically juvenile or young adult, prone to rapid ketoacidosis (DKA).\n\n2. **Type 2 Diabetes Mellitus (T2DM)**:\n   - **Mechanism**: Progressive peripheral **insulin resistance** (liver, muscle, adipose) coupled with a compensatory, then declining, relative insulin secretory defect.\n   - **Insulin Status**: **Relative deficiency** (frequently hyperinsulinemic in early stages).\n   - **Onset**: Predominantly adult onset strongly correlated with metabolic syndrome and adiposity.",
            "response_b": "Type 1 diabetes is when the pancreas stops making insulin because your body's immune system attacks it. Type 2 diabetes is when your body becomes resistant to insulin or doesn't make enough of it over time, often linked to lifestyle and diet.",
            "latency_a": 1.72,
            "latency_b": 0.65,
            "tokens_a": 420,
            "tokens_b": 110,
            "accuracy_a": 9.8,
            "relevance_a": 10.0,
            "completeness_a": 9.5,
            "clarity_a": 9.7,
            "overall_a": 9.77,
            "accuracy_b": 8.0,
            "relevance_b": 9.0,
            "completeness_b": 6.5,
            "clarity_b": 8.5,
            "overall_b": 7.93,
            "winner": "Model A",
            "strengths_a": "Precise biochemical and clinical terminology (autoantibodies, absolute vs relative deficiency, peripheral tissue sites).",
            "weaknesses_a": "Slightly denser for lay readers, though appropriate for biomedical queries.",
            "strengths_b": "Very simple and plain English explanation.",
            "weaknesses_b": "Lacks specific pathophysiological depth and physiological mechanisms.",
            "reasoning_a": "Model A gave an exact textbook-level pathophysiological breakdown.",
            "reasoning_b": "Model B was too high-level given the technical prompt.",
            "judge_summary": "Model A (Gemini 2.5 Pro) provided an authoritative and scientifically rigorous explanation.",
            "rubric_weights": {"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10},
            "is_blinded": 1
        },
        {
            "id": "sample-03",
            "timestamp": "2026-11-01 14:22:18",
            "question": "Solve this riddle: 'I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?'",
            "reference_answer": "An echo.",
            "model_a": "gemini-2.5-flash",
            "model_b": "gemini-1.5-pro",
            "judge_model": "gemini-2.5-pro",
            "response_a": "The answer to the riddle is an **echo**!\n\n**Reasoning:**\n- It speaks without a mouth (reflects voice)\n- It hears without ears (responds to sound waves)\n- It has no physical body\n- It travels through the air/wind.",
            "response_b": "The answer is an **echo**.",
            "latency_a": 0.42,
            "latency_b": 0.95,
            "tokens_a": 85,
            "tokens_b": 25,
            "accuracy_a": 10.0,
            "relevance_a": 10.0,
            "completeness_a": 9.5,
            "clarity_a": 10.0,
            "overall_a": 9.88,
            "accuracy_b": 10.0,
            "relevance_b": 10.0,
            "completeness_b": 8.5,
            "clarity_b": 10.0,
            "overall_b": 9.62,
            "winner": "Tie",
            "strengths_a": "Accurate answer accompanied by a pleasant breakdown of the riddle's clues.",
            "weaknesses_a": "None.",
            "strengths_b": "Direct and punchy.",
            "weaknesses_b": "Could have included a one-line explanation.",
            "reasoning_a": "Model A identified the exact answer and mapped each metaphor cleanly.",
            "reasoning_b": "Model B identified the exact answer immediately.",
            "judge_summary": "Both models solved the riddle flawlessly. Model A added light rationale, resulting in a virtual tie.",
            "rubric_weights": {"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10},
            "is_blinded": 1
        },
        {
            "id": "sample-04",
            "timestamp": "2026-11-01 16:05:40",
            "question": "Write an executive summary of the benefits and trade-offs of microservices vs monolithic software architecture for a fintech startup.",
            "reference_answer": "Monoliths offer rapid early deployment, simple end-to-end debugging, and ACID compliance across single databases, but can become cumbersome as teams scale. Microservices offer autonomous deployments and technology flexibility, but introduce distributed systems overhead, network latency, and eventual consistency challenges.",
            "model_a": "gemini-2.5-flash",
            "model_b": "gemini-2.5-pro",
            "judge_model": "gemini-2.5-pro",
            "response_a": "# Executive Summary: Monolith vs Microservices for Fintech\n\n### Recommendation\nFor early-stage fintech, start with a modular monolith, then decouple into microservices as transactional domain boundaries mature.\n\n### Key Comparisons\n- **Monoliths**: Faster time-to-market, single codebase, strict database transactions (ACID), but harder to scale individual services.\n- **Microservices**: Independent scaling, isolated security blast radius, but higher DevOps cost and distributed transaction complexity.",
            "response_b": "# Executive Summary: Architectural Strategy for Fintech Growth\n\n### Strategic Overview\nFor a fintech startup balancing agility with regulatory scrutiny, architectural selection is a risk-management decision:\n\n| Dimension | Modular Monolith | Distributed Microservices |\n| :--- | :--- | :--- |\n| **Time to MVP** | 🟢 4-8 weeks; unified pipeline | 🟡 12-20 weeks; infra overhead |\n| **Transactional Integrity** | 🟢 Immediate ACID compliance | 🔴 Eventual consistency / 2PC |\n| **Auditability & Compliance** | 🟢 Centralized event logging | 🟡 Distributed tracing (OpenTelemetry) |\n| **Operational Overhead** | 🟢 Low (single Kubernetes pod/VM) | 🔴 High (service mesh, Kafka, IAM) |\n| **Domain Scalability** | 🟡 Risk of spaghetti code | 🟢 Autonomous team velocity |\n\n### Executive Recommendation\nAdopt a **'Monolith-First'** paradigm with strictly enforced domain modules. Decouple high-throughput domains (e.g., payment gateway, ledger) into microservices only when organizational friction or independent scaling demands it.",
            "latency_a": 0.92,
            "latency_b": 2.45,
            "tokens_a": 210,
            "tokens_b": 490,
            "accuracy_a": 9.0,
            "relevance_a": 9.0,
            "completeness_a": 8.0,
            "clarity_a": 9.0,
            "overall_a": 8.75,
            "accuracy_b": 9.8,
            "relevance_b": 9.8,
            "completeness_b": 9.9,
            "clarity_b": 9.8,
            "overall_b": 9.82,
            "winner": "Model B",
            "strengths_a": "Clear recommendation and bulleted takeaways.",
            "weaknesses_a": "Lacks quantitative context and executive tabular formatting.",
            "strengths_b": "Exceptional executive presentation with comparative matrix, fintech-specific compliance aspects, and actionable phased roadmap.",
            "weaknesses_b": "Slightly longer generation latency.",
            "reasoning_a": "Model A gave good general points but remained generic.",
            "reasoning_b": "Model B deeply tailored the trade-offs to fintech specifics (ACID vs eventual consistency, auditability).",
            "judge_summary": "Model B (Gemini 2.5 Pro) provided an executive-ready strategic briefing with fintech domain nuance.",
            "rubric_weights": {"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10},
            "is_blinded": 1
        },
        {
            "id": "sample-05",
            "timestamp": "2026-11-01 18:50:11",
            "question": "What is the time complexity of building a heap (Heapify) from an unsorted array of n elements, and why is it not O(n log n)?",
            "reference_answer": "Building a heap takes O(n) time. While inserting n elements into an initially empty heap takes O(n log n), bottom-up heapification processes nodes level-by-level. Most nodes are near the leaves with small heights; the mathematical summation yields O(n).",
            "model_a": "gemini-2.5-pro",
            "model_b": "gemini-1.5-pro",
            "judge_model": "gemini-2.5-pro",
            "response_a": "The time complexity of building a binary heap from an unsorted array using bottom-up Heapify (Floyd's algorithm) is **O(n)**, not O(n log n).\n\n### Mathematical Proof\nA complete binary tree of n nodes has height h = floor(log2 n).\n- At level i from the bottom, there are at most ceil(n / 2^(i+1)) nodes.\n- Each node at height i requires at most O(i) swaps to sift down.\n\nThe total work W is:\n`W = sum_{i=1}^{h} (n / 2^(i+1)) * i = (n / 4) * sum_{i=1}^{h} i / 2^(i-1)`\n\nThe series sum_{i=1}^{infinity} i / 2^(i-1) converges to 4.\nTherefore: W = (n / 4) * 4 = **O(n)**.\n\n### Why not O(n log n)?\nO(n log n) occurs when inserting elements one by one from the top down. Bottom-up heapify starts at the leaves (which require 0 swaps) and processes half the elements with height <= 1.",
            "response_b": "Building a heap takes O(n) time. It is not O(n log n) because we don't insert one by one. Half the nodes are leaves and do 0 work, a quarter do 1 swap, and so on. The infinite sum converges to 2, so the whole thing is bounded by O(n).",
            "latency_a": 2.10,
            "latency_b": 1.15,
            "tokens_a": 460,
            "tokens_b": 150,
            "accuracy_a": 10.0,
            "relevance_a": 10.0,
            "completeness_a": 10.0,
            "clarity_a": 9.5,
            "overall_a": 9.95,
            "accuracy_b": 9.0,
            "relevance_b": 9.5,
            "completeness_b": 7.5,
            "clarity_b": 8.5,
            "overall_b": 8.70,
            "winner": "Model A",
            "strengths_a": "Rigorous mathematical proof with Taylor/geometric series convergence and clear contrast between top-down and bottom-up builds.",
            "weaknesses_a": "None.",
            "strengths_b": "Intuitively correct observation regarding leaf node proportions.",
            "weaknesses_b": "Omits formal summation and specific height indices.",
            "reasoning_a": "Model A demonstrated mastery of algorithmic analysis and proof formulation.",
            "reasoning_b": "Model B had the right intuition but lacked algebraic completeness.",
            "judge_summary": "Model A (Gemini 2.5 Pro) provided an academically rigorous and complete demonstration.",
            "rubric_weights": {"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10},
            "is_blinded": 1
        }
    ]

    count = 0
    conn = get_db_connection()
    cursor = conn.cursor()
    for item in sample_data:
        cursor.execute("SELECT id FROM evaluations WHERE id = ?", (item["id"],))
        if not cursor.fetchone():
            save_evaluation(item)
            count += 1
    conn.close()
    return count

