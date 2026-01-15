# app/infra/settings.py
from pydantic import BaseModel
import os

class Settings(BaseModel):
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "commandlayer")
    db_password: str = os.getenv("DB_PASSWORD", "commandlayer")
    db_name: str = os.getenv("DB_NAME", "commandlayer")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()
