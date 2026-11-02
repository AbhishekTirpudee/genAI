import re
import sqlite3

MAX_ROWS = 100

_STATEMENT_START = re.compile(r"^(select|with)\b", re.IGNORECASE)
_WRITE_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex)\b",
    re.IGNORECASE,
)


def validate_query(sql: str) -> str:
    statement = sql.strip().rstrip(";").strip()
    if not statement:
        raise ValueError("Query is empty.")
    if ";" in statement:
        raise ValueError("Only a single SQL statement is allowed.")
    if not _STATEMENT_START.match(statement):
        raise ValueError("Only SELECT queries are allowed.")
    if _WRITE_KEYWORDS.search(statement):
        raise ValueError("Query contains a disallowed keyword.")
    return statement


def run_readonly_query(conn: sqlite3.Connection, sql: str) -> dict:
    try:
        statement = validate_query(sql)
        cursor = conn.execute(statement)
        columns = [column[0] for column in cursor.description or []]
        rows = cursor.fetchmany(MAX_ROWS + 1)
    except (ValueError, sqlite3.Error) as exc:
        return {"error": str(exc)}

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    return {
        "columns": columns,
        "rows": [list(row) for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }
