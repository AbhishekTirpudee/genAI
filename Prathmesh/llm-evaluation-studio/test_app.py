"""
Comprehensive Test Suite for LLM Evaluation Studio.
Tests database operations, rubric validators, score calculations,
response generation, judge evaluation, and chart generation.
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import (
    AVAILABLE_MODELS,
    DEFAULT_RUBRIC_WEIGHTS,
    get_api_key,
    set_api_key
)
from backend.database import (
    init_db,
    save_evaluation,
    get_all_evaluations,
    get_evaluation_by_id,
    delete_evaluation,
    get_analytics_summary,
    seed_sample_evaluations
)
from utils.validators import (
    validate_rubric_weights,
    validate_evaluation_input,
    clean_and_parse_json,
    validate_and_normalize_judge_scores
)
from utils.export import export_to_csv, export_to_json
from backend.model_generator import generate_parallel_responses, generate_single_response
from backend.evaluator import evaluate_both_models, evaluate_single_response
from backend.comparison import (
    create_score_comparison_df,
    create_bar_chart,
    create_radar_chart,
    create_history_trend_chart,
    create_win_distribution_chart
)


def run_tests():
    print("=" * 60)
    print("RUNNING LLM EVALUATION STUDIO TEST SUITE")
    print("=" * 60)

    # 1. Config Test
    print("\n[1/7] Testing Configuration...")
    assert len(AVAILABLE_MODELS) >= 4, "Should have at least 4 available models"
    assert sum(DEFAULT_RUBRIC_WEIGHTS.values()) == 1.0, "Default weights must sum to 1.0"
    print("  [OK] Configuration verified.")

    # 2. Database & Sample Data Test
    print("\n[2/7] Testing SQLite Database...")
    init_db()
    seeded = seed_sample_evaluations()
    print(f"  [OK] Seeded {seeded} sample records.")
    
    evals = get_all_evaluations(limit=10)
    assert len(evals) >= 5, f"Expected at least 5 seeded records, found {len(evals)}"
    sample_id = evals[0]["id"]
    rec = get_evaluation_by_id(sample_id)
    assert rec is not None, "Failed to retrieve record by ID"
    assert "accuracy_a" in rec, "Record missing accuracy_a"

    stats = get_analytics_summary()
    assert stats["total_evaluations"] >= 5, "Analytics summary count mismatch"
    assert "model_stats" in stats, "Analytics missing model stats"
    print(f"  [OK] Database CRUD & Analytics verified (Total: {stats['total_evaluations']} evaluations).")

    # 3. Validators Test
    print("\n[3/7] Testing Rubric & JSON Validators...")
    # Valid weights
    valid, msg, _ = validate_rubric_weights({"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10})
    assert valid is True, "Valid weights incorrectly rejected"
    
    # Invalid weights
    invalid, msg, norm = validate_rubric_weights({"accuracy": 0.50, "relevance": 0.25, "completeness": 0.25, "clarity": 0.20})
    assert invalid is False, "Invalid weights not caught"
    assert sum(norm.values()) == 1.0, "Normalized suggestion must sum to 1.0"

    # JSON extraction from markdown
    raw_md = "```json\n{\"accuracy\": 9.5, \"relevance\": 9.0, \"completeness\": 8.5, \"clarity\": 9.0, \"strengths\": \"Great\", \"weaknesses\": \"None\", \"reasoning\": \"Solid\"}\n```"
    parsed = clean_and_parse_json(raw_md)
    assert parsed is not None and parsed["accuracy"] == 9.5, "Failed to parse markdown JSON"

    # Score clamping & calculation
    _, normalized, _ = validate_and_normalize_judge_scores(
        {"accuracy": 12.0, "relevance": -2.0, "completeness": 8.0, "clarity": 10.0},
        DEFAULT_RUBRIC_WEIGHTS
    )
    assert normalized["accuracy"] == 10.0, "Score > 10 was not clamped"
    assert normalized["relevance"] == 0.0, "Score < 0 was not clamped"
    # overall: 10*0.40 + 0*0.25 + 8*0.25 + 10*0.10 = 4.0 + 0.0 + 2.0 + 1.0 = 7.0
    assert normalized["overall_score"] == 7.0, f"Expected overall score 7.0, got {normalized['overall_score']}"
    print("  [OK] Validators and score clamping verified.")

    # 4. Response Generator Test (Simulated / Fallback)
    print("\n[4/7] Testing Response Generation...")
    res_a, res_b = generate_parallel_responses(
        model_a="gemini-2.5-flash",
        model_b="gemini-2.5-pro",
        prompt="Explain LRU cache in Python."
    )
    assert res_a["success"] is True, f"Model A failed: {res_a.get('error')}"
    assert res_b["success"] is True, f"Model B failed: {res_b.get('error')}"
    assert len(res_a["response"]) > 20, "Model A response too short"
    assert len(res_b["response"]) > 20, "Model B response too short"
    assert res_a["latency_sec"] >= 0.0, "Latency invalid"
    print(f"  [OK] Parallel response generation successful (Latencies: {res_a['latency_sec']}s, {res_b['latency_sec']}s).")

    # 5. LLM-as-a-Judge Evaluation Test
    print("\n[5/7] Testing LLM-as-a-Judge Engine...")
    eval_a, eval_b, winner, summary = evaluate_both_models(
        question="Explain LRU cache in Python.",
        reference_answer="Use a hash map paired with a doubly linked list for O(1) ops.",
        response_a=res_a["response"],
        response_b=res_b["response"],
        model_a_name="gemini-2.5-flash",
        model_b_name="gemini-2.5-pro",
        rubric_weights=DEFAULT_RUBRIC_WEIGHTS,
        blind_evaluation=True
    )
    assert "overall_score" in eval_a, "Missing overall score for model A"
    assert "overall_score" in eval_b, "Missing overall score for model B"
    assert winner in ("Model A", "Model B", "Tie"), f"Invalid winner: {winner}"
    assert len(summary) > 10, "Summary too short"
    print(f"  [OK] Judge evaluation passed: Winner = {winner} (Score A: {eval_a['overall_score']}, Score B: {eval_b['overall_score']}).")

    # 6. Comparison & Chart Generation Test
    print("\n[6/7] Testing Comparison & Visualizations...")
    df_comp = create_score_comparison_df(eval_a, eval_b, "gemini-2.5-flash", "gemini-2.5-pro")
    assert len(df_comp) == 5, f"Expected 5 comparison rows, got {len(df_comp)}"
    
    fig_bar = create_bar_chart(eval_a, eval_b, "gemini-2.5-flash", "gemini-2.5-pro")
    assert fig_bar is not None, "Bar chart creation failed"

    fig_radar = create_radar_chart(eval_a, eval_b, "gemini-2.5-flash", "gemini-2.5-pro")
    assert fig_radar is not None, "Radar chart creation failed"

    fig_donut = create_win_distribution_chart(stats["winner_counts"])
    assert fig_donut is not None, "Donut chart creation failed"

    fig_trend = create_history_trend_chart(evals)
    assert fig_trend is not None, "Trend chart creation failed"
    print("  [OK] Comparison tables and Plotly charts created successfully.")

    # 7. Export Test
    print("\n[7/7] Testing CSV & JSON Data Export...")
    csv_str = export_to_csv(evals)
    assert "Model A Accuracy" in csv_str, "CSV export missing header"
    json_str = export_to_json(evals)
    assert len(json_str) > 50, "JSON export too short"
    print("  [OK] Data export verified.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! (7/7 suites passed)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
