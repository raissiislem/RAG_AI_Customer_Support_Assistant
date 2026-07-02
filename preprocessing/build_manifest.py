"""
Builds two manifest files from your topic-organized .txt files:
  - manifest.json          : one row per file (summary — matches your Week 1-2 plan)
  - manifest_detailed.json : one row per section (title + source URL) — useful later
                              for citation lookups and for the ingestion pipeline to
                              track exactly what was scraped and when.

Run this after any re-scrape/re-categorization to keep the manifest in sync.
"""

import re
import os
import json
from datetime import date

DATA_DIR = r"C:\Files\RAG Project\biat-rag-assistant\data"   # change to your local data/ folder
OUT_DIR = r"C:\Files\RAG Project\biat-rag-assistant\data"    # where manifest files get written

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


def topic_name_from_filename(filename):
    # "loans_credit_biat.txt" -> "loans_credit"
    return filename.replace("_biat.txt", "").replace(".txt", "")


def parse_sections(filepath):
    """Return list of (title, source_url) for each ===== Title ===== block."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"^={5}\s*(.+?)\s*={5}\s*$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    sections = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]

        source_match = re.search(r"^Source:\s*(.+)$", block, re.MULTILINE)
        source_url = source_match.group(1).strip() if source_match else None

        sections.append({"title": title, "source_url": source_url})

    return sections


def main():
    summary = []
    detailed = []
    today = date.today().isoformat()

    for filename in TOPIC_FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Skipping missing file: {filename}")
            continue

        sections = parse_sections(filepath)
        topic = topic_name_from_filename(filename)

        summary.append({
            "file": filename,
            "topic": topic,
            "sections": len(sections),
            "date_collected": today,
        })

        detailed.append({
            "file": filename,
            "topic": topic,
            "date_collected": today,
            "sections": sections,
        })

    summary_path = os.path.join(OUT_DIR, "manifest.json")
    detailed_path = os.path.join(OUT_DIR, "manifest_detailed.json")

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with open(detailed_path, "w", encoding="utf-8") as f:
        json.dump(detailed, f, ensure_ascii=False, indent=2)

    total_sections = sum(row["sections"] for row in summary)
    print(f"manifest.json: {len(summary)} files, {total_sections} total sections")
    print(f"manifest_detailed.json: same files, with per-section titles + source URLs")


if __name__ == "__main__":
    main()
