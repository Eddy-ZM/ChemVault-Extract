from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://chemvault:chemvault@postgres:5432/chemvault_extract"
    redis_url: str = "redis://redis:6379/0"
    redis_queue: str = "chemvault:extract:jobs"
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "chemvault"
    s3_secret_key: str = "chemvault-secret"
    s3_bucket: str = "chemvault-documents"
    default_user_email: str = "local@chemvault.extract"
    default_project_name: str = "Default Project"
    worker_step_delay_seconds: float = 1.0
    max_chunk_tokens: int = 900

    ai_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4"
    openai_fallback_model: str = "gpt-5.4"
    ai_max_chunks_per_document: int = 20
    ai_max_chunk_chars: int = 6000
    ai_enable_fallback_model: bool = False
    ai_estimated_input_token_ratio: float = 0.25
    ai_monthly_free_file_limit: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
