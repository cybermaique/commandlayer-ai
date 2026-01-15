from fastapi import FastAPI

app = FastAPI(title="CommandLayer AI")

@app.get("/health")
def health():
    return {"status": "ok"}
