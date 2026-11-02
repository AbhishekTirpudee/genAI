from __future__ import annotations

import html
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def markdown_to_pdf(markdown: str) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="MarketMind AI research report",
    )
    styles = getSampleStyleSheet()
    story = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
            continue
        if line.startswith("# "):
            style = styles["Title"]
            line = line[2:]
        elif line.startswith("## "):
            style = styles["Heading1"]
            line = line[3:]
        elif line.startswith("### "):
            style = styles["Heading2"]
            line = line[4:]
        else:
            style = styles["BodyText"]
            if line.startswith("- "):
                line = "\u2022 " + line[2:]
            elif line.startswith("> "):
                line = line[2:]
                style = styles["Italic"]
        safe_line = html.escape(line).replace("**", "")
        story.append(Paragraph(safe_line, style))
        story.append(Spacer(1, 3))
    document.build(story)
    return output.getvalue()
