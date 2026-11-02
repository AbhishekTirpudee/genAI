from __future__ import annotations

import json
import os
import sqlite3

from groq import Groq

from db import build_database
from sql_tool import run_readonly_query

DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """You are an inventory management assistant for a warehouse business.
Answer questions about stock availability, low-stock products and product-wise quantities.
Always use the run_sql_query tool to get data. Never guess numbers.

Database schema (SQLite):
- categories(id, name)
- products(id, sku, name, category_id -> categories.id, unit_price, reorder_level)
- warehouses(id, name, location)
- stock(product_id -> products.id, warehouse_id -> warehouses.id, quantity)
  one row per product per warehouse
- product_stock (view): product_id, sku, product_name, category, unit_price, reorder_level, total_quantity
  total_quantity is the sum across all warehouses, 0 if none

Rules:
- Low stock means total_quantity < reorder_level. Use the product_stock view.
- Out of stock means total_quantity = 0.
- Only write SELECT queries. If a query returns an error, fix it and retry.
- Answer concisely and include SKUs and quantities where relevant.
"""

RUN_SQL_TOOL = {
    "type": "function",
    "function": {
        "name": "run_sql_query",
        "description": "Run a read-only SQLite SELECT query on the inventory database and return the rows.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "A single SELECT or WITH query."},
            },
            "required": ["sql"],
        },
    },
}


class InventoryAgent:
    def __init__(self, conn: sqlite3.Connection | None = None, client=None, model: str | None = None):
        if client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is not set. Add it to .env or the environment.")
            client = Groq(api_key=api_key)

        self.client = client
        self.conn = conn or build_database()
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def ask(self, question: str) -> str:
        self.messages.append({"role": "user", "content": question})

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=[RUN_SQL_TOOL],
                tool_choice="auto",
                temperature=0,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                answer = message.content or ""
                self.messages.append({"role": "assistant", "content": answer})
                return answer

            self.messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in message.tool_calls
                ],
            })
            for call in message.tool_calls:
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": self._run_tool(call.function.name, call.function.arguments),
                })

        return "Sorry, I could not answer that within the step limit. Please try a simpler question."

    def _run_tool(self, name: str, raw_arguments: str) -> str:
        if name != "run_sql_query":
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            arguments = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            return json.dumps({"error": "Tool arguments were not valid JSON."})
        return json.dumps(run_readonly_query(self.conn, arguments.get("sql", "")), default=str)
