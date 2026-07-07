import json

data = json.load(open("biat-rag-assistant\\embeddings\\chunks_with_embeddings.json", "r", encoding="utf-8"))

print(f"Total chunks: {len(data)}")
print(f"Embedding dimension: {len(data[0]['embedding'])}")
print()
print("Sample chunk:")
print("  Title:", data[0]["title"])
print("  Topic:", data[0]["topic"])
print("  Source:", data[0]["source_url"])
print("  Text preview:", data[0]["text"][:150])