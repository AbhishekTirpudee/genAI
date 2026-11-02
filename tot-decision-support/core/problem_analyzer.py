
from config import generate_response
from utils.prompts import ANALYZE_PROMPT


def analyze_problem(problem: str) -> str:
    """
    Analyze the business problem and identify
    root causes, objectives and constraints.
    """

    if not problem or not problem.strip():
        raise ValueError("Business problem cannot be empty.")

    prompt = ANALYZE_PROMPT.format(
        problem=problem.strip()
    )

    analysis = generate_response(prompt)

    return analysis
