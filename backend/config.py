from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str
    sync_database_url: str

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "customer-support-kb"
    pinecone_namespace: str = "documents"

    # API Security
    api_secret_key: str = "dev-secret"

    # App settings
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    # Agent settings
    max_iterations: int = 10
    escalation_threshold: int = 3
    refund_limit_usd: float = 500.0


settings = Settings()
