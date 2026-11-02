"""
Orchestration State Manager
Maintains the shared ResearchState across all agents and persists it to JSON.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.research import ResearchState, ResearchStatus

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages the lifecycle of a ResearchState object.
    Persists state to disk at each milestone for recovery and inspection.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: ResearchState, label: str = "checkpoint") -> Path:
        """Save state to JSON file. Returns the path."""
        filename = f"state_{state.run_id}_{label}.json"
        path = self.output_dir / filename

        # Convert state to JSON-serialisable dict
        state_dict = state.model_dump(mode="json", exclude_none=False)

        # Ensure datetime fields are serialised
        def default_serialiser(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, "model_dump"):
                return obj.model_dump(mode="json")
            return str(obj)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, default=default_serialiser)

        logger.debug(f"State saved: {path}")
        return path

    def load(self, path: Path) -> ResearchState:
        """Load state from JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return ResearchState(**data)

    def transition(
        self,
        state: ResearchState,
        new_status: ResearchStatus,
        agent: str,
        message: str,
    ) -> ResearchState:
        """Transition state to a new status and log the event."""
        old_status = state.status
        state.status = new_status
        state.add_event(
            event_type="STATUS_CHANGE",
            agent=agent,
            message=message,
            data={"from": old_status.value, "to": new_status.value},
        )
        logger.info(f"[{state.run_id[:8]}] {old_status.value} → {new_status.value}: {message}")
        return state
