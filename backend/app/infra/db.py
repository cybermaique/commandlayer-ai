# app/infra/db.py
from sqlalchemy import create_engine, text
from app.infra.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

def ping_db() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
