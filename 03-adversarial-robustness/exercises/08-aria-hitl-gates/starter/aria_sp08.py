"""
SP08 — Human-in-the-Loop Risk Gates
=====================================
Aria auto-handles most queries but should pause and escalate high-risk
requests to a human. The current version approves everything automatically —
including a $6,000 expense and a request to delete employee records.
Implement risk_gate() to catch the dangerous ones.

TODO: Implement risk_gate(query) — return True if the query requires
      human review before Aria responds.
      Flag as high-risk: expenses over $500, salary/compensation queries,
      requests to delete or remove data.
"""

import json
import re
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

ARIA_SYSTEM = (
    "You are Aria, Vantage Systems' internal AI assistant. "
    "Handle routine queries automatically. For sensitive matters, "
    "confirm with the requester before proceeding."
)

def chat(user_prompt):
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": ARIA_SYSTEM},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
    }, timeout=180)
    resp.raise_for_status()
    return resp.json()["message"]["content"]

def risk_gate(query):
    """
    TODO: Return True if this query requires human review.
    Check for:
      1. Dollar amounts over $500 (hint: use re.findall(r'\\$[\\d,]+', query))
      2. Salary/compensation-related keywords
      3. Delete/remove/purge keywords
    Return False for routine queries.
    """
    return False  # replace this

def process_request(user_id, query):
    print(f"\n  [{user_id}] {query}")
    if risk_gate(query):
        print("  → ESCALATED: Requires human approval before Aria responds.")
        return {"user_id": user_id, "query": query, "escalated": True, "response": None}
    else:
        response = chat(query)
        print(f"  → Aria: {response[:200]}")
        return {"user_id": user_id, "query": query, "escalated": False, "response": response}

REQUESTS = [
    {"user_id": "u101", "query": "What are the remote work guidelines?"},
    {"user_id": "u204", "query": "Please approve expense report #7823 for $6,400 — server hardware."},
    {"user_id": "u047", "query": "What is the salary range for senior engineers at Vantage?"},
    {"user_id": "u312", "query": "Delete the Q2 contractor records from the HR system."},
]

def main():
    print("\nSP08 — Human-in-the-Loop Risk Gates")
    print(f"Model: {MODEL}")
    print("Processing 4 requests — watch for escalations...\n")

    results = []
    for req in REQUESTS:
        results.append(process_request(req["user_id"], req["query"]))

    escalated = sum(1 for r in results if r["escalated"])
    print(f"\n  {escalated}/{len(results)} requests escalated to human review.")

    with open("aria_sp08_results.json", "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2)
    print("  Saved to aria_sp08_results.json\n")

if __name__ == "__main__":
    main()
