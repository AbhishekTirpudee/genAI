from __future__ import annotations

import json
import logging
import os
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from backend.config import settings
from backend.database import ResearchDatabase
from backend.export import markdown_to_pdf
from backend.orchestrator import ResearchOrchestrator
from backend.schemas import AgentEvent, ResearchRequest

logger = logging.getLogger(__name__)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


class ResearchService:
    """Durable, bounded background execution for independent research jobs."""

    def __init__(
        self,
        database: ResearchDatabase | None = None,
        output_dir: Path | None = None,
        max_workers: int | None = None,
    ) -> None:
        self.database = database or ResearchDatabase()
        self._output_dir = output_dir or settings.output_dir
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers or settings.max_workers,
            thread_name_prefix="marketmind-research",
        )
        self._futures: dict[str, Future[Any]] = {}
        self._lock = threading.RLock()
        for job_id in self.database.recover_interrupted_jobs():
            self._submit(job_id)

    def submit(self, request: ResearchRequest) -> dict[str, Any]:
        if not request.demo_mode and settings.missing_live_credentials:
            raise RuntimeError(
                "Live research is unavailable until these backend credentials are configured: "
                + ", ".join(settings.missing_live_credentials)
            )
        job = self.database.create_job(request)
        self._submit(job["job_id"])
        return job

    def _submit(self, job_id: str) -> None:
        with self._lock:
            existing = self._futures.get(job_id)
            if existing and not existing.done():
                return
            self._futures[job_id] = self._executor.submit(self._run, job_id)

    def _run(self, job_id: str) -> None:
        job = self.database.get_job(job_id)
        if not job:
            logger.error("Queued research job %s disappeared from SQLite.", job_id)
            return
        request = ResearchRequest.model_validate(job["request"])
        self.database.update_status(job_id, "running")

        def persist_event(event: AgentEvent) -> None:
            self.database.append_event(job_id, event)

        try:
            result = ResearchOrchestrator(on_event=persist_event).run(request)
            report = result["report"]
            state_json = {
                key: value.model_dump(mode="json") if hasattr(value, "model_dump") else value
                for key, value in result.items()
            }
            serialized_report = report.model_dump(mode="json")
            output_dir = self._output_dir / job_id
            _atomic_write(output_dir / "report.md", report.markdown)
            _atomic_write(
                output_dir / "report.json",
                json.dumps(serialized_report, indent=2, ensure_ascii=False),
            )
            _atomic_write(
                output_dir / "state.json",
                json.dumps(state_json, indent=2, default=lambda value: value.model_dump(mode="json")),
            )
            _atomic_write_bytes(output_dir / "report.pdf", markdown_to_pdf(report.markdown))
            self.database.update_status(
                job_id,
                "completed",
                report=serialized_report,
                state=state_json,
                search_calls_used=result.get("search_calls_used", 0),
            )
            persist_event(
                AgentEvent(
                    agent="orchestrator",
                    status="completed",
                    message=f"Research finished with {len(result.get('sources', []))} real sources.",
                )
            )
        except Exception as exc:
            logger.exception("Research job %s failed.", job_id)
            self.database.update_status(job_id, "failed", error_message=str(exc))
            try:
                persist_event(
                    AgentEvent(agent="orchestrator", status="failed", message=f"Research failed: {exc}")
                )
            except Exception:
                logger.exception("Failed to persist failure event for research job %s.", job_id)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.database.get_job(job_id)

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.database.list_jobs(limit)

    def get_events(self, job_id: str, after_event_id: int = 0) -> list[dict[str, Any]]:
        return self.database.get_events(job_id, after_event_id)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=False)
