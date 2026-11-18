"""API do EloBairro. Rodar a partir de 01-front-end: uvicorn api.main:app --port 8000"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import visao

app = FastAPI(title="EloBairro API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(visao.router)


@app.get("/saude")
def saude():
    return {"status": "ok"}
