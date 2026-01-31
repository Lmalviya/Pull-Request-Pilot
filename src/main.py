from fastapi import FastAPI
from src.api.webhook import router as webhook_router

app = FastAPI(title="Pull Request Pilot")

@app.get("/health")
def health():
    return {"status": "OK"}

app.include_router(webhook_router)