import sys
import io
from pathlib import Path
from typing import List, Tuple, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.box import ROUNDED

from .config import config
from .vector_store import vector_index
from .text_splitter import TextChunk

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr.encoding.lower() != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

console = Console(force_terminal=True, highlight=False)


def print_banner():
    banner_text = """
  ____       _           _            ____      _     ____  
 / ___|  ___| |__   ___ | | __ _ _ __|  _ \    / \   / ___| 
 \___ \ / __| '_ \ / _ \| |/ _` | '__| |_) |  / _ \ | |  _  
  ___) | (__| | | | (_) | | (_| | |  |  _ <  / ___ \| |_| | 
 |____/ \___|_| |_|\___/|_|\__,_|_|  |_| \_\/_/   \_\\____| 
              [ Academic Notes PDF RAG Chatbot ]
    """
    console.print(f"[bold cyan]{banner_text}[/bold cyan]")
    
    doc_count = len(vector_index.documents)
    chunk_count = len(vector_index.chunks)
    prov = config.provider.upper()
    model = config.model_name
    
    status_table = Table(box=ROUNDED, show_header=False, expand=True)
    status_table.add_column("Key", style="bold yellow", width=22)
    status_table.add_column("Value", style="bold white")
    
    status_table.add_row("[+] Indexed Documents:", f"{doc_count} PDF(s) loaded ({chunk_count} total text chunks)")
    status_table.add_row("[*] Active LLM Engine:", f"[magenta]{prov}[/magenta] ([cyan]{model}[/cyan])")
    status_table.add_row("[>] Retrieval Strategy:", "Hybrid BM25 Lexical + Cosine Semantic Ranking")
    status_table.add_row("[?] Quick Help:", "Type [bold green]/help[/bold green] for commands or ask any question directly!")
    
    console.print(Panel(status_table, title="[bold green]System Status[/bold green]", border_style="cyan"))


def print_help():
    table = Table(title="ScholarRAG Commands", box=ROUNDED, header_style="bold magenta")
    table.add_column("Command", style="bold green", width=24)
    table.add_column("Description", style="white")
    table.add_column("Example", style="italic cyan")

    table.add_row("/upload <path>", "Ingest single PDF file or folder of notes", "/upload notes/biology.pdf")
    table.add_row("/docs", "List all uploaded notes and chunk stats", "/docs")
    table.add_row("/remove <filename>", "Remove a document from the index", "/remove biology.pdf")
    table.add_row("/summary [doc]", "Generate academic notes summary", "/summary or /summary biology.pdf")
    table.add_row("/quiz [n] [topic]", "Generate practice test questions", "/quiz 5 machine learning")
    table.add_row("/flashcards [n]", "Generate active recall flashcards", "/flashcards 5")
    table.add_row("/sources", "Inspect context chunks from last answer", "/sources")
    table.add_row("/provider [name]", "Switch provider (openai, groq, ollama, offline)", "/provider groq")
    table.add_row("/key <api_key>", "Set your OpenAI or Groq API key", "/key gsk_...")
    table.add_row("/model <name>", "Set active model name", "/model gpt-4o-mini")
    table.add_row("/export [file]", "Export Q&A history to Markdown file", "/export session.md")
    table.add_row("/clear", "Clear chat history or wipe index", "/clear")
    table.add_row("/exit or exit", "Quit ScholarRAG", "/exit")

    console.print(table)


def print_documents_table(docs: Dict[str, Dict[str, Any]]):
    if not docs:
        console.print("[yellow]No documents currently indexed. Use [bold green]/upload <path.pdf>[/bold green] to get started![/yellow]")
        return

    table = Table(title="Uploaded Academic Notes", box=ROUNDED, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Document Name", style="bold green")
    table.add_column("Pages", justify="center", style="yellow")
    table.add_column("Words", justify="right", style="magenta")
    table.add_column("Chunks", justify="center", style="cyan")
    table.add_column("Path", style="dim")

    for i, (name, info) in enumerate(docs.items(), 1):
        table.add_row(
            str(i),
            name,
            str(info.get("total_pages", "-")),
            f"{info.get('total_words', 0):,}",
            str(info.get("chunk_count", "-")),
            str(info.get("file_path", "-")),
        )

    console.print(table)


def print_sources(results: List[Tuple[TextChunk, float]]):
    if not results:
        console.print("[dim]No sources retrieved for last query.[/dim]")
        return

    console.print("\n[bold cyan]-- Retrieved Academic Context Sources --[/bold cyan]")
    for i, (chunk, score) in enumerate(results, 1):
        header = f"[bold green]Source {i}:[/bold green] [yellow]{chunk.doc_name}[/yellow] - [bold white]Page {chunk.page_num}[/bold white] (Similarity: [magenta]{score:.2f}[/magenta])"
        snippet = chunk.text.strip()
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        console.print(Panel(snippet, title=header, border_style="blue", box=ROUNDED))


def print_flashcards_table(cards: List[Dict[str, str]]):
    if not cards:
        console.print("[yellow]Could not extract flashcards. Try uploading notes with clear definitions or headings.[/yellow]")
        return

    for i, card in enumerate(cards, 1):
        panel_content = f"[bold yellow]Definition / Formula:[/bold yellow]\n{card['definition']}\n\n[dim]Source: {card['source']}[/dim]"
        console.print(
            Panel(
                panel_content,
                title=f"[bold green]Flashcard {i}: [white]{card['term']}[/white][/bold green]",
                border_style="yellow",
                box=ROUNDED,
            )
        )
