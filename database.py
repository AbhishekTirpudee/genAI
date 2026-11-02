from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.config import settings
from backend.schemas import AgentEvent, ResearchRequest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class ResearchDatabase:
    """Thread-safe SQLite persistence; each operation has its own WAL-enabled connection."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.database_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS research_jobs (
                    job_id TEXT PRIMARY KEY,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_agent TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT NOT NULL DEFAULT '',
                    search_calls_used INTEGER NOT NULL DEFAULT 0,
                    report_json TEXT,
                    state_json TEXT
                );
                CREATE TABLE IF NOT EXISTS research_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL REFERENCES research_jobs(job_id) ON DELETE CASCADE,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL,
                    iteration INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_research_events_job
                    ON research_events(job_id, event_id);
                CREATE INDEX IF NOT EXISTS idx_research_jobs_created
                    ON research_jobs(created_at DESC);
                """
            )

    def create_job(self, request: ResearchRequest) -> dict[str, Any]:
        job_id = str(uuid4())
        now = _now()
        request_json = request.model_dump_json()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO research_jobs (job_id, request_json, status, created_at, updated_at)
                VALUES (?, ?, 'queued', ?, ?)
                """,
                (job_id, request_json, now, now),
            )
            self._insert_event(
                connection,
                job_id,
                AgentEvent(agent="orchestrator", status="info", message="Research job queued."),
            )
        return self.get_job(job_id)

    def _insert_event(
        self,
        connection: sqlite3.Connection,
        job_id: str,
        event: AgentEvent,
    ) -> None:
        connection.execute(
            """
            INSERT INTO research_events
                (job_id, agent, status, message, timestamp, duration_seconds, iteration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                event.agent,
                event.status,
                event.message,
                event.timestamp.isoformat(),
                event.duration_seconds,
                event.iteration,
            ),
        )

    def append_event(self, job_id: str, event: AgentEvent) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._insert_event(connection, job_id, event)
            current_agent = event.agent if event.agent != "orchestrator" else None
            if current_agent:
                connection.execute(
                    "UPDATE research_jobs SET current_agent = ?, updated_at = ? WHERE job_id = ?",
                    (current_agent, _now(), job_id),
                )
            else:
                connection.execute(
                    "UPDATE research_jobs SET updated_at = ? WHERE job_id = ?",
                    (_now(), job_id),
                )

    def get_events(self, job_id: str, after_event_id: int = 0) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, agent, status, message, timestamp, duration_seconds, iteration
                FROM research_events
                WHERE job_id = ? AND event_id > ?
                ORDER BY event_id
                """,
                (job_id, after_event_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_snapshot(self, job_id: str, state: dict[str, Any]) -> None:
        payload = json.dumps(state, default=_json_value, ensure_ascii=True)
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE research_jobs SET state_json = ?, updated_at = ? WHERE job_id = ?",
                (payload, _now(), job_id),
            )

    def update_status(
        self,
        job_id: str,
        status: str,
        error_message: str = "",
        report: dict[str, Any] | None = None,
        state: dict[str, Any] | None = None,
        search_calls_used: int = 0,
    ) -> None:
        now = _now()
        report_json = json.dumps(report, default=_json_value, ensure_ascii=True) if report is not None else None
        state_json = json.dumps(state, default=_json_value, ensure_ascii=True) if state is not None else None
        completed_at = now if status in {"completed", "failed"} else None
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE research_jobs SET
                    status = ?, updated_at = ?, completed_at = COALESCE(?, completed_at),
                    error_message = ?, report_json = COALESCE(?, report_json),
                    state_json = COALESCE(?, state_json), search_calls_used = ?
                WHERE job_id = ?
                """,
                (
                    status,
                    now,
                    completed_at,
                    error_message,
                    report_json,
                    state_json,
                    search_calls_used,
                    job_id,
                ),
            )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM research_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["request"] = json.loads(result.pop("request_json"))
        result["report"] = json.loads(result.pop("report_json")) if result.get("report_json") else None
        result["state"] = json.loads(result.pop("state_json")) if result.get("state_json") else None
        return result

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT job_id FROM research_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [job for row in rows if (job := self.get_job(row["job_id"])) is not None]

    def recover_interrupted_jobs(self) -> list[str]:
        now = _now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            interrupted = connection.execute(
                "SELECT job_id FROM research_jobs WHERE status IN ('queued', 'running')"
            ).fetchall()
            job_ids = [row["job_id"] for row in interrupted]
            connection.executemany(
                "UPDATE research_jobs SET status = 'queued', updated_at = ? WHERE job_id = ?",
                [(now, job_id) for job_id in job_ids],
            )
            for job_id in job_ids:
                self._insert_event(
                    connection,
                    job_id,
                    AgentEvent(
                        agent="orchestrator",
                        status="info",
                        message="Recovering interrupted job from its persisted request.",
                    ),
                )
        return job_ids
