from fastapi import FastAPI
from app.infra.db import ping_db
from app.api.routes.commands import router as commands_router

app = FastAPI(title="CommandLayer AI")

app.include_router(commands_router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    ok = ping_db()
    if ok:
        return {"status": "ok", "db": "ok"}
    return {"status": "degraded", "db": "error"}
