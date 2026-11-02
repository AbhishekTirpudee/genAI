import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# Path to backend directory and root directory
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    APP_NAME: str = "DreamCanvas AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Cloudflare Workers AI Settings
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_MODEL: str = "@cf/black-forest-labs/flux-1-schnell"
    
    # Server / CORS Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Generation Defaults
    DEFAULT_STEPS: int = 4
    MAX_PROMPT_LENGTH: int = 1000
    
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
