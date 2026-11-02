"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class LLMProvider(ABC):
    """Abstract Base Class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        """Generate text from the LLM given a prompt and optional system instruction."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the underlying model."""
        pass
