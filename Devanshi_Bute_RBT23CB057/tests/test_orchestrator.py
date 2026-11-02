"""Unit tests for the end-to-end multi-agent orchestrator."""

import unittest
import tempfile
import shutil
from pathlib import Path
from tech_reporter.config import AppConfig
from tech_reporter.orchestrator import MultiAgentOrchestrator
from tech_reporter.models import AgentEvent


class TestOrchestrator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AppConfig(
            llm_provider="mock",
            output_dir=self.temp_dir,
            search_backend="mock"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_pipeline_run(self):
        events = []
        def capture_event(ev: AgentEvent):
            events.append(ev)

        orchestrator = MultiAgentOrchestrator(
            config=self.config,
            event_callback=capture_event
        )

        report = orchestrator.run(
            technology="eBPF in Cloud-Native Observability",
            focus_areas=["Socket Filtering", "Ring Buffer"],
            target_audience="Principal Infrastructure Architects"
        )

        self.assertIsNotNone(report)
        self.assertIn("eBPF", report.technology)
        self.assertGreater(len(report.markdown_content), 1000)

        # Check emitted events
        agents_seen = set(e.agent for e in events)
        self.assertIn("PlannerAgent", agents_seen)
        self.assertIn("ResearchAgent", agents_seen)
        self.assertIn("ReviewerAgent", agents_seen)
        self.assertIn("ReportWritingAgent", agents_seen)
        self.assertIn("Orchestrator", agents_seen)

        # Check saved files
        saved_files = list(self.temp_dir.glob("*"))
        self.assertEqual(len(saved_files), 3)  # .md, .html, .json
        suffixes = {f.suffix for f in saved_files}
        self.assertEqual(suffixes, {".md", ".html", ".json"})


if __name__ == "__main__":
    unittest.main()
