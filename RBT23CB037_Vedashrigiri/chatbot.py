"""
chatbot.py
ScholarMind AI — Academic PDF-Based RAG Chatbot & Study Agent.
Allows students to upload academic notes, ask questions with exact page-level citations,
practice interactive flashcards, take exam quizzes, and view executive summaries.

Usage:
  Interactive CLI Mode:
    python chatbot.py
  Web UI Server Mode:
    python chatbot.py --web
"""

import sys
import os
import glob
import argparse

# Ensure standard output supports UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rag_engine import AcademicRAGEngine


def create_cli_engine() -> AcademicRAGEngine:
    """Initializes RAG engine and loads bundled sample academic notes."""
    engine = AcademicRAGEngine()
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_notes")
    if os.path.exists(sample_dir):
        for pdf_path in glob.glob(os.path.join(sample_dir, "*.pdf")):
            try:
                with open(pdf_path, "rb") as f:
                    data = f.read()
                filename = os.path.basename(pdf_path)
                engine.add_pdf(data, filename)
            except Exception as e:
                print(f"[Warning] Could not load sample {pdf_path}: {e}")
    return engine


def run_interactive_cli():
    """Runs a feature-rich terminal CLI for ScholarMind AI."""
    print("=" * 70)
    print(" 🎓 ScholarMind AI: Academic PDF RAG Assistant & Study Agent")
    print(" Hybrid Retrieval: BM25 Keyword Search + TF-IDF Vector Space (RRF)")
    print("=" * 70)

    engine = create_cli_engine()
    print(f"✅ Indexed {len(engine.documents)} document(s) with {len(engine.chunks)} semantic chunks.")
    for doc in engine.documents.values():
        print(f"   • {doc['filename']} ({doc['total_pages']} pages, {doc['total_chunks']} chunks)")

    print("\nCommands:")
    print(" • Type any academic question (e.g. 'What are Coffman conditions?')")
    print(" • '/upload <filepath.pdf>' : Index a new PDF study guide")
    print(" • '/flashcards'           : View generated study flashcards")
    print(" • '/quiz'                 : Take an interactive exam quiz")
    print(" • '/summary'              : View executive notes summary & formulas")
    print(" • '/docs'                 : List all indexed documents")
    print(" • '/web'                  : Launch the Web UI server")
    print(" • 'bye' or 'exit'         : Quit the assistant\n" + "-" * 70)

    while True:
        try:
            user_input = input("\nStudent ❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Happy studying!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        # Exit commands
        if cmd in ["bye", "exit", "quit", "q"]:
            print("Bot: Goodbye and best of luck with your academic studies! 🎓")
            break

        # Greetings
        if cmd in ["hi", "hello", "hey", "good morning", "good evening"]:
            print("Bot: Hello! I am ScholarMind AI, your academic notes assistant.")
            print("     Ask me anything based on your loaded PDFs or type '/quiz' to test your knowledge!")
            continue

        # Upload command
        if cmd.startswith("/upload"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("Bot: Usage: /upload <path_to_pdf>")
                continue
            filepath = parts[1].strip().strip('"').strip("'")
            if not os.path.exists(filepath):
                print(f"Bot: ❌ File not found at: {filepath}")
                continue
            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                filename = os.path.basename(filepath)
                res = engine.add_pdf(content, filename)
                print(f"Bot: ✅ Successfully indexed '{filename}' ({res['total_pages']} pages, {res['total_chunks']} chunks)!")
            except Exception as e:
                print(f"Bot: ❌ Failed to parse PDF: {e}")
            continue

        # Flashcards command
        if cmd == "/flashcards":
            print("\n🗂️  Generating Study Flashcards from Notes...")
            cards = engine.generate_flashcards(count=4)
            for idx, c in enumerate(cards, 1):
                print(f"\n[Card {idx}/{len(cards)}] ({c.get('category', 'Concept')} - Page {c.get('page', 1)})")
                print(f"Q: {c.get('front')}")
                print(f"A: {c.get('back')}")
            continue

        # Quiz command
        if cmd == "/quiz":
            print("\n📝 Starting Interactive Practice Quiz...")
            quiz = engine.generate_quiz(count=3)
            score = 0
            for idx, q in enumerate(quiz, 1):
                print(f"\nQuestion {idx}: {q['question']}")
                for opt_idx, opt in enumerate(q['options']):
                    letter = chr(65 + opt_idx)
                    print(f"  [{letter}] {opt}")
                ans = input("Your answer (A/B/C/D): ").strip().upper()
                selected_idx = ord(ans) - 65 if ans in ["A", "B", "C", "D"] else -1
                if selected_idx == q['correct_index']:
                    print("  ✅ Correct!")
                    score += 1
                else:
                    correct_letter = chr(65 + q['correct_index'])
                    print(f"  ❌ Incorrect. Correct answer was [{correct_letter}]")
                print(f"  Explanation: {q['explanation']} (Cited from Page {q['page']})")
            print(f"\nQuiz Finished! You scored {score} / {len(quiz)} points.")
            continue

        # Summary command
        if cmd == "/summary":
            summary = engine.generate_summary()
            print(f"\n📋 {summary.get('title')}")
            print(summary.get('overview'))
            if summary.get("formulas"):
                print("\nKey Formulas:")
                for f in summary["formulas"]:
                    print(f" • {f['name']}: {f['formula']} (Page {f['page']})")
            continue

        # Docs command
        if cmd == "/docs":
            print(f"\nIndexed Documents ({len(engine.documents)}):")
            for doc in engine.documents.values():
                print(f" • {doc['filename']}: {doc['total_pages']} pages, {doc['total_chunks']} chunks, {doc['total_words']} words")
            continue

        # Web command
        if cmd == "/web":
            print("\n🌐 Launching ScholarMind AI Web Application on http://localhost:8000 ...")
            import uvicorn
            import app as web_app
            uvicorn.run(web_app.app, host="127.0.0.1", port=8000)
            break

        # Standard RAG Query
        print("Bot is searching indexed notes...")
        res = engine.query(user_input)
        print("\n" + "=" * 50)
        print(res["answer"])
        print("=" * 50)

        if res.get("citations"):
            print("\n📌 Exact Source Citations:")
            for c in res["citations"]:
                print(f" • {c['doc_name']} | Page {c['page']} ({c['section']}) — Relevance: {c['relevance']}%")

        if res.get("follow_up_questions"):
            print("\n💡 Recommended Follow-up Questions:")
            for fu in res["follow_up_questions"]:
                print(f" • {fu}")


def main():
    parser = argparse.ArgumentParser(description="ScholarMind AI - Academic PDF RAG Assistant")
    parser.add_argument("--web", action="store_true", help="Launch web UI server on port 8000")
    parser.add_argument("--port", type=int, default=8000, help="Port for web server (default: 8000)")
    args = parser.parse_args()

    if args.web:
        import uvicorn
        import app as web_app
        print(f"\n🚀 Launching ScholarMind AI Web UI on http://localhost:{args.port} ...")
        uvicorn.run(web_app.app, host="127.0.0.1", port=args.port)
    else:
        run_interactive_cli()


if __name__ == "__main__":
    main()
