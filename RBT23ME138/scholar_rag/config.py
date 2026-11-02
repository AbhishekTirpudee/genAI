import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / ".scholar_cache"
INDEX_FILE = STORAGE_DIR / "documents_index.json"
CONFIG_FILE = STORAGE_DIR / "config.json"


class Config:
    def __init__(self):
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.config_data = self._load_saved_config()

    def _load_saved_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2)

    # API Keys & Provider
    @property
    def openai_api_key(self) -> Optional[str]:
        return self.config_data.get("openai_api_key") or os.getenv("OPENAI_API_KEY")

    @openai_api_key.setter
    def openai_api_key(self, val: str):
        self.config_data["openai_api_key"] = val
        self.save()

    @property
    def groq_api_key(self) -> Optional[str]:
        return self.config_data.get("groq_api_key") or os.getenv("GROQ_API_KEY")

    @groq_api_key.setter
    def groq_api_key(self, val: str):
        self.config_data["groq_api_key"] = val
        self.save()

    @property
    def provider(self) -> str:
        """
        Providers:
        - 'openai' (requires OPENAI_API_KEY)
        - 'groq' (requires GROQ_API_KEY)
        - 'ollama' (requires local ollama server)
        - 'offline' (smart local academic extractive synthesis, no key needed)
        """
        saved = self.config_data.get("provider")
        if saved:
            return saved
        if self.openai_api_key:
            return "openai"
        if self.groq_api_key:
            return "groq"
        return "offline"

    @provider.setter
    def provider(self, val: str):
        self.config_data["provider"] = val.lower()
        self.save()

    @property
    def model_name(self) -> str:
        saved = self.config_data.get("model_name")
        if saved:
            return saved
        prov = self.provider
        if prov == "openai":
            return "gpt-4o-mini"
        elif prov == "groq":
            return "llama-3.3-70b-versatile"
        elif prov == "ollama":
            return "llama3"
        return "offline-extractive"

    @model_name.setter
    def model_name(self, val: str):
        self.config_data["model_name"] = val
        self.save()

    @property
    def ollama_base_url(self) -> str:
        return self.config_data.get("ollama_base_url", "http://localhost:11434")

    @ollama_base_url.setter
    def ollama_base_url(self, val: str):
        self.config_data["ollama_base_url"] = val
        self.save()

    @property
    def chunk_size(self) -> int:
        return int(self.config_data.get("chunk_size", 750))

    @property
    def chunk_overlap(self) -> int:
        return int(self.config_data.get("chunk_overlap", 150))

    @property
    def top_k(self) -> int:
        return int(self.config_data.get("top_k", 4))


config = Config()
