# Demo — Aria Named Guardrails

**Lesson 23** · video topher `206710` · watch before you start the exercise.

## What the video shows

Three probes against the same prompt: salary is handled by RULE-01, personal data by RULE-02, and the roadmap probe leaks — as Kevin puts it, "because nothing explicitly forbids it." The fix is to write the missing rule.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-11-aria-named-guardrails/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

The unguarded run often deflects rather than leaking outright, so the contrast can look weak. Read both answers closely: a hedge that still confirms the feature exists is a leak.

## What to carry into the exercise

Numbered rules are what make a prompt auditable. You can say "RULE-03 failed" in a report, and you can see which topics have no rule at all — which is the gap this exercise is really about.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
