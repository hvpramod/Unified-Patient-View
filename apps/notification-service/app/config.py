from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    service_name: str = "notification-service"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_labs_new: str = "patient.labs.new"
    teams_webhook_url: str = ""
    upv_base_url: str = "http://localhost:3000"
    ai_agent_service_url: str = "http://ai-agent-service:8004"


settings = Settings()
