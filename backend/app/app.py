from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infra.db import ping_db
from app.api.routes.commands import router as commands_router
from app.api.routes.observability import router as observability_router

app = FastAPI(title="CommandLayer AI")

# --- CORS (necessário para frontend web) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend Next.js
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(commands_router)
app.include_router(observability_router)

# --- Health checks ---
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    ok = ping_db()
    if ok:
        return {"status": "ok", "db": "ok"}
    return {"status": "degraded", "db": "error"}
