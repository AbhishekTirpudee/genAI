import sys
import os
import re
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr.encoding.lower() != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from scholar_rag.config import config
from scholar_rag.vector_store import vector_index
from scholar_rag.rag_engine import rag_engine
from scholar_rag.study_assistant import study_assistant
from scholar_rag.ui import (
    console,
    print_banner,
    print_help,
    print_documents_table,
    print_sources,
    print_flashcards_table,
)


def handle_interactive_repl():
    """Main interactive REPL shell for ScholarRAG."""
    print_banner()

    # Prompt if no documents indexed
    if not vector_index.chunks:
        console.print(
            Panel(
                "[bold yellow]No academic notes found in index yet![/bold yellow]\n"
                "To get started, upload your PDF notes using: [bold green]/upload <path/to/notes.pdf>[/bold green]\n"
                "Or run the included sample generator: [bold cyan]python sample_data/create_sample_pdf.py[/bold cyan]",
                title="[bold yellow]Welcome New Student[/bold yellow]",
                border_style="yellow",
            )
        )

    while True:
        try:
            raw_input = Prompt.ask("\n[bold cyan]ScholarBot[/bold cyan] [green]>[/green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Goodbye! Happy studying![/bold yellow]")
            break

        if not raw_input:
            continue

        # Clean copy-pasted prompts like 'ScholarBot > /upload' or ': /upload'
        user_input = re.sub(r"^scholarbot\s*[>:]*\s*", "", raw_input, flags=re.IGNORECASE).strip()
        user_input = user_input.lstrip(":").strip()

        # Auto-detect if user pasted a PDF file path directly
        clean_path = user_input.strip('"').strip("'")
        if (clean_path.lower().endswith(".pdf") or Path(clean_path).is_file()) and Path(clean_path).exists():
            user_input = f"/upload {clean_path}"

        cmd = user_input.lower()

        # Handle commands
        if cmd in ["exit", "quit", "/exit", "/quit"]:
            console.print("[bold yellow]Goodbye! Happy studying![/bold yellow]")
            break

        elif cmd in ["/help", "help", "?"]:
            print_help()

        elif cmd == "/docs":
            print_documents_table(vector_index.documents)

        elif user_input.startswith("/upload"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Usage: /upload <path_to_pdf_or_folder>[/red]")
                continue
            path_str = parts[1].strip().strip('"').strip("'")
            try:
                stats = rag_engine.ingest_path(path_str)
                console.print(
                    Panel(
                        f"[bold green]✓ Successfully Ingested Notes![/bold green]\n"
                        f"• Documents: {len(stats['processed_docs'])}\n"
                        f"• Total Pages: {stats['total_pages']}\n"
                        f"• Text Chunks Indexed: {stats['total_chunks']}",
                        title="[bold green]Ingestion Complete[/bold green]",
                        border_style="green",
                    )
                )
            except Exception as e:
                console.print(f"[bold red]Ingestion error: {e}[/bold red]")

        elif user_input.startswith("/remove"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Usage: /remove <filename>[/red]")
                continue
            fname = parts[1].strip()
            if vector_index.remove_document(fname):
                console.print(f"[green]Removed document '{fname}' from index.[/green]")
            else:
                console.print(f"[yellow]Document '{fname}' not found in index.[/yellow]")

        elif user_input.startswith("/summary"):
            parts = user_input.split(maxsplit=1)
            doc_name = parts[1].strip() if len(parts) > 1 else None
            console.print(f"[cyan]Generating academic summary...[/cyan]")
            summary_text = study_assistant.generate_summary(doc_name)
            console.print(Markdown(summary_text))

        elif user_input.startswith("/quiz"):
            parts = user_input.split()
            count = 4
            topic = None
            if len(parts) > 1 and parts[1].isdigit():
                count = int(parts[1])
                if len(parts) > 2:
                    topic = " ".join(parts[2:])
            elif len(parts) > 1:
                topic = " ".join(parts[1:])
            console.print(f"[cyan]Generating {count}-question academic practice quiz...[/cyan]")
            quiz_text = study_assistant.generate_quiz(num_questions=count, topic=topic)
            console.print(Markdown(quiz_text))

        elif user_input.startswith("/flashcards"):
            parts = user_input.split()
            count = 5
            if len(parts) > 1 and parts[1].isdigit():
                count = int(parts[1])
            console.print(f"[cyan]Extracting active recall flashcards...[/cyan]")
            cards = study_assistant.generate_flashcards(count=count)
            print_flashcards_table(cards)

        elif cmd == "/sources":
            print_sources(rag_engine.last_retrieved_chunks)

        elif user_input.startswith("/provider"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 1:
                console.print(f"Current provider: [bold magenta]{config.provider}[/bold magenta] (model: [cyan]{config.model_name}[/cyan])")
                console.print("Available providers: [bold green]openai[/bold green], [bold green]groq[/bold green], [bold green]ollama[/bold green], [bold green]offline[/bold green]")
            else:
                new_prov = parts[1].strip().lower()
                if new_prov in ["openai", "groq", "ollama", "offline"]:
                    config.provider = new_prov
                    console.print(f"[green]Active provider switched to: [bold]{new_prov}[/bold] (model: {config.model_name})[/green]")
                else:
                    console.print("[red]Unknown provider. Choose from: openai, groq, ollama, offline[/red]")

        elif user_input.startswith("/key"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Usage: /key <your_api_key>[/red]")
                continue
            key = parts[1].strip()
            if key.startswith("gsk_"):
                config.groq_api_key = key
                config.provider = "groq"
                console.print("[green]Groq API key saved and provider set to 'groq'![/green]")
            else:
                config.openai_api_key = key
                config.provider = "openai"
                console.print("[green]OpenAI API key saved and provider set to 'openai'![/green]")

        elif user_input.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print(f"Current model: [bold cyan]{config.model_name}[/bold cyan]")
            else:
                config.model_name = parts[1].strip()
                console.print(f"[green]Model set to: [bold]{config.model_name}[/bold][/green]")

        elif user_input.startswith("/export"):
            parts = user_input.split(maxsplit=1)
            out_file = parts[1].strip() if len(parts) > 1 else "study_session_notes.md"
            res = rag_engine.export_history(out_file)
            console.print(f"[green]✓ Study session exported to: [bold]{res}[/bold][/green]")

        elif cmd == "/clear":
            rag_engine.chat_history = []
            confirm = Prompt.ask("[yellow]Clear only chat history (c) or wipe entire document index (w)?[/yellow]", choices=["c", "w"], default="c")
            if confirm == "w":
                vector_index.clear()
                console.print("[red]Document index wiped clean.[/red]")
            else:
                console.print("[green]Chat history cleared.[/green]")

        else:
            # Question query to RAG Engine
            if not vector_index.chunks:
                console.print("[bold red]No notes uploaded yet![/bold red] Please run [bold green]/upload <path/to/notes.pdf>[/bold green] first.")
                continue

            console.print(f"\n[bold magenta]ScholarBot is thinking...[/bold magenta]\n")
            try:
                # Streaming response
                full_text = []
                for token in rag_engine.ask(user_input):
                    console.print(token, end="", highlight=False)
                    full_text.append(token)
                console.print("\n")

                # Show compact source citations footer
                citations = []
                for chunk, score in rag_engine.last_retrieved_chunks[:3]:
                    citations.append(f"[bold]{chunk.doc_name}[/bold] (p.{chunk.page_num})")
                if citations:
                    console.print(f"[dim]📌 Sources: {', '.join(citations)} | Type [cyan]/sources[/cyan] for full excerpts[/dim]")

            except Exception as e:
                console.print(f"\n[bold red]Error generating answer: {e}[/bold red]")


def main():
    parser = argparse.ArgumentParser(
        description="ScholarRAG: Academic Notes PDF RAG Chatbot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # upload subcommand
    upload_parser = subparsers.add_parser("upload", help="Upload and index a PDF file or directory")
    upload_parser.add_argument("path", help="Path to PDF file or folder containing PDFs")

    # ask subcommand
    ask_parser = subparsers.add_parser("ask", help="Ask a question against indexed notes")
    ask_parser.add_argument("query", help="Question to ask")
    ask_parser.add_argument("--pdf", help="Optional PDF to ingest prior to asking", default=None)
    ask_parser.add_argument("--top-k", type=int, default=4, help="Number of context chunks")

    # summary subcommand
    summary_parser = subparsers.add_parser("summary", help="Generate academic notes summary")
    summary_parser.add_argument("--doc", help="Document name to summarize", default=None)
    summary_parser.add_argument("--pdf", help="Optional PDF to ingest first", default=None)

    # quiz subcommand
    quiz_parser = subparsers.add_parser("quiz", help="Generate practice test questions")
    quiz_parser.add_argument("--num", type=int, default=4, help="Number of questions")
    quiz_parser.add_argument("--topic", help="Specific topic or chapter", default=None)
    quiz_parser.add_argument("--pdf", help="Optional PDF to ingest first", default=None)

    # docs subcommand
    subparsers.add_parser("docs", help="List all currently indexed notes")

    args = parser.parse_args()

    # If no subcommand, start interactive REPL
    if not args.command:
        handle_interactive_repl()
        return

    if args.command == "upload":
        try:
            stats = rag_engine.ingest_path(args.path)
            console.print(f"[bold green]✓ Ingested {len(stats['processed_docs'])} document(s) ({stats['total_pages']} pages, {stats['total_chunks']} chunks)[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            sys.exit(1)

    elif args.command == "ask":
        if args.pdf:
            rag_engine.ingest_path(args.pdf)
        if not vector_index.chunks:
            console.print("[bold red]No notes indexed. Please provide --pdf or run 'python cli.py upload <pdf>' first.[/bold red]")
            sys.exit(1)
        console.print(f"[bold cyan]Q: {args.query}[/bold cyan]\n")
        for token in rag_engine.ask(args.query, top_k=args.top_k):
            console.print(token, end="", highlight=False)
        console.print("\n")

    elif args.command == "summary":
        if args.pdf:
            rag_engine.ingest_path(args.pdf)
        console.print(Markdown(study_assistant.generate_summary(args.doc)))

    elif args.command == "quiz":
        if args.pdf:
            rag_engine.ingest_path(args.pdf)
        console.print(Markdown(study_assistant.generate_quiz(args.num, args.topic)))

    elif args.command == "docs":
        print_documents_table(vector_index.documents)


if __name__ == "__main__":
    main()
