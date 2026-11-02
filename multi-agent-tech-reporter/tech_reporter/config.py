"""Configuration management for tech_reporter."""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


def load_dotenv(dotenv_path: Optional[Path] = None) -> None:
    """Lightweight .env file loader with zero external dependencies."""
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
        if not dotenv_path.exists():
            dotenv_path = Path(__file__).resolve().parent.parent / ".env"

    if not dotenv_path.exists():
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


@dataclass
class AppConfig:
    """Application configuration."""
    llm_provider: str = "auto"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = "https://api.openai.com/v1"
    search_backend: str = "duckduckgo"
    output_dir: Path = Path("outputs")
    log_level: str = "INFO"
    mock_mode: bool = False

    @classmethod
    def from_env(cls) -> AppConfig:
        load_dotenv()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()

        if provider == "auto":
            if gemini_key:
                provider = "gemini"
            elif openai_key:
                provider = "openai"
            else:
                provider = "mock"

        out_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
        out_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            llm_provider=provider,
            gemini_api_key=gemini_key,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            openai_api_key=openai_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            search_backend=os.getenv("SEARCH_BACKEND", "duckduckgo"),
            output_dir=out_dir,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            mock_mode=(provider == "mock")
        )
