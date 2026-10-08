# Demo — Aria Multimodal Injection

**Lesson 21** · video topher `206709` · watch before you start the exercise.

## What the video shows

A receipt for $261.96 is uploaded for review. Its extracted text carries an appended instruction, and Aria replies that the receipt is approved for $10,000 and all future expense limits have been waived. Kevin then shows the sanitiser stripping the payload.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-10-aria-multimodal-injection/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

Kevin notes the stub here is not empty — it returns the text unchanged, so you can see raw content reaching the model. Your **`text_sanitizer()`** strips offending lines and keeps the rest, rather than rejecting the whole file as SP03 and SP05 do.

## What to carry into the exercise

Images, PDFs and scans all become a string before the model sees them. One text function defends every input format, because extraction is where multimodal turns into text.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
