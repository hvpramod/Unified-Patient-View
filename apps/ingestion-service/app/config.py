from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    service_name: str = "ingestion-service"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://upv:upv@localhost:5432/upv"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_patient_updated: str = "patient.data.updated"
    kafka_topic_labs_new: str = "patient.labs.new"
    kafka_topic_medications_changed: str = "patient.medications.changed"
    kafka_topic_encounter_created: str = "patient.encounter.created"

    # Athena
    athena_base_url: str = "https://api.platform.athenahealth.com/v1"
    athena_client_id: str = ""
    athena_client_secret: str = ""
    athena_practice_id: str = ""
    athena_poll_interval_seconds: int = 60

    # HealthGorilla (mock)
    healthgorilla_base_url: str = "http://mock-healthgorilla:8080"
    healthgorilla_api_key: str = "mock-key"

    # Pathway (mock)
    pathway_base_url: str = "http://mock-pathway:8080"
    pathway_api_key: str = "mock-key"


settings = Settings()
