"""Unit tests for search and content tools."""

import unittest
from tech_reporter.tools.search import TechnicalSearchTool
from tech_reporter.tools.fetcher import HTMLTextExtractor


class TestTools(unittest.TestCase):

    def test_search_knowledge_bank_ebpf(self):
        tool = TechnicalSearchTool(backend="mock")
        results = tool.search("ebpf kernel architecture", max_results=3)
        self.assertGreater(len(results), 0)
        self.assertTrue(any("ebpf" in r.title.lower() or "ebpf" in r.snippet.lower() for r in results))

    def test_search_fallback_generation(self):
        tool = TechnicalSearchTool(backend="mock")
        results = tool.search("QuantumAnnealingFramework", max_results=2)
        self.assertEqual(len(results), 2)
        self.assertTrue(any("quantumannealingframework" in r.url.lower() for r in results))

    def test_html_text_extractor(self):
        raw_html = "<html><head><title>Test</title><style>body { color: red; }</style></head><body><h1>Heading</h1><p>Paragraph with <b>bold</b> text.</p><script>console.log(1);</script></body></html>"
        parser = HTMLTextExtractor()
        parser.feed(raw_html)
        text = parser.get_text()
        self.assertIn("Heading", text)
        self.assertIn("Paragraph with bold text.", text)
        self.assertNotIn("console.log", text)
        self.assertNotIn("color: red", text)


if __name__ == "__main__":
    unittest.main()
