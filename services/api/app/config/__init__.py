from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    node_env: str = "development"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://app.chemvault.science"
    database_url: str = "postgresql+psycopg://chemvault:chemvault@postgres:5432/chemvault_extract"
    hyperdrive_binding: str | None = None
    hyperdrive_database_url: str | None = None
    queue_provider: str = "redis"
    redis_url: str = "redis://redis:6379/0"
    redis_queue: str = "chemvault:extract:jobs"
    webhook_delivery_queue: str = "chemvault:webhook:deliveries"
    storage_provider: str = "minio"
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "chemvault"
    s3_secret_key: str = "chemvault-secret"
    s3_bucket: str = "chemvault-documents"
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    r2_endpoint: str | None = None
    r2_public_base_url: str | None = None
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    cloudflare_zone_id: str | None = None
    cloudflare_queue_name: str | None = None
    cloudflare_queue_id: str | None = None
    internal_worker_token: str | None = None
    default_user_email: str = "local@chemvault.extract"
    default_project_name: str = "Default Project"
    worker_step_delay_seconds: float = 1.0
    max_chunk_tokens: int = 900
    jwt_secret: str | None = None
    jwt_expires_in_minutes: int = 10080
    app_encryption_key: str | None = None
    allow_user_openai_keys: bool = True

    ai_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4"
    openai_fallback_model: str = "gpt-5.5"
    ai_max_chunks_per_document: int = 20
    ai_max_chunk_chars: int = 6000
    ai_enable_fallback_model: bool = False
    ai_estimated_input_token_ratio: float = 0.25
    ai_monthly_free_file_limit: int = 10
    default_free_monthly_ai_file_limit: int = 10
    default_free_monthly_ai_cost_limit_usd: float = 5.00

    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_customer_portal_return_url: str = "http://localhost:3000/account/billing"
    stripe_checkout_success_url: str = "http://localhost:3000/account/billing/success"
    stripe_checkout_cancel_url: str = "http://localhost:3000/account/billing/cancel"
    stripe_price_student_monthly: str | None = None
    stripe_price_researcher_monthly: str | None = None
    stripe_price_lab_monthly: str | None = None
    stripe_price_student_yearly: str | None = None
    stripe_price_researcher_yearly: str | None = None
    stripe_price_lab_yearly: str | None = None

    pubchem_base_url: str = "https://pubchem.ncbi.nlm.nih.gov"
    pubchem_timeout_seconds: float = 5.0
    pubchem_cache_ttl_seconds: int = 3600
    enable_api_docs: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
