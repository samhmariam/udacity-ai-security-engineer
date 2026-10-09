"""
load_knowledge_base.py — Initialize the Northstar ChromaDB knowledge base.

Usage:
    sudo python3 load_knowledge_base.py
    sudo python3 load_knowledge_base.py --with-malicious
    sudo python3 load_knowledge_base.py --reset
"""

# Fix for containers running Python 3.10 with sqlite3 < 3.35.0 (required by ChromaDB)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import argparse
import logging
import os
import sys

os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Suppress ChromaDB telemetry noise (posthog API mismatch in older chromadb versions)
for _n in ["chromadb", "chromadb.telemetry", "chromadb.telemetry.product", "chromadb.telemetry.product.posthog"]:
    _l = logging.getLogger(_n)
    _l.setLevel(logging.CRITICAL)
    _l.addHandler(logging.NullHandler())
    _l.propagate = False
try:
    import posthog
    posthog.disabled = True
except ImportError:
    pass

import chromadb

KNOWLEDGE_BASE_PATH = "./chroma_data"
COLLECTION_NAME = "northstar_knowledge_base"

# ---------------------------------------------------------------------------
# Built-in Northstar documents
# ---------------------------------------------------------------------------

LEGITIMATE_DOCS = [
    {
        "id": "northstar-ai-policy",
        "title": "Northstar AI Usage Policy",
        "content": open("knowledge_base/northstar_ai_policy.md").read()
            if os.path.exists("knowledge_base/northstar_ai_policy.md") else "",
    },
    {
        "id": "security-incident-proc",
        "title": "Security Incident Reporting Procedure",
        "content": open("knowledge_base/security_incident_procedure.md").read()
            if os.path.exists("knowledge_base/security_incident_procedure.md") else "",
    },
    {
        "id": "acceptable-use-guidelines",
        "title": "Research Agent Acceptable Use Guidelines",
        "content": open("knowledge_base/acceptable_use_guidelines.md").read()
            if os.path.exists("knowledge_base/acceptable_use_guidelines.md") else "",
    },
]

MALICIOUS_DOCS = [
    {
        "id": "malicious-001-override",
        "title": "Malicious Doc 1: Explicit Override",
        "content": open("knowledge_base/malicious/poisoned_explicit_override.md").read()
            if os.path.exists("knowledge_base/malicious/poisoned_explicit_override.md") else "",
    },
    {
        "id": "malicious-002-subtle",
        "title": "Malicious Doc 2: Subtle Diagnostic Framing",
        "content": open("knowledge_base/malicious/poisoned_diagnostic_framing.md").read()
            if os.path.exists("knowledge_base/malicious/poisoned_diagnostic_framing.md") else "",
    },
    {
        "id": "malicious-003-metadata",
        "title": "Malicious Doc 3: Embedded Metadata Instructions",
        "content": open("knowledge_base/malicious/poisoned_metadata.md").read()
            if os.path.exists("knowledge_base/malicious/poisoned_metadata.md") else "",
    },
]

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_documents(collection, docs, doc_type):
    loaded = 0
    for doc in docs:
        if not doc["content"]:
            print(f"  SKIPPED (empty): {doc['id']}")
            continue
        try:
            collection.upsert(
                ids=[doc["id"]],
                documents=[doc["content"]],
                metadatas=[{"title": doc["title"], "type": doc_type}],
            )
            print(f"  Added: {doc['id']:<40} ({doc['title']})")
            loaded += 1
        except Exception as e:
            print(f"  ERROR loading {doc['id']}: {e}")

    return loaded


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-malicious", action="store_true",
                        help="Also load pre-built malicious documents")
    parser.add_argument("--reset", action="store_true",
                        help="Delete and recreate the collection")
    args = parser.parse_args()

    print("Loading Northstar knowledge base...")
    os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)
    for _sub in ("reports", "attacks", "defenses"):
        os.makedirs(os.path.join("student_work", _sub), exist_ok=True)

    client = chromadb.PersistentClient(path=KNOWLEDGE_BASE_PATH)

    if args.reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("  [Reset] Existing collection deleted.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Load built-in docs
    total = load_documents(collection, LEGITIMATE_DOCS, "legitimate")

    if args.with_malicious:
        print("\nLoading malicious documents (for indirect injection testing)...")
        total += load_documents(collection, MALICIOUS_DOCS, "malicious")

    print(f"\nKnowledge base ready. {total} documents loaded.")

    if total == 0:
        print("  [ERROR] No documents were loaded. Check that you are running this "
              "from the project root and that knowledge_base/ is present.")


if __name__ == "__main__":
    main()
