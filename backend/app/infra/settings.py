# app/infra/settings.py
import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "commandlayer")
    db_password: str = os.getenv("DB_PASSWORD", "commandlayer")
    db_name: str = os.getenv("DB_NAME", "commandlayer")

    # OpenAI / LLM
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))

    # Intent resolution
    intent_resolution_mode: str = os.getenv("INTENT_RESOLUTION_MODE", "pre_ai")

    # RAG
    rag_mode: str = os.getenv("RAG_MODE", "off")
    rag_max_chars: int = int(os.getenv("RAG_MAX_CHARS", "4000"))
    knowledge_base_path: str = os.getenv(
        "KNOWLEDGE_BASE_PATH",
        "/app/knowledge_base",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
