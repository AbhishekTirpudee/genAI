"""
MarketMind AI — Master Orchestrator
Coordinates all six specialist agents in the correct sequence.

Execution flow:
  1. ResearchPlannerAgent  → structured research plan
  2. WebResearcherAgent    → evidence collection
  3. CompetitorAnalystAgent → competitor discovery & profiling
  4. MarketAnalystAgent    → comprehensive market analysis
  5. VerificationAgent     → claim verification + coverage evaluation
  6. [Research Loop]       → bounded additional research (max 3 iterations)
  7. ReportWriterAgent     → final structured report
  8. Output saving         → JSON + Markdown files
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from config.settings import settings
from components.research_planner import ResearchPlannerAgent
from components.web_researcher import WebResearcherAgent
from components.competitor_analyst import CompetitorAnalystAgent
from components.market_analyst import MarketAnalystAgent
from components.verification_agent import VerificationAgent
from components.report_writer import ReportWriterAgent
from orchestration.state_manager import StateManager
from orchestration.research_loop import ResearchLoop
from schemas.report import FinalResearchReport
from schemas.research import ResearchRequest, ResearchState, ResearchStatus

logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """
    Central coordinator for the MarketMind AI agent pipeline.
    
    Usage:
        orchestrator = MasterOrchestrator()
        report = orchestrator.run(request, progress_callback=print)
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self._output_dir = output_dir or settings.OUTPUT_DIR
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Instantiate all agents
        self._planner = ResearchPlannerAgent()
        self._researcher = WebResearcherAgent()
        self._competitor_analyst = CompetitorAnalystAgent()
        self._market_analyst = MarketAnalystAgent()
        self._verifier = VerificationAgent()
        self._report_writer = ReportWriterAgent()

        # State management
        self._state_manager = StateManager(self._output_dir)
        self._loop = ResearchLoop(self._researcher, self._verifier)

        logger.info(
            f"MasterOrchestrator initialised | mode={'MOCK' if settings.MOCK_MODE else 'LIVE'} | "
            f"output={self._output_dir}"
        )

    def run(
        self,
        request: ResearchRequest,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> FinalResearchReport:
        """
        Execute the full autonomous research pipeline.

        Args:
            request: Validated ResearchRequest from the user
            progress_callback: Optional callable(message) for live progress updates

        Returns:
            FinalResearchReport — structured report with all findings
        """
        def emit(message: str) -> None:
            logger.info(message)
            if progress_callback:
                progress_callback(message)

        start_time = time.time()
        
        # ── Initialise shared state ──────────────────────────────────────────
        state = ResearchState(
            research_id="pending",  # filled after planning
            request=request,
            status=ResearchStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        emit(f"\n{'='*60}")
        emit(f"  MarketMind AI — Research Run: {state.run_id[:8]}")
        emit(f"  Query: {request.query}")
        emit(f"  Mode: {'🔴 MOCK' if settings.MOCK_MODE else '🟢 LIVE'}")
        emit(f"{'='*60}\n")

        try:
            # ── STEP 1: Research Planning ────────────────────────────────────
            self._state_manager.transition(
                state, ResearchStatus.PLANNING, "orchestrator", "Creating research plan"
            )
            emit("📋 STEP 1/7 — Research Planner: analysing your query...")

            plan = self._planner.plan(request)
            state.research_id = plan.research_id
            state.plan = plan

            emit(f"   ✓ Plan: {plan.research_objective[:80]}")
            emit(f"   ✓ Industry: {plan.industry} | Geography: {plan.geography}")
            emit(f"   ✓ Search queries: {len(plan.search_queries)}")
            emit(f"   ✓ Required agents: {', '.join(plan.required_agents)}")

            self._state_manager.save(state, "01_planned")

            # ── STEP 2: Web Research ─────────────────────────────────────────
            self._state_manager.transition(
                state, ResearchStatus.RESEARCHING, "orchestrator", "Collecting web evidence"
            )
            emit("\n🌐 STEP 2/7 — Web Researcher: searching the internet...")

            evidence = self._researcher.research(plan=plan, state=state)
            state.evidence = evidence

            emit(f"   ✓ Evidence collected: {len(evidence)} records")
            emit(f"   ✓ Search calls used: {state.search_calls_used}")
            emit(f"   ✓ Unique sources: {state.sources_collected}")

            self._state_manager.save(state, "02_researched")

            # ── STEP 3: Competitor Analysis ──────────────────────────────────
            emit("\n🏆 STEP 3/7 — Competitor Analyst: discovering competitors...")

            competitors, comparison = self._competitor_analyst.analyse(
                plan=plan, evidence=evidence, state=state
            )
            state.competitors = competitors

            emit(f"   ✓ Competitors discovered: {len(competitors)}")
            if competitors:
                emit(f"   ✓ Profiles: {', '.join(c.name for c in competitors[:5])}")
            emit(f"   ✓ Market gaps identified: {len(comparison.market_gaps)}")

            self._state_manager.save(state, "03_competitors")

            # ── STEP 4: Market Analysis ──────────────────────────────────────
            self._state_manager.transition(
                state, ResearchStatus.ANALYSING, "orchestrator", "Performing market analysis"
            )
            emit("\n📊 STEP 4/7 — Market Analyst: analysing industry and market...")

            market_analysis = self._market_analyst.analyse(
                plan=plan, evidence=evidence, state=state
            )
            state.market_analysis = market_analysis

            emit(f"   ✓ Market definition: {market_analysis.market_definition[:60]}...")
            if market_analysis.tam.value:
                emit(f"   ✓ TAM: {market_analysis.tam.value} {market_analysis.tam.unit} "
                     f"({'verified' if market_analysis.tam.is_verified else 'estimated'})")
            emit(f"   ✓ SWOT: {'✓' if market_analysis.swot else '✗'} | "
                 f"PESTLE: {'✓' if market_analysis.pestle else '✗'} | "
                 f"Porter's: {'✓' if market_analysis.porters_five_forces else '✗'}")

            self._state_manager.save(state, "04_market_analysed")

            # ── STEP 5: Verification ─────────────────────────────────────────
            self._state_manager.transition(
                state, ResearchStatus.VERIFYING, "orchestrator", "Verifying research findings"
            )
            emit("\n✅ STEP 5/7 — Verification Agent: validating claims...")

            verification_results = self._verifier.verify(
                plan=plan,
                evidence=evidence,
                market_analysis=market_analysis,
                competitors=competitors,
                state=state,
            )
            state.verification_results = verification_results

            # Evaluate coverage
            coverage = self._verifier.evaluate_coverage(
                plan=plan,
                evidence=evidence,
                verification_results=verification_results,
                state=state,
            )

            verified = sum(1 for r in verification_results if r.status.value == "VERIFIED")
            partial = sum(1 for r in verification_results if r.status.value == "PARTIALLY_VERIFIED")
            unverified = sum(1 for r in verification_results if r.status.value == "UNVERIFIED")
            conflicting = sum(1 for r in verification_results if r.status.value == "CONFLICTING")

            emit(f"   ✓ Claims verified: {verified} | Partial: {partial} | "
                 f"Unverified: {unverified} | Conflicting: {conflicting}")
            emit(f"   ✓ Coverage score: {coverage.coverage_score:.1%}")
            emit(f"   ✓ Sufficient: {'Yes' if coverage.is_sufficient else 'No — triggering research loop'}")

            self._state_manager.save(state, "05_verified")

            # ── STEP 6: Research Loop (bounded) ──────────────────────────────
            loop_count = 0
            while not coverage.is_sufficient:
                loop_count += 1
                emit(f"\n🔄 STEP 6/7 — Research Loop iteration {loop_count}...")
                emit(f"   Gaps: {', '.join(coverage.critical_gaps[:3])}")

                evidence, verification_results, coverage = self._loop.maybe_loop(
                    plan=plan,
                    state=state,
                    coverage=coverage,
                    market_analysis=market_analysis,
                    competitors=competitors,
                )

                emit(f"   ✓ New total evidence: {len(evidence)} records")
                emit(f"   ✓ Updated coverage: {coverage.coverage_score:.1%}")

                if coverage.is_sufficient:
                    emit("   ✓ Coverage now sufficient — proceeding to report")
                    break

                if state.iteration_count >= state.request.limits.max_research_iterations:
                    emit("   ⚠ Research iteration limit reached — generating best available report")
                    break

            self._state_manager.save(state, "06_loop_done")

            # ── STEP 7: Report Generation ─────────────────────────────────────
            self._state_manager.transition(
                state, ResearchStatus.WRITING, "orchestrator", "Generating final report"
            )
            emit("\n📝 STEP 7/7 — Report Writer: generating final research report...")

            report = self._report_writer.write(
                plan=plan,
                evidence=evidence,
                competitors=competitors,
                competitor_comparison=comparison,
                market_analysis=market_analysis,
                verification_results=verification_results,
                state=state,
            )
            state.final_report = report

            # ── Save outputs ──────────────────────────────────────────────────
            output_paths = self._save_outputs(report, state)

            elapsed = time.time() - start_time
            state.status = ResearchStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            self._state_manager.save(state, "final")

            emit(f"\n{'='*60}")
            emit(f"  ✅ Research Complete!")
            emit(f"  Run ID: {state.run_id[:8]}")
            emit(f"  Duration: {elapsed:.1f}s")
            emit(f"  Sources: {report.total_sources} | Verified: {report.verified_claims}")
            emit(f"  Coverage: {report.coverage_score:.1%}")
            emit(f"\n  📄 Outputs saved:")
            for label, path in output_paths.items():
                emit(f"     {label}: {path}")
            emit(f"{'='*60}\n")

            return report

        except Exception as exc:
            elapsed = time.time() - start_time
            state.status = ResearchStatus.FAILED
            state.errors.append(str(exc))
            state.completed_at = datetime.utcnow()
            self._state_manager.save(state, "failed")

            logger.error(f"Research run failed after {elapsed:.1f}s: {exc}", exc_info=True)
            emit(f"\n❌ Research failed: {exc}")
            raise

    def _save_outputs(self, report: FinalResearchReport, state: ResearchState) -> dict[str, Path]:
        """Save all output files and return their paths."""
        run_prefix = state.run_id[:8]
        paths = {}

        # 1. Markdown report
        md_path = self._output_dir / f"research_report_{run_prefix}.md"
        md_path.write_text(report.to_markdown(), encoding="utf-8")
        paths["Markdown Report"] = md_path

        # 2. Full JSON report (for dashboard / API)
        json_path = self._output_dir / f"research_report_{run_prefix}.json"
        report_dict = report.model_dump(mode="json", exclude_none=True)

        def json_default(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump(mode="json")
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            return str(obj)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, default=json_default)
        paths["JSON Report"] = json_path

        # 3. Sources JSON
        sources = []
        for ev in state.evidence:
            sources.append({
                "title": ev.source_title,
                "url": ev.source_url,
                "publisher": ev.publisher,
                "published_date": ev.publication_date,
                "category": ev.research_category.value,
                "confidence": ev.confidence,
                "is_mock": ev.is_mock,
            })
        sources_path = self._output_dir / f"research_sources_{run_prefix}.json"
        with open(sources_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2)
        paths["Sources JSON"] = sources_path

        # 4. Competitor analysis JSON
        competitors_data = []
        for comp in state.competitors:
            competitors_data.append(
                comp.model_dump(mode="json", exclude={"evidence_ids", "run_id"}, exclude_none=True)
            )
        comp_path = self._output_dir / f"competitor_analysis_{run_prefix}.json"
        with open(comp_path, "w", encoding="utf-8") as f:
            json.dump(competitors_data, f, indent=2, default=str)
        paths["Competitor Analysis JSON"] = comp_path

        # 5. Most-recent symlinks (always points to latest run)
        for label, src_path in [
            ("research_report.md", md_path),
            ("research_report.json", json_path),
            ("research_sources.json", sources_path),
            ("competitor_analysis.json", comp_path),
        ]:
            latest = self._output_dir / label
            try:
                latest.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

        return paths
