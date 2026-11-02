
import json
import re

from config import generate_response
from utils.prompts import GENERATE_THOUGHTS_PROMPT


def extract_json(response: str) -> dict:
    """Extract JSON safely from Gemini response."""

    cleaned = response.strip()

    # Remove Markdown code fences if present
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    return json.loads(cleaned)


def generate_thoughts(problem: str, analysis: str) -> list:
    """
    Generate independent strategic solution branches.
    """

    prompt = GENERATE_THOUGHTS_PROMPT.format(
        problem=problem,
        analysis=analysis
    )

    response = generate_response(prompt)

    try:
        data = extract_json(response)
        thoughts = data.get("thoughts", [])

        if not thoughts:
            raise ValueError("No strategic solutions generated.")

        return thoughts

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Failed to generate valid strategic solutions: {error}"
        ) from error
