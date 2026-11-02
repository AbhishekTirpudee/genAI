# Inventory Management Agent

A command-line assistant that answers inventory questions in plain English. An LLM (Groq free tier) writes read-only SQL against an inventory database, runs it, and explains the result.

Example questions:

- Which products are low on stock?
- How many units of USB-C Charger do we have?
- Which products are out of stock?
- Show the quantity per warehouse for Basmati Rice.

## Features

- Stock availability per product, summed across all warehouses
- Low-stock detection (total quantity below each product's reorder level)
- Out-of-stock detection
- Product-wise and warehouse-wise quantities
- Read-only SQL execution with several safety guards
- Sample data defined in code, so no external files or setup are needed

## How it works

1. You type a question in the terminal.
2. The agent sends the question and the database schema to a Groq chat model, with one tool: `run_sql_query`.
3. The model writes a SELECT query and the agent runs it against an in-memory SQLite database.
4. The rows go back to the model, which writes the final answer. If a query fails, the model can correct it and try again (up to 5 tool rounds per question).

## Project structure

| File | Purpose |
| --- | --- |
| `db.py` | SQL schema, sample data, and the read-only database connection |
| `sql_tool.py` | Query validation and execution (SELECT/WITH only, 100-row cap) |
| `agent.py` | Groq client, system prompt, and tool-calling loop |
| `main.py` | Interactive command-line interface |
| `test_inventory.py` | Unit tests for data and SQL guards |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for environment variables |

## Database schema

- `categories(id, name)`
- `products(id, sku, name, category_id, unit_price, reorder_level)`
- `warehouses(id, name, location)`
- `stock(product_id, warehouse_id, quantity)`: one row per product per warehouse
- `product_stock` (view): `product_id, sku, product_name, category, unit_price, reorder_level, total_quantity`

Low stock means `total_quantity < reorder_level`. Out of stock means `total_quantity = 0`.

## Requirements

- Python 3.9 or newer
- A free Groq API key from the [Groq console](https://console.groq.com)

## Setup

```bash
cd inventory-agent
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and set your key:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

`GROQ_MODEL` is optional. It must be a Groq chat model that supports tool calling. If you see a `model_not_found` error, the model is not available to your key. Change `GROQ_MODEL` to another model from your Groq account.

## Run

```bash
.venv/bin/python main.py
```

Type a question at the `You:` prompt. Type `exit` or `quit` to stop.

## Tests

```bash
.venv/bin/python -m unittest -v test_inventory
```

The tests do not call the Groq API, so they run without a key.

## Safety notes

- Only a single SELECT or WITH statement is accepted. Write keywords such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `PRAGMA` are rejected.
- The database connection is set to `query_only`, so writes fail even if validation is bypassed.
- Results are capped at 100 rows.
- The `.env` file is git-ignored, so your API key is not committed.

## Changing the data

Edit the `CATEGORIES`, `WAREHOUSES`, `PRODUCTS`, and `STOCK` lists in [db.py](db.py). The database is rebuilt from these lists each time the program starts.
