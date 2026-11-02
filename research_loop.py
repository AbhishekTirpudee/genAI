"""
Research Loop — Bounded feedback loop between verification and additional web research.

When the Verification Agent identifies critical gaps:
1. Targeted additional search queries are generated
2. Web Researcher fetches new evidence
3. Evidence is merged back into the research state
4. Verification Agent re-evaluates

Maximum 3 iterations (configurable via MAX_RESEARCH_ITERATIONS in .env).
"""

from __future__ import annotations

import logging

from config.settings import settings
from components.web_researcher import WebResearcherAgent
from components.verification_agent import VerificationAgent
from schemas.evidence import EvidenceRecord
from schemas.report import CoverageEvaluation, VerificationResult
from schemas.research import ResearchPlan, ResearchState, ResearchStatus

logger = logging.getLogger(__name__)


class ResearchLoop:
    """
    Implements the bounded research feedback loop.
    Prevents infinite loops via iteration_count tracking.
    Also prevents duplicate query execution by tracking seen queries.
    """

    def __init__(self, web_researcher: WebResearcherAgent, verifier: VerificationAgent):
        self._researcher = web_researcher
        self._verifier = verifier
        self._executed_queries: set[str] = set()

    def maybe_loop(
        self,
        plan: ResearchPlan,
        state: ResearchState,
        coverage: CoverageEvaluation,
        market_analysis,
        competitors,
    ) -> tuple[list[EvidenceRecord], list[VerificationResult], CoverageEvaluation]:
        """
        If coverage is insufficient and budget remains, execute one additional research iteration.

        Returns:
            (updated_evidence, updated_verification_results, updated_coverage)
        """
        if coverage.is_sufficient:
            logger.info("Research loop: coverage is sufficient — no additional loop needed")
            return state.evidence, state.verification_results, coverage

        if state.iteration_count >= state.request.limits.max_research_iterations:
            logger.warning(
                f"Research loop: maximum iterations ({state.request.limits.max_research_iterations}) reached"
            )
            state.add_event(
                "WARNING", "orchestrator",
                f"Research loop limit reached ({state.iteration_count} iterations). "
                "Generating best available report.",
            )
            coverage.is_sufficient = True  # Force completion
            return state.evidence, state.verification_results, coverage

        if not state.budget_remaining():
            logger.warning("Research loop: budget exhausted")
            state.add_event("WARNING", "orchestrator", "Research budget exhausted. Proceeding to report generation.")
            coverage.is_sufficient = True
            return state.evidence, state.verification_results, coverage

        # Identify new queries — filter out already executed ones
        new_queries = [
            q for q in coverage.additional_queries_needed
            if q.strip() not in self._executed_queries
        ]

        if not new_queries:
            logger.info("Research loop: no new queries to execute — forcing completion")
            coverage.is_sufficient = True
            return state.evidence, state.verification_results, coverage

        # Mark queries as executed to prevent re-running
        for q in new_queries:
            self._executed_queries.add(q.strip())

        state.iteration_count += 1
        state.add_event(
            "LOOP_ITERATION", "orchestrator",
            f"Research iteration {state.iteration_count}: executing {len(new_queries)} additional queries",
            {
                "iteration": state.iteration_count,
                "queries": new_queries,
                "gaps": coverage.critical_gaps,
            },
        )

        logger.info(
            f"Research loop iteration {state.iteration_count}: "
            f"executing {len(new_queries)} additional queries"
        )

        # Execute additional research
        new_evidence = self._researcher.research(
            plan=plan,
            state=state,
            additional_queries=new_queries,
        )

        # Merge new evidence
        existing_urls = {e.source_url for e in state.evidence}
        unique_new = [e for e in new_evidence if e.source_url not in existing_urls]
        state.evidence.extend(unique_new)

        logger.info(f"Research loop: added {len(unique_new)} new unique evidence records")

        # Re-run verification on updated evidence set
        updated_verification = self._verifier.verify(
            plan=plan,
            evidence=state.evidence,
            market_analysis=market_analysis,
            competitors=competitors,
            state=state,
        )
        state.verification_results = updated_verification

        # Re-evaluate coverage
        updated_coverage = self._verifier.evaluate_coverage(
            plan=plan,
            evidence=state.evidence,
            verification_results=updated_verification,
            state=state,
        )

        return state.evidence, updated_verification, updated_coverage
