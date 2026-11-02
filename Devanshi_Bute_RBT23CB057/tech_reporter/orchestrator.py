"""Multi-Agent Orchestrator managing agent collaboration lifecycle."""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, List, Callable, Dict, Any

from tech_reporter.config import AppConfig
from tech_reporter.models import (
    ResearchPlan,
    ResearchDossier,
    ReviewFeedback,
    TechnicalReport,
    ResearchSource,
    AgentEvent
)
from tech_reporter.llm.factory import create_llm_provider
from tech_reporter.tools.search import TechnicalSearchTool
from tech_reporter.tools.fetcher import DocumentFetcher
from tech_reporter.agents.planner import PlannerAgent
from tech_reporter.agents.researcher import ResearcherAgent
from tech_reporter.agents.reviewer import ReviewerAgent
from tech_reporter.agents.writer import ReportWritingAgent
from tech_reporter.formatters.markdown import MarkdownFormatter
from tech_reporter.formatters.html import HTMLFormatter

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Coordinates Planner, Researcher, Reviewer, and Writer agents."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        event_callback: Optional[Callable[[AgentEvent], None]] = None
    ):
        self.config = config or AppConfig.from_env()
        self.event_callback = event_callback
        self.events: List[AgentEvent] = []

        # LLM Engine
        self.llm = create_llm_provider(self.config)

        # Tools
        self.search_tool = TechnicalSearchTool(backend=self.config.search_backend)
        self.fetcher = DocumentFetcher()

        # Agents
        self.planner = PlannerAgent(llm=self.llm, event_callback=self._handle_event)
        self.researcher = ResearcherAgent(
            llm=self.llm,
            search_tool=self.search_tool,
            fetcher=self.fetcher,
            event_callback=self._handle_event
        )
        self.reviewer = ReviewerAgent(llm=self.llm, event_callback=self._handle_event)
        self.writer = ReportWritingAgent(llm=self.llm, event_callback=self._handle_event)

    def _handle_event(self, event: AgentEvent) -> None:
        """Internal event bus dispatching to callers and storing trajectory."""
        self.events.append(event)
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception as e:
                logger.warning(f"Error in external event callback: {e}")

    def run(
        self,
        technology: str,
        focus_areas: Optional[List[str]] = None,
        target_audience: str = "Principal Engineers & Systems Architects",
        documents: Optional[List[str | Path]] = None
    ) -> TechnicalReport:
        """Executes the complete multi-agent research and report generation pipeline."""
        custom_sources: List[ResearchSource] = []
        if documents:
            for doc_item in documents:
                p = Path(doc_item)
                if p.is_dir():
                    for subfile in sorted(p.glob("*")):
                        if subfile.is_file() and subfile.suffix.lower() in (".txt", ".md", ".json", ".log"):
                            src = self._load_local_document(subfile)
                            if src:
                                custom_sources.append(src)
                elif p.is_file():
                    src = self._load_local_document(p)
                    if src:
                        custom_sources.append(src)

        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="info",
            message=f"Starting multi-agent workflow for technology: '{technology}' using LLM provider [{self.llm.model_name}]" + (f" with {len(custom_sources)} ingested reference documents" if custom_sources else "")
        ))

        # Phase 1: Research Planning
        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="think",
            message="Phase 1/4: Dispatching research scoping task to Planner Agent..."
        ))
        plan: ResearchPlan = self.planner.create_plan(
            technology=technology,
            focus_areas=focus_areas,
            target_audience=target_audience
        )

        # Phase 2: Technical Investigation & Evidence Gathering
        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="search",
            message=f"Phase 2/4: Dispatching deep technical exploration to Research Agent ({len(plan.dimensions)} dimensions)..."
        ))
        dossier: ResearchDossier = self.researcher.conduct_research(plan, custom_sources=custom_sources)

        # Phase 3: Peer Review & Quality Audit Gate
        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="critique",
            message="Phase 3/4: Submitting technical research dossier to Reviewer Agent for quality audit..."
        ))
        review: ReviewFeedback = self.reviewer.review_dossier(dossier)

        # Phase 4: Report Synthesis & Drafting
        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="write",
            message="Phase 4/4: Commissioning Report-Writing Agent to synthesize final publication-grade technical report..."
        ))
        report: TechnicalReport = self.writer.write_report(dossier, review)

        # Polish and format
        report.markdown_content = MarkdownFormatter.format(report)
        report.html_content = HTMLFormatter.render(report)

        # Save artifacts
        self._save_outputs(report)

        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="success",
            message=f"Multi-agent workflow successfully completed for '{technology}'!",
            details={
                "report_title": report.title,
                "sections": len(report.sections),
                "sources": len(report.references)
            }
        ))

        return report

    def _load_local_document(self, file_path: Path) -> Optional[ResearchSource]:
        """Reads a local file and structures it as a grounded ResearchSource."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if not content:
                return None
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            first_line = lines[0].replace("#", "").strip() if lines else file_path.name
            snippet = content[:2000]
            return ResearchSource(
                url=f"local://{file_path.name}",
                title=f"Local Reference: {first_line[:60]}",
                snippet=snippet,
                author_or_domain="local_document"
            )
        except Exception as e:
            logger.warning(f"Failed to read local document {file_path}: {e}")
            return None

    def _save_outputs(self, report: TechnicalReport) -> Dict[str, Path]:
        """Persists generated report in Markdown, HTML, and JSON formats."""
        slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in report.technology.lower())
        out_dir = self.config.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        md_path = out_dir / f"{slug}_report.md"
        html_path = out_dir / f"{slug}_report.html"
        json_path = out_dir / f"{slug}_report.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report.markdown_content)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(report.html_content)

        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.to_json())

        self._handle_event(AgentEvent(
            agent="Orchestrator",
            event_type="info",
            message=f"Artifacts exported:\n- Markdown: {md_path}\n- HTML: {html_path}\n- JSON: {json_path}"
        ))

        return {"markdown": md_path, "html": html_path, "json": json_path}
