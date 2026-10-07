# Demo — Aria Indirect Injection

**Lesson 07** · video topher `207035 / 206702` · watch before you start the exercise.

## What the video shows

This is where Aria is introduced — the internal assistant for Vantage Systems that every later exercise uses. Kevin summarises three employee documents. One of them, the vendor meeting notes, carries a hidden instruction, and Aria repeats it in the summary. He then opens the poisoned document and shows the payload sitting in the text.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-03-aria-indirect-injection/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

The video calls the control `sanitize_document` and points at line 52. In your file it is **`block_injection()`**, and it returns `True`/`False` rather than cleaned text — the surrounding code prints `[BLOCKED]` and records `"blocked": true`. Same control, different name.

## What to carry into the exercise

The attacker needed no access and no credentials. They only needed to write something the pipeline would later read. That is the whole attack.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
