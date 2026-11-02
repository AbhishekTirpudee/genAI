import os
import sys

import groq

try:                                   
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

SYSTEM_PROMPT = """You are a simple engineering problem solver.
Solve the problem step by step and always reply in this format:

GIVEN: the values in the problem, with units
FIND: what we have to calculate
FORMULAS: the formulas we will use
STEPS:
Step 1: ...
Step 2: ...
FINAL ANSWER: the answer with its unit

Rules:
- One small calculation per step: write the formula, put in the numbers, then the result.
- Show every intermediate calculation. Do not skip any arithmetic.
- If units must be converted, do it in its own step.
- Check your arithmetic once before the final answer."""


EXAMPLE_Q = ("A pencil costs Rs 5 and a notebook costs Rs 20. "
             "Find the cost of 3 pencils and 2 notebooks.")
EXAMPLE_A = """GIVEN: pencil = Rs 5, notebook = Rs 20, quantity = 3 pencils and 2 notebooks
FIND: total cost
FORMULAS: Cost = quantity x price
STEPS:
Step 1: Cost of pencils = 3 x 5 = Rs 15
Step 2: Cost of notebooks = 2 x 20 = Rs 40
Step 3: Total cost = 15 + 40 = Rs 55
FINAL ANSWER: Total cost = Rs 55"""

DEMO_PROBLEMS = [
    "A car travels at 60 km/h for 2 hours and then at 80 km/h for 1.5 hours. "
    "Find the total distance travelled and the average speed for the whole journey.",
]



def solve(client, problem):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": EXAMPLE_Q},
        {"role": "assistant", "content": EXAMPLE_A},
        {"role": "user", "content": problem},
    ]
    response = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0.1)
    return response.choices[0].message.content


def main():
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("Error: GROQ_API_KEY is not set")
    client = groq.Groq()

    print(f"Model: {MODEL}")
    print("Type an engineering problem, 'demo' for two sample problems, or 'q' to quit.\n")
    while True:
        text = input("Problem> ").strip()
        if text.lower() in ("q", "quit", "exit"):
            break
        problems = DEMO_PROBLEMS if text.lower() == "demo" else [text]
        for problem in problems:
            if not problem:
                continue
            print(f"\n{problem}\n")
            try:
                print(solve(client, problem))
            except groq.APIError as e:
                print(f"Groq error: {e}")
            print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()