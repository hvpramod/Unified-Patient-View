from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    service_name: str = "ai-agent-service"
    database_url: str = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    redis_url: str = "redis://localhost:6379"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_patient_updated: str = "patient.data.updated"
    kafka_topic_labs_new: str = "patient.labs.new"
    kafka_topic_medications_changed: str = "patient.medications.changed"

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_model_summarization: str = "gpt-4o"
    anthropic_model_reasoning: str = "claude-sonnet-4-6"
    embedding_model: str = "text-embedding-3-small"

    # RAG
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.75

    # Cache TTL
    summary_cache_ttl_seconds: int = 3600  # 1 hour


settings = Settings()
