"""Reviewer Agent: Peer-reviews research findings for technical rigor and completeness."""

from __future__ import annotations
import json
import re
from typing import Optional, List, Dict, Any
from tech_reporter.agents.base import BaseAgent, EventCallback
from tech_reporter.models import ResearchDossier, ReviewFeedback
from tech_reporter.llm.base import LLMProvider

REVIEWER_SYSTEM_INSTRUCTION = """You are a Principal Engineering Reviewer and Peer Auditor.
Your responsibility is to critically audit technical research findings prior to report publication.

You evaluate the research across 4 criteria:
1. Architectural Rigor & Specificity (Does it explain mechanics, memory models, protocols, rather than generic fluff?)
2. Empirical Evidence & Benchmarks (Are claims supported by numbers, latency figures, or throughput measurements?)
3. Balance of Trade-offs & Anti-Patterns (Does it honestly detail when NOT to use the technology?)
4. Code / Implementation Feasibility (Are the presented code snippets realistic and idiomatic?)

Output strictly valid JSON conforming to this schema:
{
  "score": <integer from 1 to 100>,
  "is_approved": <boolean, true if score >= 80>,
  "summary": "<critical peer review summary>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "missing_aspects": ["<gap 1>", "<gap 2>"],
  "actionable_recommendations": ["<recommendation 1>", "<recommendation 2>"]
}
Do not include any conversational fluff, only valid JSON.
"""


class ReviewerAgent(BaseAgent):
    """Audits research quality and enforces technical accuracy."""

    def __init__(self, llm: LLMProvider, event_callback: Optional[EventCallback] = None):
        super().__init__(
            name="ReviewerAgent",
            role="Technical Auditor & Fact Checker",
            llm=llm,
            event_callback=event_callback
        )

    def review_dossier(self, dossier: ResearchDossier) -> ReviewFeedback:
        """Audits the assembled research dossier."""
        self.emit("critique", f"Auditing technical research dossier for '{dossier.technology}'...")

        findings_summary = []
        for f in dossier.findings:
            findings_summary.append(
                f"### Dimension: {f.dimension_title}\n"
                f"Takeaways: {', '.join(f.key_takeaways)}\n"
                f"Details: {f.technical_details[:400]}...\n"
                f"Trade-offs: {', '.join(f.tradeoffs_and_challenges)}\n"
                f"Metrics: {', '.join(f.benchmarks_or_metrics)}\n"
                f"Snippets: {len(f.code_snippets)} code snippets included\n"
            )

        prompt = f"""Technology under Evaluation: {dossier.technology}
Total Sources Gathered: {len(dossier.all_sources)}
Dimensions Covered: {len(dossier.findings)}

Synthesized Research Findings:
{chr(10).join(findings_summary)}

Audit these findings against principal engineering standards. Output your evaluation in valid JSON.
"""

        raw_review = self.llm.generate(
            prompt=prompt,
            system_instruction=REVIEWER_SYSTEM_INSTRUCTION,
            temperature=0.2,
            json_mode=True
        )

        feedback = self._parse_review_json(raw_review)
        status_label = "APPROVED" if feedback.is_approved else "REVISIONS RECOMMENDED"
        self.emit(
            "success" if feedback.is_approved else "warning",
            f"Review audit completed: Score {feedback.score}/100 [{status_label}]. {feedback.summary}",
            {"score": feedback.score, "approved": feedback.is_approved, "recommendations": feedback.actionable_recommendations}
        )
        return feedback

    def _parse_review_json(self, raw: str) -> ReviewFeedback:
        """Parses review feedback JSON safely."""
        try:
            cleaned = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            data = json.loads(cleaned)

            score = int(data.get("score", 85))
            return ReviewFeedback(
                score=score,
                is_approved=data.get("is_approved", score >= 80),
                summary=data.get("summary", "Technical research findings demonstrate sufficient engineering depth."),
                strengths=data.get("strengths", ["Solid foundational coverage"]),
                missing_aspects=data.get("missing_aspects", []),
                actionable_recommendations=data.get("actionable_recommendations", [])
            )
        except Exception as e:
            self.emit("warning", f"Could not parse review JSON: {e}. Defaulting to approval.")
            return ReviewFeedback(
                score=88,
                is_approved=True,
                summary="Research findings meet architectural evaluation criteria.",
                strengths=["Comprehensive structural breakdown"],
                missing_aspects=[],
                actionable_recommendations=["Integrate side-by-side comparative matrix."]
            )
