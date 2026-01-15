from fastapi import FastAPI
from app.infra.db import ping_db

app = FastAPI(title="CommandLayer AI")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    ok = ping_db()
    if ok:
        return {"status": "ok", "db": "ok"}
    return {"status": "degraded", "db": "error"}
