from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.competitor import CompetitorAnalysisAgent
from backend.agents.customer_insights import CustomerInsightsAgent
from backend.agents.financial import FinancialAnalysisAgent
from backend.agents.market_research import MarketResearchAgent
from backend.agents.planner import ResearchPlannerAgent
from backend.agents.report_writer import ReportWriterAgent
from backend.agents.swot import SWOTAnalysisAgent
from backend.agents.verification import VerificationAgent
from backend.config import settings
from backend.schemas import AgentEvent, ResearchRequest, ResearchState
from backend.tools import DemoTools, ResearchTools

logger = logging.getLogger(__name__)
AGENT_NAMES = (
    "research_planner",
    "market_research",
    "competitor_analysis",
    "customer_insights",
    "swot_analysis",
    "financial_analysis",
    "report_writer",
)


class MarketMindGraph:
    """Seven independent agents, real LangGraph fan-out, and a bounded verification loop."""

    def __init__(self, tools: Any, on_event: Callable[[AgentEvent], None] | None = None):
        self.tools = tools
        self.on_event = on_event
        self._planner = ResearchPlannerAgent()
        self._market = MarketResearchAgent()
        self._competitors = CompetitorAnalysisAgent()
        self._customers = CustomerInsightsAgent()
        self._swot = SWOTAnalysisAgent()
        self._financial = FinancialAnalysisAgent()
        self._verifier = VerificationAgent()
        self._writer = ReportWriterAgent()
        self.graph = self._build()

    def _emit(self, name: str, status: str, message: str, iteration: int, elapsed: float | None = None) -> AgentEvent:
        event = AgentEvent(
            agent=name,
            status=status,
            message=message,
            duration_seconds=round(elapsed, 2) if elapsed is not None else None,
            iteration=iteration,
        )
        if self.on_event:
            self.on_event(event)
        return event

    def _execute(self, name: str, fn: Callable[[], dict[str, Any]], state: ResearchState) -> dict[str, Any]:
        iteration = state.get("iteration_count", 0)
        start = time.monotonic()
        running = self._emit(name, "running", "Agent execution started.", iteration)
        try:
            result = fn()
        except Exception as exc:
            elapsed = time.monotonic() - start
            message = f"{name} failed: {type(exc).__name__}: {exc}"
            logger.exception(message)
            failed = self._emit(name, "failed", message, iteration, elapsed)
            return {
                "events": [running, failed],
                "errors": [message],
            }

        elapsed = time.monotonic() - start
        completed = self._emit(
            name,
            "completed",
            f"Agent execution completed in {elapsed:.1f}s.",
            iteration,
            elapsed,
        )
        return {**result, "events": [running, completed]}

    def _build(self):
        builder = StateGraph(ResearchState)

        def planner(state: ResearchState) -> dict[str, Any]:
            result = self._execute(
                "research_planner",
                lambda: {
                    "plan": self._planner.run(state["request"], self.tools),
                    "used_queries": [],
                },
                state,
            )
            return result

        def market_research(state: ResearchState) -> dict[str, Any]:
            def execute():
                output, sources, calls = self._market.run(
                    request=state["request"],
                    plan=state["plan"],
                    sources=state.get("sources", []),
                    additional_queries=state.get("additional_queries", []),
                    search_calls_used=state.get("search_calls_used", 0),
                    tools=self.tools,
                )
                return {
                    "market_research": output,
                    "sources": sources,
                    "search_calls_used": state.get("search_calls_used", 0) + calls,
                }
            return self._execute("market_research", execute, state)

        def competitor_analysis(state: ResearchState) -> dict[str, Any]:
            return self._execute(
                "competitor_analysis",
                lambda: {
                    "competitors": self._competitors.run(
                        state["request"], state["plan"], state.get("sources", []), self.tools
                    )
                },
                state,
            )

        def customer_insights(state: ResearchState) -> dict[str, Any]:
            return self._execute(
                "customer_insights",
                lambda: {
                    "customers": self._customers.run(
                        state["request"], state["plan"], state.get("sources", []), self.tools
                    )
                },
                state,
            )

        def strategy_analyses(state: ResearchState) -> dict[str, Any]:
            del state
            return {}

        def fan_out(state: ResearchState) -> dict[str, Any]:
            del state
            return {}

        def swot_analysis(state: ResearchState) -> dict[str, Any]:
            return self._execute(
                "swot_analysis",
                lambda: {
                    "swot": self._swot.run(
                        state["request"],
                        state["plan"],
                        state.get("sources", []),
                        state["market_research"],
                        state["competitors"],
                        state["customers"],
                        self.tools,
                    )
                },
                state,
            )

        def financial_analysis(state: ResearchState) -> dict[str, Any]:
            return self._execute(
                "financial_analysis",
                lambda: {
                    "financial": self._financial.run(
                        state["request"],
                        state["plan"],
                        state.get("sources", []),
                        state["market_research"],
                        state["competitors"],
                        state["customers"],
                        self.tools,
                    )
                },
                state,
            )

        def verify(state: ResearchState) -> dict[str, Any]:
            return self._execute(
                "verification",
                lambda: {
                    "verification": self._verifier.run(
                        request=state["request"],
                        plan=state["plan"],
                        sources=state.get("sources", []),
                        market_research=state["market_research"],
                        competitors=state["competitors"],
                        customers=state["customers"],
                        swot=state["swot"],
                        financial=state["financial"],
                        iteration_count=state.get("iteration_count", 0),
                        tools=self.tools,
                    )
                },
                state,
            )

        def prepare_additional_research(state: ResearchState) -> dict[str, Any]:
            verification = state["verification"]
            used = set(state.get("used_queries", []))
            fresh = [
                query.strip()
                for query in verification.additional_search_queries
                if query.strip() and query.strip().casefold() not in {q.casefold() for q in used}
            ][:3]
            return {
                "iteration_count": state.get("iteration_count", 0) + 1,
                "additional_queries": fresh,
                "used_queries": state.get("used_queries", []) + fresh,
                "events": [
                    self._emit(
                        "orchestrator",
                        "info",
                        f"Verification found coverage gaps; routing {len(fresh)} new targeted searches.",
                        state.get("iteration_count", 0) + 1,
                    )
                ],
            }

        def report_writer(state: ResearchState) -> dict[str, Any]:
            return self._execute(
                "report_writer",
                lambda: {
                    "report": self._writer.run(
                        request=state["request"],
                        plan=state["plan"],
                        sources=state.get("sources", []),
                        market_research=state["market_research"],
                        competitors=state["competitors"],
                        customers=state["customers"],
                        swot=state["swot"],
                        financial=state["financial"],
                        verification=state["verification"],
                        tools=self.tools,
                    )
                },
                state,
            )

        def fail_workflow(state: ResearchState) -> dict[str, Any]:
            message = "; ".join(state.get("errors", [])) or "Research workflow failed."
            return {
                "workflow_failed": True,
                "events": [
                    self._emit(
                        "orchestrator",
                        "failed",
                        message,
                        state.get("iteration_count", 0),
                    )
                ],
            }

        builder.add_node("planner", planner)
        builder.add_node("market_research", market_research)
        builder.add_node("market_research_fanout", fan_out)
        builder.add_node("competitor_analysis", competitor_analysis)
        builder.add_node("customer_insights", customer_insights)
        builder.add_node("strategy_analyses", strategy_analyses)
        builder.add_node("strategy_fanout", fan_out)
        builder.add_node("swot_analysis", swot_analysis)
        builder.add_node("financial_analysis", financial_analysis)
        builder.add_node("verification", verify)
        builder.add_node("prepare_additional_research", prepare_additional_research)
        builder.add_node("report_writer", report_writer)
        builder.add_node("failure", fail_workflow)

        builder.add_edge(START, "planner")
        builder.add_conditional_edges(
            "planner",
            lambda state: "failure" if state.get("errors") else "continue",
            {"failure": "failure", "continue": "market_research"},
        )
        builder.add_conditional_edges(
            "market_research",
            lambda state: "failure" if state.get("errors") else "continue",
            {"failure": "failure", "continue": "market_research_fanout"},
        )
        builder.add_edge("market_research_fanout", "competitor_analysis")
        builder.add_edge("market_research_fanout", "customer_insights")
        builder.add_edge(["competitor_analysis", "customer_insights"], "strategy_analyses")
        builder.add_conditional_edges(
            "strategy_analyses",
            lambda state: "failure" if state.get("errors") else "continue",
            {
                "failure": "failure",
                "continue": "strategy_fanout",
            },
        )
        builder.add_edge("strategy_fanout", "swot_analysis")
        builder.add_edge("strategy_fanout", "financial_analysis")
        builder.add_edge(["swot_analysis", "financial_analysis"], "verification")
        builder.add_conditional_edges(
            "verification",
            self._verification_route,
            {
                "failure": "failure",
                "additional_research": "prepare_additional_research",
                "report": "report_writer",
            },
        )
        builder.add_edge("prepare_additional_research", "market_research")
        builder.add_conditional_edges(
            "report_writer",
            lambda state: "failure" if state.get("errors") else "done",
            {"failure": "failure", "done": END},
        )
        builder.add_edge("failure", END)
        return builder.compile()

    @staticmethod
    def _verification_route(state: ResearchState) -> str:
        if state.get("errors"):
            return "failure"
        request = state["request"]
        verification = state["verification"]
        iterations = state.get("iteration_count", 0)
        calls_remaining = settings.max_search_calls - state.get("search_calls_used", 0)
        sources_remaining = settings.max_sources - len(state.get("sources", []))
        has_new_queries = any(
            query.strip()
            and query.strip().casefold() not in {item.casefold() for item in state.get("used_queries", [])}
            for query in verification.additional_search_queries
        )
        if (
            not request.demo_mode
            and verification.gaps
            and has_new_queries
            and iterations < settings.max_research_iterations
            and calls_remaining > 0
            and sources_remaining > 0
        ):
            return "additional_research"
        return "report"

    def run(self, request: ResearchRequest) -> ResearchState:
        initial: ResearchState = {
            "request": request,
            "sources": [],
            "events": [],
            "errors": [],
            "search_calls_used": 0,
            "iteration_count": 0,
            "used_queries": [],
        }
        current: ResearchState | None = None
        for update in self.graph.stream(initial, stream_mode="values"):
            current = update
        if current is None:
            raise RuntimeError("The LangGraph research workflow produced no result.")
        if current.get("workflow_failed"):
            raise RuntimeError("; ".join(current.get("errors", [])) or "Research workflow failed.")
        if not current.get("report"):
            raise RuntimeError("Research workflow ended without generating a report.")
        return current


def build_research_graph(
    on_event: Callable[[AgentEvent], None] | None = None,
    tools: Any | None = None,
) -> MarketMindGraph:
    return MarketMindGraph(tools=tools or ResearchTools(), on_event=on_event)
