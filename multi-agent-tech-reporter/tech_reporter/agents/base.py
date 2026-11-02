"""Base Agent class providing common interface and event telemetry."""

from __future__ import annotations
import logging
from typing import Callable, Optional, List, Dict, Any
from tech_reporter.models import AgentEvent
from tech_reporter.llm.base import LLMProvider

EventCallback = Callable[[AgentEvent], None]


class BaseAgent:
    """Foundational agent class with logging and event dispatching."""

    def __init__(
        self,
        name: str,
        role: str,
        llm: LLMProvider,
        event_callback: Optional[EventCallback] = None
    ):
        self.name = name
        self.role = role
        self.llm = llm
        self.event_callback = event_callback
        self.logger = logging.getLogger(f"agent.{name.lower()}")

    def emit(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Dispatches an AgentEvent to the registered listener."""
        event = AgentEvent(
            agent=self.name,
            event_type=event_type,
            message=message,
            details=details
        )
        self.logger.info(f"[{self.name}] {message}")
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception as e:
                self.logger.warning(f"Error in event callback: {e}")
