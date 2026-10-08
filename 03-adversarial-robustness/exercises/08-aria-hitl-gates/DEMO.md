# Demo — Aria Human Risk Gates

**Lesson 17** · video topher `206707` · watch before you start the exercise.

## What the video shows

Aria approves a $6,400 expense on its own, out loud — "the report has been approved and the payment will be processed." Kevin then shows the risk gate and names the three signals that trigger escalation: large dollar amounts, compensation keywords, and destructive action keywords.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-08-aria-hitl-gates/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.


## What to carry into the exercise

Kevin's framing on camera is the hard part of this exercise: find the point where you catch the risky requests without sending a human everything. A gate that escalates constantly gets switched off.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
