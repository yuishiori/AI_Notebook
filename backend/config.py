from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 8192
    gemini_timeout_seconds: int = 60
    gemini_stream: bool = True
    gemini_safety_threshold: str = "BLOCK_NONE"

    # Database
    database_url: Optional[str] = None

    # Embedding
    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-m3"
    gemini_embedding_model: str = "text-embedding-004"

    # 後端
    app_host: str = "127.0.0.1"
    app_port: int = 8765
    log_level: str = "INFO"

    # 資料目錄
    data_dir: str = "./data"
    uploads_dir: str = "./uploads"
    reports_dir: str = "./reports"
    briefings_dir: str = "./briefings"

    # 排程
    briefing_time: str = "08:00"
    briefing_timezone: str = "Asia/Taipei"
    due_warning_days: int = 3
    stale_project_days: int = 3

    # Workspace
    default_workspace: str = "work"
    rag_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 100

settings = Settings()

# Ensure directories exist (only for local, Cloud Storage FUSE will handle cloud)
if not settings.database_url:
    for d in [settings.data_dir, settings.uploads_dir, settings.reports_dir, settings.briefings_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
