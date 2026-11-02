"""
ReAct-Based AI Assistant
Tools: DuckDuckGo Search and Python Calculator
LLM: Groq API (openai/gpt-oss-120b)

Set GROQ_API_KEY before running:
Windows PowerShell:
    $env:GROQ_API_KEY="your_api_key"
Run:
    python react_assistant.py
"""

import os
import json
import ast
import operator

from groq import Groq
from ddgs import DDGS


MODEL = "openai/gpt-oss-120b"
MAX_ITERATIONS = 5


# -------------------------------
# 1. Initialize the LLM client
# -------------------------------

def create_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Set it in your terminal before running."
        )
    return Groq(api_key=api_key)


# -------------------------------
# 2. Calculator tool
# -------------------------------

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculator(expression):
    """Safely evaluate basic arithmetic expressions using Python AST."""

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPERATORS:
                raise ValueError("Operator not allowed")
            return _ALLOWED_OPERATORS[op_type](
                evaluate(node.left), evaluate(node.right)
            )

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPERATORS:
                raise ValueError("Operator not allowed")
            return _ALLOWED_OPERATORS[op_type](evaluate(node.operand))

        raise ValueError("Invalid mathematical expression")

    try:
        tree = ast.parse(expression, mode="eval")
        result = evaluate(tree.body)
        return str(result)
    except Exception as exc:
        return f"Calculation error: {exc}"


# -------------------------------
# 3. Search tool
# -------------------------------

def search_tool(query):
    """Search the web and return a compact set of results."""
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No search results found."

        formatted_results = []
        for item in results:
            formatted_results.append(
                f"Title: {item.get('title', '')}\n"
                f"Description: {item.get('body', '')}\n"
                f"URL: {item.get('href', '')}"
            )
        return "\n\n".join(formatted_results)

    except Exception as exc:
        return f"Search error: {exc}"


# -------------------------------
# 4. ReAct agent
# -------------------------------

SYSTEM_PROMPT = """
You are a ReAct-based AI assistant.

Available tools:
1. calculator: performs arithmetic. Input must be an arithmetic expression.
2. search: searches the web. Input must be a search query.

Follow this cycle:
Thought -> Action -> Observation -> (repeat if needed) -> Final Answer.

Return ONLY a valid JSON object with these keys:
{
  "thought": "Brief decision summary, not private chain-of-thought",
  "action": "search, calculator, or final",
  "action_input": "query or arithmetic expression",
  "final_answer": "answer when action is final"
}

Rules:
- Use calculator for arithmetic calculations.
- Use search for factual or current information.
- Use tool observations as evidence.
- You may call more than one tool if needed.
- Do not invent tool observations or claim a tool ran when it did not.
- When enough information is available, choose action="final".
- Keep the thought field brief.
"""


def react_agent(question, client):
    """Run the ReAct loop for one user question."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n========== STEP {step} ==========")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
        except Exception as exc:
            print(f"LLM/API error: {exc}")
            return "The assistant could not get a valid response from the LLM."

        thought = result.get("thought", "")
        action = str(result.get("action", "")).lower().strip()
        action_input = str(result.get("action_input", ""))

        print("THOUGHT:", thought)

        if action == "final":
            answer = result.get("final_answer", "")
            print("\nFINAL ANSWER:\n", answer)
            return answer

        if action == "calculator":
            print("ACTION: Calculator")
            print("INPUT:", action_input)
            observation = calculator(action_input)

        elif action == "search":
            print("ACTION: Search")
            print("INPUT:", action_input)
            observation = search_tool(action_input)

        else:
            observation = (
                "Invalid action. Choose exactly: search, calculator, or final."
            )

        print("\nOBSERVATION:\n", observation)

        # Append the model's action and the tool observation to the conversation.
        messages.append({
            "role": "assistant",
            "content": json.dumps(result),
        })
        messages.append({
            "role": "user",
            "content": (
                "TOOL OBSERVATION:\n"
                f"{observation}\n\n"
                "Continue the ReAct process. Use another tool if needed, "
                "otherwise return the final answer in the required JSON format."
            ),
        })

    print("\nMaximum iterations reached.")
    return "Unable to complete within the iteration limit. Please try again."


# -------------------------------
# 5. Main application
# -------------------------------

def main():
    print("=" * 45)
    print("          ReAct AI ASSISTANT")
    print("=" * 45)
    print("Tools available: Search and Calculator")
    print("Type 'exit' to quit.")

    try:
        client = create_client()
    except EnvironmentError as exc:
        print(f"\nConfiguration error: {exc}")
        return

    while True:
        question = input("\nEnter your question: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Thank you for using ReAct Assistant!")
            break

        if not question:
            print("Please enter a question.")
            continue

        react_agent(question, client)


if __name__ == "__main__":
    main()
