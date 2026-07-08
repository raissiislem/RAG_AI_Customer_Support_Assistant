"""
Uploads your 134 embedded chunks into Qdrant, then runs a test query
to prove retrieval actually works.

Prereqs:
  - Qdrant running (docker run -p 6335:6333 -p 6336:6334 qdrant/qdrant)
  - chunks_with_embeddings.json already generated (from embed_chunks.py)
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"  # use cached model, skip the online version check

import json
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

CHUNKS_PATH = "biat-rag-assistant\\embeddings\\chunks_with_embeddings.json"  # adjust path if needed
COLLECTION_NAME = "biat_docs"
QDRANT_PORT = 6335  # matches the -p 6335:6333 mapping above
EMBEDDING_DIM = 1024  # bge-m3 output size, confirmed from your sanity check
    

def load_chunks():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def upload_chunks(client, chunks):
    # (re)create the collection fresh each run — simplest for a dev workflow
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    points = []
    for i, chunk in enumerate(chunks):
        points.append(
            PointStruct(
                id=i,  # Qdrant wants an integer or UUID id, not our hash string
                vector=chunk["embedding"],
                payload={
                    "chunk_id": chunk["id"],
                    "topic": chunk["topic"],
                    "title": chunk["title"],
                    "source_url": chunk["source_url"],
                    "text": chunk["text"],
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Uploaded {len(points)} chunks to Qdrant collection '{COLLECTION_NAME}'")


def search(client, model, query_text, top_k=3):
    query_vector = model.encode(query_text, normalize_embeddings=True).tolist()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )
    results = response.points

    print(f"\nQuery: \"{query_text}\"")
    print(f"Top {top_k} results:")
    for r in results:
        print(f"  [{r.score:.3f}] {r.payload['title']}  ({r.payload['topic']})")
        print(f"          {r.payload['source_url']}")


if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer

    print("Connecting to Qdrant...")
    client = QdrantClient(host="localhost", port=QDRANT_PORT)

    print("Loading chunks...")
    chunks = load_chunks()

    upload_chunks(client, chunks)

    print("\nLoading bge-m3 model for test queries (uses your cached download)...")
    model = SentenceTransformer("BAAI/bge-m3")

    # a few test queries in French, matching your BIAT content
    test_queries = [
        "comment avoir un crédit pour une voiture",
        "je veux payer ma facture STEG",
        "quelles sont les cartes bancaires disponibles",
    ]

    for q in test_queries:
        search(client, model, q)