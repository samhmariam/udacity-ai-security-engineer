# SP05 — Aria RAG Poisoning

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Northstar uses retrieved documents. If those documents are poisoned, the model can be manipulated even when the user query looks harmless.

---

## Background

**RAG (Retrieval-Augmented Generation)** means the model does not answer from memory alone. At query time, relevant documents are retrieved from a knowledge base and passed to the model as context. The model uses that retrieved content to ground its answer. That is powerful — and it is also a new attack surface: if a retrieved document contains injected instructions, the model may treat them as legitimate.

Aria answers employee questions using a small knowledge base. One of the documents contains a malicious instruction designed to override the normal expense-policy answer. The user's query looks completely harmless — but the poisoned document changes what Aria returns.

There is also a second failure mode worth watching for: a scanner that only checks exact keywords can be evaded by an attacker who rephrases the payload slightly. Your implementation catches the obvious case, but the discussion questions ask you to think about what comes next.

Your job is to add a **simple content-screening control** that flags the poisoned document before it is trusted as context.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP05
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp05.py`
- Function: `scan_for_injection(doc_text)`

Steps:

1. Run the script once and compare the clean-document answer with the poisoned-document answer.
2. Edit only `scan_for_injection(doc_text)`.
3. Re-run the script.

You are done when:

- `vendor_evaluation.txt` is flagged
- the other documents are not flagged

---

## Hint

Start with obvious prompt-injection markers such as:

- `SYSTEM:`
- `ignore your`
- `ignore all`
- `previous instructions`

---

## Security Note

This is a narrow teaching control. Real RAG security is broader than phrase matching. You would also want ingestion controls, trust metadata, provenance, retrieval constraints, and validation of what gets passed to the model.

---

## Deliverable

`aria_sp05_results.json` — auto-saved. Scan results should show one flagged document.

---

## Discussion Questions

1. What kind of access would an attacker need to poison this knowledge base?
2. What false-positive risk comes with simple phrase scanning?
3. What control besides content scanning could reduce this risk?
