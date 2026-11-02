"""Markdown formatter and sanitizer for technical reports."""

from __future__ import annotations
import re
from tech_reporter.models import TechnicalReport


class MarkdownFormatter:
    """Enhances and ensures structural integrity of markdown reports."""

    @staticmethod
    def format(report: TechnicalReport) -> str:
        """Produces a pristine markdown document with table of contents and metadata."""
        content = report.markdown_content.strip()

        # Build Table of Contents if not already present
        if "## Table of Contents" not in content and report.sections:
            toc_lines = ["## Table of Contents\n"]
            for s in report.sections:
                anchor = re.sub(r"[^\w\s-]", "", s.title.lower()).replace(" ", "-")
                toc_lines.append(f"- [{s.title}](#{anchor})")
            toc_text = "\n".join(toc_lines) + "\n\n---\n"

            # Insert TOC after Executive Summary or Title
            if "## 1. Executive Summary" in content:
                content = content.replace("## 1. Executive Summary", f"{toc_text}\n## 1. Executive Summary", 1)
            else:
                parts = content.split("---", 1)
                if len(parts) > 1:
                    content = f"{parts[0]}---\n\n{toc_text}\n{parts[1]}"
                else:
                    content = f"{toc_text}\n\n{content}"

        return content
