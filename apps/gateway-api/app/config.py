from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    service_name: str = "gateway-api"
    database_url: str = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    redis_url: str = "redis://localhost:6379"

    # Azure AD
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_jwks_url: str = ""  # auto-derived if empty

    # Internal service URLs
    ai_agent_service_url: str = "http://ai-agent-service:8004"
    ingestion_service_url: str = "http://ingestion-service:8001"

    # Athena writeback (via ingestion service)
    athena_writeback_enabled: bool = True

    # Rate limiting
    rate_limit_per_minute: int = 100


settings = Settings()

if not settings.azure_jwks_url and settings.azure_tenant_id:
    settings.azure_jwks_url = (
        f"https://login.microsoftonline.com/{settings.azure_tenant_id}/discovery/v2.0/keys"
    )
