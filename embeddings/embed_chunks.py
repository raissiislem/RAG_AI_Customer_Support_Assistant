"""
Reads the topic .txt files (already split into ===== Title ===== sections),
treats each section as one chunk, and generates a bge-m3 embedding for each.

Output: chunks_with_embeddings.json
    Each entry: {id, topic, title, source_url, text, embedding}

This file is what you'll upload to Qdrant in the next step.
"""

import re
import os
import json
import hashlib
from sentence_transformers import SentenceTransformer

DATA_DIR = r"C:\Files\RAG Project\biat-rag-assistant\data"
OUT_PATH = r"C:\Files\RAG Project\biat-rag-assistant\embeddings\chunks_with_embeddings.json"

TOPIC_FILES = [
    "loans_credit_biat.txt",
    "credit_cards_biat.txt",
    "savings_investments_biat.txt",
    "accounts_biat.txt",
    "transfers_operations_biat.txt",
    "cheques_documents_biat.txt",
    "packages_biat.txt",
    "digital_banking_biat.txt",
    "other_services_biat.txt",
    "insurance_biat.txt",
    "bill_payments_biat.txt",
]


def parse_sections(filepath):
    """Return list of (title, source_url, body_text) per ===== Title ===== block."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"^={5}\s*(.+?)\s*={5}\s*$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    sections = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end].strip()

        source_match = re.search(r"^Source:\s*(.+)$", block, re.MULTILINE)
        source_url = source_match.group(1).strip() if source_match else None

        # strip the "(from ...)" and "Source:" metadata lines to get pure body text
        body_lines = [
            line for line in block.splitlines()
            if not line.startswith("(from ") and not line.startswith("Source:")
        ]
        body_text = "\n".join(body_lines).strip().lstrip("-").strip()

        sections.append((title, source_url, body_text))

    return sections


def make_chunk_id(topic, title):
    raw = f"{topic}:{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def main():
    print("Loading bge-m3 model (first run downloads ~2.2GB, be patient)...")
    model = SentenceTransformer("BAAI/bge-m3")

    all_chunks = []

    for filename in TOPIC_FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Skipping missing file: {filename}")
            continue

        topic = filename.replace("_biat.txt", "")
        sections = parse_sections(filepath)
        print(f"{filename}: {len(sections)} sections")

        for title, source_url, body_text in sections:
            if not body_text:
                continue  # skip empty sections (e.g. failed fetches)

            # embed title + body together — helps retrieval match on the
            # product/service name itself, not just its description
            embed_input = f"{title}\n{body_text}"

            all_chunks.append({
                "id": make_chunk_id(topic, title),
                "topic": topic,
                "title": title,
                "source_url": source_url,
                "text": body_text,
                "embed_input": embed_input,  # temp field, removed after embedding
            })

    print(f"\nTotal chunks to embed: {len(all_chunks)}")
    print("Generating embeddings (this may take a few minutes on CPU)...")

    texts = [c["embed_input"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    for chunk, embedding in zip(all_chunks, embeddings):
        chunk["embedding"] = embedding.tolist()
        del chunk["embed_input"]  # no longer needed

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False)

    print(f"\nSaved {len(all_chunks)} chunks with embeddings to {OUT_PATH}")
    print(f"Embedding dimension: {len(all_chunks[0]['embedding'])}")


if __name__ == "__main__":
    main()
