"""
Configuration module for LLM Evaluation Studio.
Handles environment variables, default model settings, rubric weights, and paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DB_DIR = PROJECT_ROOT / "database"
DB_PATH = DB_DIR / "evaluations.db"
ENV_FILE = PROJECT_ROOT / ".env"

# Ensure database directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env if present
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=False)
else:
    load_dotenv(override=False)

# Available Google Gemini Models
AVAILABLE_MODELS = [
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "badge": "Fast & Efficient",
        "description": "Optimized for high-speed generation, lower latency, and broad language tasks."
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "badge": "Advanced Reasoning",
        "description": "Best for complex reasoning, comprehensive coding, and nuanced evaluation."
    },
    {
        "id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "badge": "Lightweight",
        "description": "Cost-effective, versatile model for rapid turnaround."
    },
    {
        "id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "badge": "Deep Context",
        "description": "Designed for intensive multi-turn analysis and rigorous structured outputs."
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "badge": "Next-Gen Flash",
        "description": "Next generation speed and high reasoning capability."
    }
]

# Quick model ID lists
MODEL_IDS = [m["id"] for m in AVAILABLE_MODELS]

# Default Model Selections
DEFAULT_MODEL_A = os.getenv("DEFAULT_MODEL_A", "gemini-2.5-flash")
DEFAULT_MODEL_B = os.getenv("DEFAULT_MODEL_B", "gemini-2.5-pro")
DEFAULT_JUDGE_MODEL = os.getenv("DEFAULT_JUDGE_MODEL", "gemini-2.5-pro")

# Default Scoring Rubric Weights (Must sum to 1.0 / 100%)
DEFAULT_RUBRIC_WEIGHTS = {
    "accuracy": 0.40,
    "relevance": 0.25,
    "completeness": 0.25,
    "clarity": 0.10
}

RUBRIC_METRIC_INFO = {
    "accuracy": {
        "label": "Accuracy",
        "weight_pct": 40,
        "description": "Factual correctness, adherence to truths, and absence of hallucinations."
    },
    "relevance": {
        "label": "Relevance",
        "weight_pct": 25,
        "description": "Directly answering the user's specific prompt without deviating."
    },
    "completeness": {
        "label": "Completeness",
        "weight_pct": 25,
        "description": "Addressing all sub-questions, edge cases, and required depth."
    },
    "clarity": {
        "label": "Clarity",
        "weight_pct": 10,
        "description": "Logical organization, concise readability, and clear formatting."
    }
}

# Generation Defaults
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))


def get_api_key() -> str:
    """Retrieve Gemini API key from environment variable or .env file."""
    # Check os environment first
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return api_key


def set_api_key(api_key: str, persist_to_env_file: bool = True) -> bool:
    """
    Set API key in current environment and optionally persist to .env file.
    Never exposes key in logs.
    """
    clean_key = api_key.strip()
    os.environ["GEMINI_API_KEY"] = clean_key

    if persist_to_env_file:
        try:
            lines = []
            key_set = False
            if ENV_FILE.exists():
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            lines.append(f"GEMINI_API_KEY={clean_key}\n")
                            key_set = True
                        else:
                            lines.append(line)
            if not key_set:
                lines.append(f"GEMINI_API_KEY={clean_key}\n")

            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        except Exception:
            return False
    return True


def is_demo_mode() -> bool:
    """Check if demo/mock simulation mode is active."""
    val = os.getenv("DEMO_MODE", "false").lower()
    return val in ("1", "true", "yes")

