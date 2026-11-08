from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Agentic Research Dashboard"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"

    llm_provider: str = "offline"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    openai_api_key: str = ""
    openai_base_url: str = ""
    google_api_key: str = ""

    search_provider: str = "offline"
    tavily_api_key: str = ""
    search_results_per_query: int = 4
    search_timeout_seconds: float = 20.0

    default_user_email: str = "local@example.com"
    max_depth: int = 4
    queries_per_round: int = 3

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
