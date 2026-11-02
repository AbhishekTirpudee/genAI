"""
Export utilities for converting evaluation history into CSV and JSON formats.
"""

import io
import json
import pandas as pd
from typing import List, Dict, Any


def export_to_csv(evaluations: List[Dict[str, Any]]) -> str:
    """
    Convert a list of evaluation records into a formatted CSV string.
    """
    if not evaluations:
        return ""

    flattened = []
    for e in evaluations:
        flat_record = {
            "ID": e.get("id"),
            "Timestamp": e.get("timestamp"),
            "Question": e.get("question"),
            "Reference Answer": e.get("reference_answer"),
            "Model A": e.get("model_a"),
            "Model B": e.get("model_b"),
            "Judge Model": e.get("judge_model"),
            "Response A": e.get("response_a"),
            "Response B": e.get("response_b"),
            "Latency A (s)": e.get("latency_a"),
            "Latency B (s)": e.get("latency_b"),
            "Tokens A": e.get("tokens_a"),
            "Tokens B": e.get("tokens_b"),
            "Model A Accuracy": e.get("accuracy_a"),
            "Model A Relevance": e.get("relevance_a"),
            "Model A Completeness": e.get("completeness_a"),
            "Model A Clarity": e.get("clarity_a"),
            "Model A Overall": e.get("overall_a"),
            "Model B Accuracy": e.get("accuracy_b"),
            "Model B Relevance": e.get("relevance_b"),
            "Model B Completeness": e.get("completeness_b"),
            "Model B Clarity": e.get("clarity_b"),
            "Model B Overall": e.get("overall_b"),
            "Winner": e.get("winner"),
            "Model A Strengths": e.get("strengths_a"),
            "Model A Weaknesses": e.get("weaknesses_a"),
            "Model B Strengths": e.get("strengths_b"),
            "Model B Weaknesses": e.get("weaknesses_b"),
            "Reasoning A": e.get("reasoning_a"),
            "Reasoning B": e.get("reasoning_b"),
            "Judge Summary": e.get("judge_summary"),
            "Blinded Evaluation": "Yes" if e.get("is_blinded") else "No"
        }
        flattened.append(flat_record)

    df = pd.DataFrame(flattened)
    return df.to_csv(index=False)


def export_to_json(evaluations: List[Dict[str, Any]]) -> str:
    """
    Convert evaluations into indented JSON string.
    """
    return json.dumps(evaluations, indent=2, ensure_ascii=False)

