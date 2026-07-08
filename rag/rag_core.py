"""
Core RAG logic: retrieval + prompt building + generation.
Same logic as rag_pipeline.py, but organized as importable functions/class
instead of a script that runs test questions on import.
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import ollama

COLLECTION_NAME = "biat_docs"
QDRANT_PORT = 6335
OLLAMA_MODEL = "qwen2.5:3b"
TOP_K = 4
MIN_SCORE = 0.5 

SYSTEM_PROMPT = """Tu es l'assistant virtuel officiel de la BIAT. Tu réponds aux questions \
des clients UNIQUEMENT à partir du contexte fourni ci-dessous, extrait de documents \
officiels BIAT et MyBIAT.

Règles strictes :
- N'utilise QUE les informations présentes dans le contexte. N'invente rien.
- Si le contexte ne contient pas la réponse, dis clairement : \
"Je n'ai pas cette information dans les documents disponibles, merci de contacter \
votre agence BIAT ou le service client."
- Réponds en français, de façon claire et concise.
- Ne mentionne pas explicitement "le contexte" dans ta réponse ; réponds naturellement, \
comme un conseiller qui connaît ces informations.
"""


class RAGEngine:
    """
    Holds the Qdrant client and embedding model in memory so they're loaded
    ONCE (at API startup), not on every request — this is the key difference
    versus running rag_pipeline.py as a script each time.
    """

    def __init__(self):
        self.client = QdrantClient(host="localhost", port=QDRANT_PORT)
        self.embed_model = SentenceTransformer("BAAI/bge-m3")

    def retrieve(self, query_text, top_k=TOP_K):
        query_vector = self.embed_model.encode(query_text, normalize_embeddings=True).tolist()
        response = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        )
        return response.points

    def build_prompt(self, query_text, chunks):
        context_blocks = [f"[{c.payload['title']}]\n{c.payload['text']}" for c in chunks]
        context = "\n\n---\n\n".join(context_blocks)
        return f"""Contexte :
{context}

Question du client : {query_text}

Réponse :"""

    def ask(self, query_text: str) -> dict:
        """Returns {"answer": str, "sources": list[str], "matched": bool}"""
        chunks = self.retrieve(query_text)
        relevant_chunks = [c for c in chunks if c.score >= MIN_SCORE]

        if not relevant_chunks:
            return {
                "answer": (
                    "Je n'ai pas cette information dans les documents disponibles, "
                    "merci de contacter votre agence BIAT ou le service client."
                ),
                "sources": [],
                "matched": False,
            }

        prompt = self.build_prompt(query_text, relevant_chunks)
        response = ollama.generate(
            model=OLLAMA_MODEL,
            system=SYSTEM_PROMPT,
            prompt=prompt,
        )
        answer = response["response"].strip()

        sources = []
        for c in relevant_chunks:
            url = c.payload["source_url"]
            if url and url not in sources:
                sources.append(url)

        return {"answer": answer, "sources": sources, "matched": True}
