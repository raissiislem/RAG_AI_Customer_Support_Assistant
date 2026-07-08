
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
from fastapi.middleware.cors import CORSMiddleware
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

# Allow browser clients, including the Angular frontend, to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="The user's question in French")
    session_id: str = Field(..., description="Client-generated ID used to track conversation history")


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    matched: bool  # whether relevant documents were found, or this is the fallback message
    standalone_question: str  # what was actually searched, after history-based rewriting


@app.get("/")
def root():
    return {"status": "ok", "service": "BIAT RAG Assistant API"}


@app.get("/health")
def health():
    return {"status": "ok", "engine_loaded": engine is not None}


# In-memory session store: session_id -> list of {"question", "answer"}.
# Fine for a single-instance dev/demo project. If you ever run multiple API
# workers or restart the server often, move this to Redis or a DB table
# instead, since this dict resets on every restart.
sessions: dict[str, list[dict]] = {}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not ready yet, try again shortly.")

    history = sessions.get(request.session_id, [])

    result = engine.ask(request.question, history=history)

    # store this turn for next time
    sessions.setdefault(request.session_id, []).append({
        "question": request.question,
        "answer": result["answer"],
    })

    # log for analytics (Week 7) — silently no-ops if Postgres isn't set up
    db.log_query(
        question=request.question,
        answer=result["answer"],
        matched=result["matched"],
        sources=result["sources"],
    )

    return AskResponse(**result)