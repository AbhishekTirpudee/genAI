"""
Validation module for user inputs, rubric weights, and LLM judge JSON output.
Ensures strict type-checking, bounds checking, and graceful sanitization.
"""

import json
import re
from typing import Tuple, Dict, Any, Optional


def validate_rubric_weights(weights: Dict[str, float]) -> Tuple[bool, str, Dict[str, float]]:
    """
    Validate that rubric weights sum to 1.0 (100%).
    Returns (is_valid, message, normalized_weights).
    """
    required_keys = ["accuracy", "relevance", "completeness", "clarity"]
    for k in required_keys:
        if k not in weights:
            return False, f"Missing required rubric dimension: {k.capitalize()}", weights

    total = sum(weights[k] for k in required_keys)
    total_pct = round(total * 100, 2)

    # Allow floating point imprecision within 0.1%
    if abs(total - 1.0) > 0.001:
        # Compute normalized suggestion
        if total > 0:
            normalized = {k: round(weights[k] / total, 4) for k in required_keys}
            # Adjust rounding residue to ensure exact 1.0
            diff = 1.0 - sum(normalized.values())
            normalized["accuracy"] = round(normalized["accuracy"] + diff, 4)
        else:
            normalized = {"accuracy": 0.40, "relevance": 0.25, "completeness": 0.25, "clarity": 0.10}

        return (
            False,
            f"Rubric weights sum to {total_pct}% instead of 100.0%. Please adjust the sliders.",
            normalized
        )

    return True, "Weights total 100%.", weights


def validate_evaluation_input(
    question: str,
    reference_answer: str,
    model_a: str,
    model_b: str,
    judge_model: str
) -> Tuple[bool, str]:
    """Validate user prompt form before initiating evaluation."""
    if not question or len(question.strip()) < 5:
        return False, "Prompt / Question must be at least 5 characters long."

    if not reference_answer or len(reference_answer.strip()) < 3:
        return False, "Please provide an expected / reference answer for benchmark comparison."

    if not model_a or not model_a.strip():
        return False, "Please select Model A."

    if not model_b or not model_b.strip():
        return False, "Please select Model B."

    if not judge_model or not judge_model.strip():
        return False, "Please select an LLM Judge model."

    return True, "Input validation passed."


def clean_and_parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON object from raw LLM output.
    Handles markdown wrappers (```json ... ```) and leading/trailing chatter.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    cleaned = raw_text.strip()

    # 1. Look for ```json ... ``` blocks
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except Exception:
            pass

    # 2. Look for outermost curly braces { ... }
    json_brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if json_brace_match:
        candidate = json_brace_match.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            # Try removing trailing commas
            candidate_cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(candidate_cleaned)
            except Exception:
                pass

    # 3. Direct parse attempt
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def validate_and_normalize_judge_scores(
    raw_data: Dict[str, Any],
    rubric_weights: Dict[str, float]
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validate and clamp judge scores between 0.0 and 10.0,
    and recalculate weighted overall score using the active rubric.
    """
    metrics = ["accuracy", "relevance", "completeness", "clarity"]
    normalized: Dict[str, Any] = {}

    for m in metrics:
        val = raw_data.get(m)
        if val is None:
            # Fallback to middle neutral score if missing
            normalized[m] = 5.0
        else:
            try:
                num = float(val)
                # Clamp between 0.0 and 10.0
                normalized[m] = max(0.0, min(10.0, round(num, 2)))
            except (ValueError, TypeError):
                normalized[m] = 5.0

    # Calculate weighted overall score strictly based on user-defined weights
    w_acc = rubric_weights.get("accuracy", 0.40)
    w_rel = rubric_weights.get("relevance", 0.25)
    w_comp = rubric_weights.get("completeness", 0.25)
    w_clar = rubric_weights.get("clarity", 0.10)

    calculated_overall = (
        (normalized["accuracy"] * w_acc) +
        (normalized["relevance"] * w_rel) +
        (normalized["completeness"] * w_comp) +
        (normalized["clarity"] * w_clar)
    )
    normalized["overall_score"] = round(calculated_overall, 2)

    # Feedback explanations
    normalized["strengths"] = str(raw_data.get("strengths", "No specific strengths noted.")).strip()
    normalized["weaknesses"] = str(raw_data.get("weaknesses", "No significant weaknesses observed.")).strip()
    normalized["reasoning"] = str(raw_data.get("reasoning", "Evaluation completed against rubric criteria.")).strip()

    return True, normalized, "Score normalization successful."

