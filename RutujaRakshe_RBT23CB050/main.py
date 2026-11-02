import sys

from dotenv import load_dotenv

from agent import InventoryAgent

EXIT_COMMANDS = {"exit", "quit"}


def main() -> int:
    load_dotenv()
    try:
        agent = InventoryAgent()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Inventory agent ready. Ask a question, or type 'exit' to quit.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if question.lower() in EXIT_COMMANDS:
            return 0
        if not question:
            continue

        try:
            print(f"\nAgent: {agent.ask(question)}")
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
