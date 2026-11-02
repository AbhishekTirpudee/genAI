"""Provider configuration for the project's chat model."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_PROVIDER = "openai"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


class LLMConfigurationError(RuntimeError):
    """Raised when the selected chat provider cannot be configured."""


GeminiConfigurationError = LLMConfigurationError


def get_llm() -> ChatOpenAI | ChatGoogleGenerativeAI:
    """Return the configured OpenAI or Gemini chat model."""
    provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise LLMConfigurationError(
                "OPENAI_API_KEY is missing. Add your OpenAI API key to the "
                "project .env file."
            )
        model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
        if not model:
            model = DEFAULT_OPENAI_MODEL
        try:
            return ChatOpenAI(model=model, api_key=api_key)
        except (TypeError, ValueError) as exc:
            raise LLMConfigurationError(
                f"Could not configure OpenAI model '{model}': {exc}"
            ) from exc

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            raise LLMConfigurationError(
                "GOOGLE_API_KEY is missing. Add it to the project .env file."
            )
        model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        if not model:
            model = DEFAULT_GEMINI_MODEL
        try:
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
            )
        except (TypeError, ValueError) as exc:
            raise LLMConfigurationError(
                f"Could not configure Gemini model '{model}': {exc}"
            ) from exc

    raise LLMConfigurationError(
        f"Unsupported LLM_PROVIDER '{provider}'. Choose 'openai' or 'gemini'."
    )
