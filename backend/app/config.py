"""Environment-driven application settings with development defaults."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    max_upload_mb: int = 25
    work_dir: Path = Path("./.workspace")
    workspace_ttl_min: int = 120
    confidence_threshold: float = 0.6

    soffice_path: str = ""
    pdf_timeout_s: int = 60

    history_db: Path = Path("./.workspace/history.db")
    history_enabled: bool = True
    # "sqlite" keeps history on local disk; "remote" uses the Cloudflare D1 history Worker.
    history_backend: Literal["sqlite", "remote"] = "sqlite"
    history_api_url: str = ""
    history_api_token: str = ""
    # On a shared server every visitor sends an anonymous X-Client-Id; history is then
    # limited to that visitor. Off locally, where there is one user.
    history_scope_by_owner: bool = False
    # 0 = only sweep expired workspaces at startup (local default). >0 = also every N minutes.
    workspace_sweep_interval_min: int = 0

    log_level: str = "INFO"
    log_format: str = "json"

    version: str = "0.1.0"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
