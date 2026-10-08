# SP10 — Aria Multimodal Injection

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Multimodal injection does not appear as a deliverable in the capstone — but it appears in production wherever AI systems process files, PDFs, or images. What this exercise builds is attack-surface awareness: any input channel the system reads from is a potential injection vector, not just the chat interface.

---

## Background

Aria processes text extracted from submitted receipts. One receipt contains hidden instruction content mixed into the otherwise normal receipt text.

Your job is to add a simple sanitizer that strips the obvious malicious lines before they reach the model.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP10
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp10.py`
- Function: `text_sanitizer(raw_text)`

Steps:

1. Run the script once and observe the poisoned receipt affecting Aria's response.
2. Edit only `text_sanitizer(raw_text)`.
3. Re-run the script.

You are done when:

- the poisoned receipt is detected as sanitized
- the second receipt produces a safer response after cleaning

---

## Hint

Strip lines containing obvious markers such as:

- `SYSTEM:`
- `admin mode`
- `ignore`
- `waived`
- `override`

---

## Security Note

Line stripping is a teaching aid, not a durable multimodal defense. Real systems need better controls around extraction pipelines, metadata trust, and prompt construction.

---

## Deliverable

`aria_sp10_results.json` — auto-saved. The poisoned receipt should show `"sanitized": true`.

---

## Discussion Questions

1. What other file types besides receipt text could carry hidden instructions?
2. How would a payload split across multiple lines challenge your sanitizer?
3. What stronger control would you pair with this in production?
