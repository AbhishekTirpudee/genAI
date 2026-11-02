from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.graph import MarketMindGraph
from backend.schemas import AgentEvent, ResearchRequest, ResearchState
from backend.tools import DemoTools, ResearchTools


class ResearchOrchestrator:
    def __init__(self, tools: Any | None = None, on_event: Callable[[AgentEvent], None] | None = None):
        self.tools = tools
        self.on_event = on_event

    def run(self, request: ResearchRequest) -> ResearchState:
        tools = self.tools or (DemoTools() if request.demo_mode else ResearchTools())
        try:
            workflow = MarketMindGraph(tools=tools, on_event=self.on_event)
            return workflow.run(request)
        finally:
            close = getattr(tools, "close", None)
            if close:
                close()
