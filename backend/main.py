"""
FastAPI backend for the BIAT RAG assistant.

Run with:
    uvicorn main:app --reload --port 8000

Then test interactively at:
    http://localhost:8000/docs

Or with curl:
    curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Comment obtenir un credit auto ?\"}"
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "rag"))
from rag_core import RAGEngine
import db

# ---- global engine instance, loaded once at startup ----
engine: RAGEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    print("Loading RAG engine (Qdrant connection + bge-m3 model)...")
    engine = RAGEngine()
    print("RAG engine ready.")
    yield
    print("Shutting down.")


app = FastAPI(
    title="BIAT RAG Assistant API",
    description="Ask questions about BIAT products and services, answered from official documents.",
    version="0.1.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="The user's question in French")


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    matched: bool  # whether relevant documents were found, or this is the fallback message


@app.get("/")
def root():
    return {"status": "ok", "service": "BIAT RAG Assistant API"}


@app.get("/health")
def health():
    return {"status": "ok", "engine_loaded": engine is not None}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not ready yet, try again shortly.")

    result = engine.ask(request.question)

    # log for analytics (Week 7) — silently no-ops if Postgres isn't set up
    db.log_query(
        question=request.question,
        answer=result["answer"],
        matched=result["matched"],
        sources=result["sources"],
    )

    return AskResponse(**result)
