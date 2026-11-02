"""Web content fetcher and HTML text extractor."""

from __future__ import annotations
import urllib.request
import urllib.error
from html.parser import HTMLParser
from typing import Optional


class HTMLTextExtractor(HTMLParser):
    """Simple parser to extract clean text from HTML documents."""

    def __init__(self):
        super().__init__()
        self._pieces = []
        self._ignore = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style", "noscript", "svg", "head"):
            self._ignore = True

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "noscript", "svg", "head"):
            self._ignore = False

    def handle_data(self, data):
        if not self._ignore:
            text = data.strip()
            if text:
                self._pieces.append(text)

    def get_text(self) -> str:
        return " ".join(self._pieces)


class DocumentFetcher:
    """Safely fetches and extracts readable text from web documents."""

    def __init__(self, timeout: int = 6):
        self.timeout = timeout

    def fetch_text(self, url: str, max_chars: int = 4000) -> Optional[str]:
        """Fetch and extract cleaned text from the specified URL."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MultiAgentTechReporter/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    return None

                raw_bytes = response.read(100_000)
                charset = response.headers.get_content_charset() or "utf-8"
                raw_text = raw_bytes.decode(charset, errors="replace")

                parser = HTMLTextExtractor()
                parser.feed(raw_text)
                clean_text = parser.get_text()
                return clean_text[:max_chars]
        except Exception:
            return None
