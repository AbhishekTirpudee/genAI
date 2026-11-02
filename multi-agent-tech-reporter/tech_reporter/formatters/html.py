"""HTML report generator with modern styling, Mermaid diagrams, and print support."""

from __future__ import annotations
import re
import html
from tech_reporter.models import TechnicalReport


class HTMLFormatter:
    """Renders structured TechnicalReport into a standalone, styled HTML document."""

    @classmethod
    def render(cls, report: TechnicalReport) -> str:
        """Transforms a report into clean, responsive HTML."""
        body_html = cls._markdown_to_html(report.markdown_content)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(report.title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (window.mermaid) {{
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
      }}
    }});
  </script>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --border: #334155;
      --code-bg: #0b1120;
      --accent: #818cf8;
      --table-stripe: #1e293b;
      --success: #34d399;
    }}

    @media (prefers-color-scheme: light) {{
      :root {{
        --bg: #f8fafc;
        --card-bg: #ffffff;
        --text: #0f172a;
        --text-muted: #64748b;
        --primary: #0284c7;
        --primary-hover: #0369a1;
        --border: #e2e8f0;
        --code-bg: #f1f5f9;
        --accent: #6366f1;
        --table-stripe: #f8fafc;
        --success: #059669;
      }}
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.65;
      padding: 2rem 1rem;
    }}

    .container {{
      max-width: 960px;
      margin: 0 auto;
      background: var(--card-bg);
      padding: 3rem;
      border-radius: 16px;
      border: 1px solid var(--border);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }}

    .badge {{
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      margin-bottom: 1rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    h1 {{
      font-size: 2.25rem;
      font-weight: 800;
      color: var(--text);
      margin-bottom: 0.75rem;
      line-height: 1.25;
    }}

    h2 {{
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--primary);
      margin-top: 2.5rem;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }}

    h3 {{
      font-size: 1.2rem;
      font-weight: 600;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      color: var(--accent);
    }}

    p {{
      margin-bottom: 1.25rem;
      color: var(--text);
    }}

    ul, ol {{
      margin-bottom: 1.25rem;
      padding-left: 1.5rem;
    }}

    li {{
      margin-bottom: 0.5rem;
    }}

    hr {{
      border: 0;
      border-top: 1px solid var(--border);
      margin: 2rem 0;
    }}

    pre {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      overflow-x: auto;
      margin: 1.5rem 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.9rem;
    }}

    code {{
      background: var(--code-bg);
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.875em;
      border: 1px solid var(--border);
    }}

    pre code {{
      border: none;
      padding: 0;
    }}

    .mermaid {{
      background: var(--card-bg);
      padding: 1.5rem;
      border-radius: 8px;
      text-align: center;
      margin: 2rem 0;
      border: 1px solid var(--border);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
      font-size: 0.95rem;
    }}

    th, td {{
      padding: 0.75rem 1rem;
      text-align: left;
      border: 1px solid var(--border);
    }}

    th {{
      background-color: rgba(56, 189, 248, 0.08);
      font-weight: 600;
      color: var(--primary);
    }}

    tr:nth-child(even) {{
      background-color: var(--table-stripe);
    }}

    blockquote {{
      border-left: 4px solid var(--primary);
      padding-left: 1rem;
      margin: 1.5rem 0;
      font-style: italic;
      color: var(--text-muted);
    }}

    a {{
      color: var(--primary);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    .footer {{
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      font-size: 0.85rem;
      color: var(--text-muted);
      text-align: center;
    }}

    @media print {{
      body {{
        background: #ffffff;
        color: #000000;
        padding: 0;
      }}
      .container {{
        box-shadow: none;
        border: none;
        padding: 0;
        max-width: 100%;
      }}
      h2 {{
        page-break-before: auto;
      }}
      pre, table {{
        page-break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="badge">Multi-Agent Systems Research</div>
    {body_html}
    <div class="footer">
      Generated autonomously by Multi-Agent Technical Reporting System • Orchestrated with Research & Report-Writing Agents
    </div>
  </div>
</body>
</html>
"""

    @classmethod
    def _markdown_to_html(cls, md: str) -> str:
        """Converts Markdown elements to semantic HTML."""
        lines = md.splitlines()
        html_lines = []
        in_code_block = False
        code_lang = ""
        code_content = []
        in_table = False
        table_rows = []

        def flush_table():
            nonlocal in_table, table_rows
            if table_rows:
                out = ["<table>"]
                is_header = True
                for row in table_rows:
                    cols = [c.strip() for c in row.strip().strip("|").split("|")]
                    if all(re.match(r"^:?-+:?$", c) for c in cols):
                        continue  # skip separator line
                    tag = "th" if is_header else "td"
                    out.append("  <tr>" + "".join(f"<{tag}>{cls._inline_format(c)}</{tag}>" for c in cols) + "</tr>")
                    is_header = False
                out.append("</table>")
                html_lines.append("\n".join(out))
                table_rows = []
            in_table = False

        for line in lines:
            stripped = line.strip()

            # Handle code blocks & mermaid
            if stripped.startswith("```"):
                if in_table:
                    flush_table()

                if in_code_block:
                    in_code_block = False
                    raw_code = "\n".join(code_content)
                    if code_lang == "mermaid":
                        html_lines.append(f'<div class="mermaid">\n{html.escape(raw_code)}\n</div>')
                    else:
                        html_lines.append(f'<pre><code class="language-{code_lang}">{html.escape(raw_code)}</code></pre>')
                    code_content = []
                    code_lang = ""
                else:
                    in_code_block = True
                    code_lang = stripped[3:].strip().lower()
                continue

            if in_code_block:
                code_content.append(line)
                continue

            # Handle markdown tables
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                table_rows.append(stripped)
                continue
            elif in_table:
                flush_table()

            # Headers
            if stripped.startswith("### "):
                html_lines.append(f"<h3>{cls._inline_format(stripped[4:])}</h3>")
            elif stripped.startswith("## "):
                html_lines.append(f"<h2>{cls._inline_format(stripped[3:])}</h2>")
            elif stripped.startswith("# "):
                html_lines.append(f"<h1>{cls._inline_format(stripped[2:])}</h1>")
            # Horizontal rule
            elif stripped in ("---", "***", "___"):
                html_lines.append("<hr>")
            # Unordered lists
            elif stripped.startswith("- ") or stripped.startswith("* "):
                html_lines.append(f"<ul><li>{cls._inline_format(stripped[2:])}</li></ul>")
            # Ordered lists
            elif re.match(r"^\d+\.\s+", stripped):
                item_text = re.sub(r"^\d+\.\s+", "", stripped)
                html_lines.append(f"<ol><li>{cls._inline_format(item_text)}</li></ol>")
            # Blank line
            elif not stripped:
                html_lines.append("")
            # Paragraph
            else:
                html_lines.append(f"<p>{cls._inline_format(stripped)}</p>")

        if in_table:
            flush_table()

        output = "\n".join(html_lines)
        # Consolidate adjacent <ul><li> into single <ul>
        output = re.sub(r"</ul>\s*<ul>", "", output)
        output = re.sub(r"</ol>\s*<ol>", "", output)
        return output

    @classmethod
    def _inline_format(cls, text: str) -> str:
        """Processes inline bold, italic, code, and links."""
        t = html.escape(text)
        # Inline code `code`
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        # Bold **text**
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        # Italic *text*
        t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
        # Markdown links [title](url)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
        return t
