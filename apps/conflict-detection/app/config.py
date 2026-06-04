from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    service_name: str = "conflict-detection"
    database_url: str = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_patient_updated: str = "patient.data.updated"


settings = Settings()
