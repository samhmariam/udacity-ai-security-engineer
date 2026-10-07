# Demo — Aria RAG Poisoning

**Lesson 11** · video topher `206704` · watch before you start the exercise.

## What the video shows

Aria answers from a retrieved knowledge base. Kevin asks the same question twice — once against a clean document, once against a poisoned one — and the second answer claims expense limits have been removed. He then shows the sanitisation step that catches it.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-05-aria-rag-poisoning/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

The video describes sanitising a document and returning an empty string. Your file implements **`scan_for_injection()`**, which flags rather than blanks, and the scan runs as a second pass *after* the queries. So the fixed run still shows the bad answer, then flags the file. Detection, not prevention — SP03 was prevention.

## What to carry into the exercise

The knowledge base is not a trust boundary just because you own it. A document poisoned after ingestion attacks every query that retrieves it.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
