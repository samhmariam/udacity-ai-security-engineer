# Demo — Aria Logging and IR

**Lesson 15** · video topher `206706` · watch before you start the exercise.

## What the video shows

Four interactions run through Aria, one of them an injection attempt. In the vulnerable state nothing is recorded at all. Kevin then shows the filled-in logging routine writing one JSON line per interaction, and walks what you would look for during an incident.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-07-aria-logging-ir/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

The difference is in the **log file**, not the terminal — both runs print the same thing. Check `aria_sp07.log`: empty in the vulnerable state, four JSON lines in the fixed one.

Also worth knowing: `RED_FLAGS` inspects the *response*, so the injection attempt from user u047 logs as `"anomalous": false` when Aria refuses cleanly. The obvious attack goes unflagged. That is a real gap, and a good thing to fix in the exercise.

## What to carry into the exercise

You cannot investigate what you did not record. Decide what a responder would need at 3am, then log that — including attempts that failed.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
