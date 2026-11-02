
import json

from config import generate_response
from utils.prompts import EXPAND_THOUGHT_PROMPT
from core.thought_generator import extract_json


def expand_thought(thought: dict) -> list:
    """
    Expand one strategic thought into actionable sub-strategies.
    """

    prompt = EXPAND_THOUGHT_PROMPT.format(
        thought=json.dumps(thought, indent=2)
    )

    response = generate_response(prompt)

    try:
        data = extract_json(response)
        sub_thoughts = data.get("sub_thoughts", [])

        if not sub_thoughts:
            raise ValueError("No sub-strategies generated.")

        return sub_thoughts

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Failed to expand strategy: {error}"
        ) from error
