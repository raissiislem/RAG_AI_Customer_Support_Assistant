from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import Base, engine
from routers.auth import router as auth_router
from routers.conversations import router as conversations_router
from routers.rag import router as rag_router

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "rag"
    )
)

from rag_core import RAGEngine  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    app.state.rag_engine = RAGEngine()
    yield


app = FastAPI(
    title="BIAT RAG Assistant",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(rag_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "rag_loaded": hasattr(app.state, "rag_engine") and app.state.rag_engine is not None,
    }
