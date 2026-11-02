"""Unit tests for Markdown and HTML formatters."""

import unittest
from tech_reporter.models import TechnicalReport, ReportSection
from tech_reporter.formatters.markdown import MarkdownFormatter
from tech_reporter.formatters.html import HTMLFormatter


class TestFormatters(unittest.TestCase):

    def setUp(self):
        self.report = TechnicalReport(
            title="Technical Architecture Report: WebAssembly",
            technology="WebAssembly",
            executive_summary="WebAssembly enables near-native execution speed.",
            target_audience="Principal Engineers",
            sections=[
                ReportSection(title="1. Executive Summary", content="Executive Summary content", slug="1-executive-summary"),
                ReportSection(title="2. Architecture", content="Architecture details", slug="2-architecture"),
            ],
            markdown_content="# Technical Architecture Report: WebAssembly\n\n## 1. Executive Summary\nExecutive Summary content\n\n## 2. Architecture\nArchitecture details\n\n```mermaid\ngraph TD\nA-->B\n```\n\n| Col1 | Col2 |\n| :--- | :--- |\n| A    | B    |\n"
        )

    def test_markdown_formatter_adds_toc(self):
        formatted = MarkdownFormatter.format(self.report)
        self.assertIn("## Table of Contents", formatted)
        self.assertIn("[1. Executive Summary]", formatted)
        self.assertIn("[2. Architecture]", formatted)

    def test_html_formatter_renders_structure(self):
        rendered_html = HTMLFormatter.render(self.report)
        self.assertIn("<!DOCTYPE html>", rendered_html)
        self.assertIn("WebAssembly", rendered_html)
        self.assertIn('<div class="mermaid">', rendered_html)
        self.assertIn("<table>", rendered_html)
        self.assertIn("<th>Col1</th>", rendered_html)


if __name__ == "__main__":
    unittest.main()
