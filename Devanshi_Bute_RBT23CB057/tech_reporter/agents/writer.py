"""Report-Writing Agent: Synthesizes research into a structured, publication-grade technical report."""

from __future__ import annotations
import re
from typing import Optional, List, Dict, Any
from tech_reporter.agents.base import BaseAgent, EventCallback
from tech_reporter.models import (
    ResearchDossier,
    ReviewFeedback,
    TechnicalReport,
    ReportSection,
    ResearchSource
)
from tech_reporter.llm.base import LLMProvider

WRITER_SYSTEM_INSTRUCTION = """You are a World-Class Principal Technical Writer and Enterprise Systems Architect.
Your mandate is to craft an authoritative, rigorous, deep Technical Report in GitHub-flavored Markdown.

Structure the report with the following mandatory sections:
# Technical Architecture & Evaluation Report: <Technology Name>

**Document Version:** 1.0.0
**Target Audience:** Principal Engineers, Architects, and Engineering Leadership
**Date:** March 2026

---

## 1. Executive Summary
(High-density synthesis of what the technology is, why it matters, primary benefits, and overall verdict)

(Must include a Mermaid diagram illustrating high-level architecture or data flow)
```mermaid
graph TD
...
```

---

## 2. Problem Statement & Technical Motivation
(Historical context, what engineering pain points existed prior, context switching, scaling bottlenecks)

---

## 3. Architecture & Internal Execution Mechanics
### 3.1 Core Components & Subsystems
### 3.2 Memory Layout & Concurrency Primitives
### 3.3 Execution Pipeline & Control vs Data Plane

---

## 4. Empirical Performance & Benchmarks
(Detailed analysis of p50/p99 latency, throughput, memory footprint, accompanied by a clean Markdown comparison table)

| Metric | Baseline / Legacy | <Technology> | Delta |
| :--- | :--- | :--- | :--- |

---

## 5. Comparative Evaluation Matrix
(Side-by-side comparison table evaluating against 2-3 prominent alternative approaches across Security, Performance, Complexity, Operational Cost)

---

## 6. Reference Implementation & Production Code
(Idiomatic, realistic code snippet demonstrating a core pattern, error handling, or telemetry hook)
```<language>
...
```

---

## 7. Operational Trade-offs & Anti-Patterns
### 7.1 When TO Adopt
### 7.2 When NOT to Adopt (Anti-Patterns & Edge Cases)

---

## 8. Strategic Adoption Roadmap
(Phased implementation plan: POC -> Staging/Observability -> Tier-1 Production)

---

## 9. References & Further Reading
(Numbered citations with URLs and titles)

CRITICAL INSTRUCTIONS:
- Write with high technical density. Avoid fluffy buzzwords.
- Ensure the Mermaid diagram is syntactically valid.
- Format all tables with clean Markdown headers and alignment markers.
- Address the Reviewer's recommendations and incorporate all gathered benchmarks.
"""


class ReportWritingAgent(BaseAgent):
    """Produces the publication-grade technical report."""

    def __init__(self, llm: LLMProvider, event_callback: Optional[EventCallback] = None):
        super().__init__(
            name="ReportWritingAgent",
            role="Lead Technical Author & Systems Synthesizer",
            llm=llm,
            event_callback=event_callback
        )

    def write_report(
        self,
        dossier: ResearchDossier,
        review_feedback: Optional[ReviewFeedback] = None
    ) -> TechnicalReport:
        """Synthesizes the dossier and review into a TechnicalReport."""
        self.emit("write", f"Drafting comprehensive technical report for '{dossier.technology}'...")

        # Prepare compiled technical dossier text
        dossier_text = []
        for finding in dossier.findings:
            dossier_text.append(f"## DIMENSION: {finding.dimension_title}")
            dossier_text.append("Key Takeaways:\n" + "\n".join(f"- {t}" for t in finding.key_takeaways))
            dossier_text.append(f"Technical Mechanics:\n{finding.technical_details}")
            if finding.benchmarks_or_metrics:
                dossier_text.append("Benchmarks:\n" + "\n".join(f"- {m}" for m in finding.benchmarks_or_metrics))
            if finding.tradeoffs_and_challenges:
                dossier_text.append("Trade-offs:\n" + "\n".join(f"- {to}" for to in finding.tradeoffs_and_challenges))
            for cs in finding.code_snippets:
                dossier_text.append(f"Code Sample ({cs.get('language', 'text')} - {cs.get('caption', '')}):\n```{cs.get('language', '')}\n{cs.get('code', '')}\n```")
            dossier_text.append("\n" + "=" * 40 + "\n")

        review_guidance = ""
        if review_feedback:
            review_guidance = (
                f"Peer Reviewer Score: {review_feedback.score}/100\n"
                f"Peer Reviewer Strengths: {', '.join(review_feedback.strengths)}\n"
                f"Peer Reviewer Missing Aspects: {', '.join(review_feedback.missing_aspects)}\n"
                f"Peer Reviewer Recommendations: {', '.join(review_feedback.actionable_recommendations)}\n"
            )

        sources_text = "\n".join(
            f"[{i+1}] {s.title} ({s.url}) - {s.snippet[:120]}..."
            for i, s in enumerate(dossier.all_sources)
        )

        prompt = f"""Target Technology: {dossier.technology}
Target Audience: {dossier.plan.target_audience}

Peer Review Auditor Feedback:
{review_guidance or 'No auditor notes provided; adhere to maximal technical rigor.'}

Verified Research Findings:
{chr(10).join(dossier_text)}

Gathered Citations & Sources:
{sources_text if sources_text else 'None provided; generate canonical industry references.'}

Generate the complete, publication-grade Technical Report in Markdown following the required structure.
"""

        raw_markdown = self.llm.generate(
            prompt=prompt,
            system_instruction=WRITER_SYSTEM_INSTRUCTION,
            temperature=0.4
        )

        # Parse sections and structure
        report = self._build_report_object(dossier, raw_markdown)
        self.emit(
            "success",
            f"Technical report generated successfully ({len(report.markdown_content.splitlines())} lines, {len(report.sections)} sections).",
            {"sections_count": len(report.sections)}
        )
        return report

    def _build_report_object(self, dossier: ResearchDossier, markdown: str) -> TechnicalReport:
        """Extracts structured fields from the generated markdown."""
        title = f"Technical Architecture & Evaluation: {dossier.technology}"
        title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Extract executive summary
        exec_match = re.search(
            r"##\s+1\.\s+Executive Summary\s*\n(.*?)(?=\n##|\Z)",
            markdown,
            re.DOTALL
        )
        executive_summary = exec_match.group(1).strip() if exec_match else (
            f"Comprehensive technical architecture, performance evaluation, and adoption guide for {dossier.technology}."
        )

        # Parse main sections
        sections: List[ReportSection] = []
        raw_sections = re.split(r"\n(?=##\s+)", markdown)
        for s in raw_sections:
            s_clean = s.strip()
            if not s_clean or s_clean.startswith("# "):
                continue
            lines = s_clean.split("\n", 1)
            sec_header = lines[0].replace("##", "").strip()
            sec_body = lines[1].strip() if len(lines) > 1 else ""
            slug = re.sub(r"[^\w\s-]", "", sec_header.lower()).replace(" ", "-")
            sections.append(ReportSection(
                title=sec_header,
                content=sec_body,
                slug=slug
            ))

        return TechnicalReport(
            title=title,
            technology=dossier.technology,
            executive_summary=executive_summary,
            target_audience=dossier.plan.target_audience,
            sections=sections,
            references=dossier.all_sources,
            markdown_content=markdown
        )
