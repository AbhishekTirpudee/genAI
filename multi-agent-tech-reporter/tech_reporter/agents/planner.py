"""Planner Agent: Analyzes the technology domain and creates a structured research plan."""

from __future__ import annotations
import json
import re
from typing import Optional, List, Dict, Any
from tech_reporter.agents.base import BaseAgent, EventCallback
from tech_reporter.models import ResearchPlan, ResearchDimension
from tech_reporter.llm.base import LLMProvider

PLANNER_SYSTEM_INSTRUCTION = """You are a Principal Software Architect and Research Planner.
Your role is to formulate an exhaustive, multi-dimensional technical research plan for a given technology.

You must decompose the technology into 4 to 5 rigorous, distinct technical dimensions:
1. Core Architecture, Subsystems & Execution Model (Internals, memory, concurrency, dispatch)
2. Performance Characteristics, Benchmarks & Resource Footprint (p99 latency, throughput, scale)
3. Ecosystem Maturity, Developer Tooling & Production Adopters (SDKs, platforms, real-world case studies)
4. Operational Trade-offs, Security Model & Anti-Patterns (Failure modes, privilege, when NOT to use)
5. Comparative Evaluation against industry alternatives

You MUST output strictly valid JSON conforming to this schema:
{
  "technology": "<technology name>",
  "scope": "<scope description>",
  "target_audience": "<target audience>",
  "dimensions": [
    {
      "id": "<snake_case_id>",
      "title": "<Dimension Title>",
      "description": "<Detailed scope of what to investigate>",
      "key_questions": ["<question 1>", "<question 2>"],
      "search_queries": ["<search query 1>", "<search query 2>"]
    }
  ]
}
Do not include any conversational fluff, only valid JSON.
"""


class PlannerAgent(BaseAgent):
    """Orchestrates research strategy and scoping."""

    def __init__(self, llm: LLMProvider, event_callback: Optional[EventCallback] = None):
        super().__init__(
            name="PlannerAgent",
            role="Technical Research Strategist & Architect",
            llm=llm,
            event_callback=event_callback
        )

    def create_plan(
        self,
        technology: str,
        focus_areas: Optional[List[str]] = None,
        target_audience: str = "Principal Engineers & Systems Architects"
    ) -> ResearchPlan:
        """Formulates an in-depth research plan."""
        self.emit("think", f"Formulating technical research strategy for '{technology}'...")

        prompt = f"""Target Technology: {technology}
Target Audience: {target_audience}
"""
        if focus_areas:
            prompt += f"Special Focus Areas Requested: {', '.join(focus_areas)}\n"

        prompt += "\nFormulate the complete technical research plan with search queries in valid JSON."

        raw_response = self.llm.generate(
            prompt=prompt,
            system_instruction=PLANNER_SYSTEM_INSTRUCTION,
            temperature=0.2,
            json_mode=True
        )

        plan = self._parse_plan_json(raw_response, technology, target_audience)
        self.emit(
            "success",
            f"Formulated research plan with {len(plan.dimensions)} dimensions for '{technology}'.",
            {"dimensions": [d.title for d in plan.dimensions]}
        )
        return plan

    def _parse_plan_json(self, raw: str, technology: str, target_audience: str) -> ResearchPlan:
        """Robust parser handling JSON extraction from LLM response."""
        try:
            # Strip potential markdown code fences
            cleaned = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            data = json.loads(cleaned)
            return ResearchPlan.from_dict(data)
        except Exception as e:
            self.emit("warning", f"Failed to parse LLM plan JSON: {e}. Falling back to default dimensions.")
            return self._build_default_plan(technology, target_audience)

    def _build_default_plan(self, technology: str, target_audience: str) -> ResearchPlan:
        """Guaranteed fallback plan structure."""
        return ResearchPlan(
            technology=technology,
            scope="Comprehensive Deep Technical Evaluation",
            target_audience=target_audience,
            dimensions=[
                ResearchDimension(
                    id="arch_internals",
                    title="Architectural Internals & Execution Model",
                    description=f"Core subsystems, memory management, and runtime execution pipeline of {technology}.",
                    key_questions=[f"How is {technology} architected internally?", "What are its runtime execution guarantees?"],
                    search_queries=[f"{technology} architectural internals", f"{technology} execution model"]
                ),
                ResearchDimension(
                    id="perf_benchmarks",
                    title="Performance Characteristics & Benchmarks",
                    description=f"Throughput, p99 latency, and resource footprint of {technology}.",
                    key_questions=["What are the empirical performance benchmarks?", "What is the memory and CPU overhead?"],
                    search_queries=[f"{technology} benchmarks latency throughput", f"{technology} resource utilization"]
                ),
                ResearchDimension(
                    id="ecosystem_tooling",
                    title="Ecosystem, Tooling & Production Adopters",
                    description=f"Developer toolchains, SDKs, and enterprise case studies for {technology}.",
                    key_questions=["Who uses this in tier-1 production?", "What does the developer toolchain look like?"],
                    search_queries=[f"{technology} production case studies", f"{technology} developer tooling SDKs"]
                ),
                ResearchDimension(
                    id="tradeoffs_security",
                    title="Operational Trade-offs, Security & Anti-Patterns",
                    description=f"Security sandbox boundaries, operational failure modes, and when NOT to use {technology}.",
                    key_questions=["What are the primary operational risks?", "When should teams avoid adopting it?"],
                    search_queries=[f"{technology} security vulnerabilities limitations", f"{technology} failure modes"]
                )
            ]
        )
