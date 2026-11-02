"""Unit tests for multi-agent workflows and individual agents."""

import unittest
from tech_reporter.llm.mock_provider import MockProvider
from tech_reporter.agents.planner import PlannerAgent
from tech_reporter.agents.researcher import ResearcherAgent
from tech_reporter.agents.reviewer import ReviewerAgent
from tech_reporter.agents.writer import ReportWritingAgent
from tech_reporter.models import AgentEvent


class TestAgents(unittest.TestCase):

    def setUp(self):
        self.llm = MockProvider()
        self.events = []

        def on_event(ev: AgentEvent):
            self.events.append(ev)

        self.on_event = on_event

    def test_planner_agent(self):
        planner = PlannerAgent(llm=self.llm, event_callback=self.on_event)
        plan = planner.create_plan(
            technology="eBPF",
            focus_areas=["Kernel Verifier", "Latency"]
        )
        self.assertEqual(plan.technology, "eBPF")
        self.assertGreaterEqual(len(plan.dimensions), 3)
        self.assertTrue(any(ev.agent == "PlannerAgent" for ev in self.events))

    def test_researcher_agent(self):
        planner = PlannerAgent(llm=self.llm)
        plan = planner.create_plan(technology="WebAssembly")

        researcher = ResearcherAgent(llm=self.llm, event_callback=self.on_event)
        dossier = researcher.conduct_research(plan)
        self.assertEqual(dossier.technology, "WebAssembly")
        self.assertGreaterEqual(len(dossier.findings), 1)
        self.assertGreaterEqual(len(dossier.all_sources), 1)

    def test_reviewer_agent(self):
        planner = PlannerAgent(llm=self.llm)
        plan = planner.create_plan(technology="Rust Tokio")
        researcher = ResearcherAgent(llm=self.llm)
        dossier = researcher.conduct_research(plan)

        reviewer = ReviewerAgent(llm=self.llm, event_callback=self.on_event)
        review = reviewer.review_dossier(dossier)
        self.assertGreaterEqual(review.score, 80)
        self.assertTrue(review.is_approved)

    def test_writer_agent(self):
        planner = PlannerAgent(llm=self.llm)
        plan = planner.create_plan(technology="Vector Databases")
        researcher = ResearcherAgent(llm=self.llm)
        dossier = researcher.conduct_research(plan)
        reviewer = ReviewerAgent(llm=self.llm)
        review = reviewer.review_dossier(dossier)

        writer = ReportWritingAgent(llm=self.llm, event_callback=self.on_event)
        report = writer.write_report(dossier, review)

        self.assertIn("Vector Databases", report.title)
        self.assertGreater(len(report.markdown_content), 500)
        self.assertGreater(len(report.sections), 2)


if __name__ == "__main__":
    unittest.main()
