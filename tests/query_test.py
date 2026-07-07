"""
Runs test queries against your already-uploaded Qdrant collection.

Use this to check retrieval quality without re-uploading chunks every time.
Run upload_to_qdrant.py first (once, or whenever your data changes),
then use this script freely to test as many queries as you want.

Prereqs:
  - Qdrant running (docker run -p 6335:6333 -p 6336:6334 qdrant/qdrant)
  - upload_to_qdrant.py already run at least once
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"  # use cached model, skip the online version check

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "biat_docs"
QDRANT_PORT = 6335  # matches the -p 6335:6333 mapping


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
    print("Connecting to Qdrant...")
    client = QdrantClient(host="localhost", port=QDRANT_PORT)

    print("Loading bge-m3 model (uses your cached download)...")
    model = SentenceTransformer("BAAI/bge-m3")

    # edit/add your own queries here to keep testing retrieval quality
    test_queries = [
        "comment avoir un crédit pour une voiture",
        "je veux payer ma facture STEG",
        "quelles sont les cartes bancaires disponibles",
    ]

    for q in test_queries:
        search(client, model, q)