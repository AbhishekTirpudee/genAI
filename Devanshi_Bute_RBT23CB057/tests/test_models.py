"""Unit tests for data models."""

import unittest
from tech_reporter.models import (
    ResearchSource,
    ResearchDimension,
    ResearchPlan,
    TechnicalFinding,
    ResearchDossier,
    ReviewFeedback,
    ReportSection,
    TechnicalReport
)


class TestModels(unittest.TestCase):

    def test_research_source_serialization(self):
        source = ResearchSource(
            url="https://example.com/ebpf-internals",
            title="eBPF Internals Specification",
            snippet="eBPF bytecode verifier and JIT compiler.",
            author_or_domain="example.com"
        )
        data = source.to_dict()
        self.assertEqual(data["url"], "https://example.com/ebpf-internals")
        self.assertEqual(data["title"], "eBPF Internals Specification")
        self.assertEqual(data["author_or_domain"], "example.com")

    def test_research_plan_serialization(self):
        dim = ResearchDimension(
            id="arch",
            title="Architecture",
            description="Internals",
            key_questions=["Q1", "Q2"],
            search_queries=["query 1"]
        )
        plan = ResearchPlan(
            technology="WebAssembly",
            scope="Deep Dive",
            target_audience="Engineers",
            dimensions=[dim]
        )
        data = plan.to_dict()
        reconstructed = ResearchPlan.from_dict(data)
        self.assertEqual(reconstructed.technology, "WebAssembly")
        self.assertEqual(len(reconstructed.dimensions), 1)
        self.assertEqual(reconstructed.dimensions[0].id, "arch")

    def test_technical_report_json(self):
        report = TechnicalReport(
            title="eBPF Architecture Report",
            technology="eBPF",
            executive_summary="Summary",
            target_audience="Architects",
            sections=[ReportSection(title="Overview", content="Body", slug="overview")],
            markdown_content="# eBPF Architecture Report\n\nBody"
        )
        json_str = report.to_json()
        self.assertIn("eBPF Architecture Report", json_str)
        self.assertIn("overview", json_str)


if __name__ == "__main__":
    unittest.main()
