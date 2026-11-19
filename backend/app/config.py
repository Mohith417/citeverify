from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = ""
    ai_provider: str = "gemini"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""
    openalex_api_key: str = ""
    contact_email: str = ""
    grobid_url: str = "http://localhost:8070"
    database_url: str = "sqlite:///./storage/citeverify.db"
    max_upload_mb: int = 20


settings = Settings()
