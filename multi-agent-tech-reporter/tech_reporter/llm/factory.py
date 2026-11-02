"""Factory function for initializing LLM providers."""

import logging
from tech_reporter.config import AppConfig
from tech_reporter.llm.base import LLMProvider
from tech_reporter.llm.gemini import GeminiProvider
from tech_reporter.llm.openai_provider import OpenAIProvider
from tech_reporter.llm.mock_provider import MockProvider

logger = logging.getLogger(__name__)


def create_llm_provider(config: AppConfig) -> LLMProvider:
    """Creates and returns the appropriate LLM provider based on config."""
    provider_name = config.llm_provider.lower()

    if provider_name == "gemini":
        if not config.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set. Falling back to MockProvider.")
            return MockProvider()
        return GeminiProvider(api_key=config.gemini_api_key, model=config.gemini_model)

    elif provider_name == "openai":
        if not config.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set. Falling back to MockProvider.")
            return MockProvider()
        return OpenAIProvider(
            api_key=config.openai_api_key,
            model=config.openai_model,
            base_url=config.openai_base_url
        )

    elif provider_name == "mock":
        return MockProvider()

    else:
        logger.warning(f"Unknown provider '{provider_name}'. Defaulting to MockProvider.")
        return MockProvider()
