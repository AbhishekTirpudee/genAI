from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "research.sqlite3")))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs")))
    max_workers: int = max(1, int(os.getenv("MAX_RESEARCH_WORKERS", "3")))
    max_search_calls: int = max(1, int(os.getenv("MAX_SEARCH_CALLS", "12")))
    max_sources: int = max(3, int(os.getenv("MAX_UNIQUE_SOURCES", "40")))
    max_research_iterations: int = max(0, min(3, int(os.getenv("MAX_RESEARCH_ITERATIONS", "2"))))
    request_timeout_seconds: float = max(3.0, float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")))

    @property
    def missing_live_credentials(self) -> list[str]:
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        return missing


settings = Settings()
