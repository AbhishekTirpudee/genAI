
import json

from config import generate_response
from utils.prompts import EVALUATE_PROMPT
from core.thought_generator import extract_json


# Evaluation weights (Total = 100%)
WEIGHTS = {
    "impact": 0.30,
    "feasibility": 0.25,
    "cost_efficiency": 0.15,
    "risk_management": 0.15,
    "time_efficiency": 0.15
}


def evaluate_thought(thought: dict, sub_thoughts: list) -> dict:
    """
    Evaluate a strategy using Gemini and calculate
    its weighted score using Python.
    """

    prompt = EVALUATE_PROMPT.format(
        thought=json.dumps(thought, indent=2),
        sub_thoughts=json.dumps(sub_thoughts, indent=2)
    )

    response = generate_response(prompt)

    try:
        evaluation = extract_json(response)

        # Validate and normalize scores
        scores = {}

        for criterion in WEIGHTS:
            score = float(evaluation[criterion])

            if not 1 <= score <= 10:
                raise ValueError(
                    f"Invalid score for {criterion}: {score}"
                )

            scores[criterion] = score

        # Python calculates the final weighted score
        weighted_score = sum(
            scores[key] * weight
            for key, weight in WEIGHTS.items()
        )

        evaluation.update(scores)
        evaluation["weighted_score"] = round(weighted_score, 2)

        return evaluation

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise RuntimeError(
            f"Strategy evaluation failed: {error}"
        ) from error
