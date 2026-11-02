"""Command Line Interface for Multi-Agent Technical Reporting System."""

from __future__ import annotations
import sys
import argparse
from pathlib import Path
from typing import List, Optional

from tech_reporter.config import AppConfig
from tech_reporter.orchestrator import MultiAgentOrchestrator
from tech_reporter.models import AgentEvent
from tech_reporter.web.server import start_server

# ANSI Color codes for zero-dependency terminal styling
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "blue": "\033[34m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "red": "\033[31m",
    "dim": "\033[2m",
}


def print_banner():
    banner = f"""
{COLORS['bold']}{COLORS['cyan']}╔════════════════════════════════════════════════════════════════════════╗
║             MULTI-AGENT TECHNICAL REPORT GENERATION SWARM              ║
║         Autonomous Research, Auditing & High-Density Reporting         ║
╚════════════════════════════════════════════════════════════════════════╝{COLORS['reset']}
"""
    print(banner)


def handle_event(event: AgentEvent):
    """Formats and prints agent events in real-time."""
    agent_colors = {
        "PlannerAgent": COLORS["blue"],
        "ResearchAgent": COLORS["green"],
        "ReviewerAgent": COLORS["yellow"],
        "ReportWritingAgent": COLORS["magenta"],
        "Orchestrator": COLORS["cyan"],
    }
    color = agent_colors.get(event.agent, COLORS["cyan"])
    badge = f"{color}[{event.agent}]{COLORS['reset']}"
    time_str = f"{COLORS['dim']}{event.timestamp}{COLORS['reset']}"

    prefix = "•"
    if event.event_type == "search":
        prefix = "🔍"
    elif event.event_type == "think":
        prefix = "🧠"
    elif event.event_type == "critique":
        prefix = "⚖️ "
    elif event.event_type == "write":
        prefix = "📝"
    elif event.event_type == "success":
        prefix = "✅"
    elif event.event_type == "warning":
        prefix = "⚠️ "
    elif event.event_type == "error":
        prefix = "❌"

    print(f" {time_str} {badge} {prefix} {event.message}")


def run_cli(args: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description="Multi-Agent Technical Report Generator: Orchestrates Research & Writer Agents to produce structured reports."
    )
    parser.add_argument(
        "technology",
        nargs="?",
        default=None,
        help="The technology to research and report on (e.g. 'eBPF', 'WebAssembly', 'Vector Databases')"
    )
    parser.add_argument(
        "--focus",
        type=str,
        default="",
        help="Comma-separated focus areas (e.g. 'Latency Benchmarks, Memory Model, Security Sandbox')"
    )
    parser.add_argument(
        "--audience",
        type=str,
        default="Principal Engineers & Systems Architects",
        help="Target audience for the technical report"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["auto", "gemini", "openai", "mock"],
        default=None,
        help="LLM provider override"
    )
    parser.add_argument(
        "--docs",
        "--doc",
        type=str,
        default=None,
        help="Path to custom reference document file or folder (e.g. 'sample_docs/')"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output directory path"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the interactive Web Studio dashboard"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Web server port (default: 8080)"
    )

    parsed = parser.parse_args(args)

    config = AppConfig.from_env()
    if parsed.provider:
        config.llm_provider = parsed.provider
    if parsed.out:
        config.output_dir = Path(parsed.out)
        config.output_dir.mkdir(parents=True, exist_ok=True)

    if parsed.serve:
        start_server(port=parsed.port, config=config)
        return

    if not parsed.technology:
        print_banner()
        print(f"{COLORS['yellow']}No technology specified.{COLORS['reset']}")
        print(f"Usage examples:")
        print(f"  python3 main.py \"eBPF in Cloud-Native Observability\"")
        print(f"  python3 main.py \"WebAssembly Serverless Architecture\" --focus \"Cold Starts, WASI 0.2\"")
        print(f"  python3 main.py --serve  (Launch Web Studio UI)\n")
        sys.exit(1)

    print_banner()
    print(f" {COLORS['bold']}Technology:{COLORS['reset']} {parsed.technology}")
    print(f" {COLORS['bold']}Target Audience:{COLORS['reset']} {parsed.audience}")
    if parsed.focus:
        print(f" {COLORS['bold']}Focus Areas:{COLORS['reset']} {parsed.focus}")
    if parsed.docs:
        print(f" {COLORS['bold']}Documents Ingested:{COLORS['reset']} {parsed.docs}")
    print(f" {COLORS['bold']}LLM Engine:{COLORS['reset']} {config.llm_provider}")
    print(f" {COLORS['bold']}Search Engine:{COLORS['reset']} {config.search_backend}")
    print(f" {COLORS['bold']}Output Directory:{COLORS['reset']} {config.output_dir.resolve()}\n")
    print(f"{COLORS['dim']}{'─'*72}{COLORS['reset']}")

    focus_list = [f.strip() for f in parsed.focus.split(",") if f.strip()] if parsed.focus else None

    orchestrator = MultiAgentOrchestrator(
        config=config,
        event_callback=handle_event
    )

    doc_paths = [parsed.docs] if parsed.docs else None

    report = orchestrator.run(
        technology=parsed.technology,
        focus_areas=focus_list,
        target_audience=parsed.audience,
        documents=doc_paths
    )

    print(f"{COLORS['dim']}{'─'*72}{COLORS['reset']}\n")
    print(f"{COLORS['bold']}{COLORS['green']}✨ SUCCESS: Technical Report Generated!{COLORS['reset']}")
    print(f" {COLORS['bold']}Title:{COLORS['reset']} {report.title}")
    print(f" {COLORS['bold']}Sections:{COLORS['reset']} {len(report.sections)}")
    print(f" {COLORS['bold']}Citations:{COLORS['reset']} {len(report.references)}\n")
    slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in report.technology.lower())
    print(f" 📄 Markdown Report: {COLORS['cyan']}{config.output_dir}/{slug}_report.md{COLORS['reset']}")
    print(f" 🌐 HTML Report:     {COLORS['cyan']}{config.output_dir}/{slug}_report.html{COLORS['reset']}")
    print(f" 📦 JSON Data:       {COLORS['cyan']}{config.output_dir}/{slug}_report.json{COLORS['reset']}\n")


if __name__ == "__main__":
    run_cli()
