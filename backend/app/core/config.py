"""
ForgeX Deep Agent Platform — Application Configuration

Pydantic Settings model loading from environment variables / .env file.
All environment variables from spec §21 are represented here.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Azure Claude binding ---
    azure_claude_api_key: str = "REPLACE_ME"
    azure_claude_base_url: str = "REPLACE_ME"
    azure_claude_model: str = "claude-sonnet-4-5-forgex-rnd"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./forgex_agent.db"
    checkpoint_db_path: str = "./forgex_checkpoints.db"

    # --- Data root ---
    data_root: str = "./data"

    # --- CORS ---
    cors_allowed_origins: str = "http://localhost:5173"

    # --- Web search ---
    web_search_provider: str = "tavily"
    tavily_api_key: Optional[str] = None
    bing_search_api_key: Optional[str] = None

    # --- Runtime tool security ---
    http_tool_allowed_host_suffixes: str = ""
    http_tool_block_private_networks: bool = True

    # --- LangSmith ---
    langsmith_tracing: bool = False
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "forgex-deepagent"

    # --- Dev controls ---
    app_env: str = "development"
    debug: bool = False

    # --- File upload ---
    max_upload_size_mb: int = 50
    allowed_mime_types: str = (
        "application/pdf,text/plain,text/markdown,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "image/png,image/jpeg"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        if not self.http_tool_allowed_host_suffixes:
            return []
        return [s.strip() for s in self.http_tool_allowed_host_suffixes.split(",") if s.strip()]

    @property
    def allowed_mime_list(self) -> list[str]:
        return [m.strip() for m in self.allowed_mime_types.split(",") if m.strip()]


# Singleton settings instance
settings = Settings()
