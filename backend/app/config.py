from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AI ------------------------------------------------------------------
    # ai_provider: gemini | groq | openai_compat | ollama | auto
    # "auto" picks Gemini when a Google AI Studio key is present, otherwise an
    # OpenAI-compatible provider (e.g. Groq) when a key/base URL is configured.
    ai_provider: str = "auto"
    ai_model: str = ""
    ai_base_url: str = ""
    ai_api_key: str = ""

    gemini_api_key: str = ""
    gemini_model: str = ""

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""

    # Research discovery ---------------------------------------------------
    openalex_api_key: str = ""
    contact_email: str = ""
    semantic_scholar_api_key: str = ""
    unpaywall_email: str = ""
    arxiv_email: str = ""
    enable_semantic_scholar: bool = True
    enable_arxiv: bool = True

    # Services -------------------------------------------------------------
    grobid_url: str = "http://localhost:8070"
    # Comma-separated browser origins allowed to call the API. Set this to the
    # deployed frontend origin in production (e.g. https://citeverify.vercel.app).
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )
    database_url: str = "sqlite:///./storage/citeverify.db"
    max_upload_mb: int = 20

    # Pipeline limits (keeps a demo run bounded) ---------------------------
    max_claims: int = 16
    max_verify_claims: int = 12
    max_references: int = 40
    evidence_top_k: int = 3


settings = Settings()
