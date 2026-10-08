# Demo — Vulnerable Agent Task Hijacking

**Lesson 19** · video topher `206708` · watch before you start the exercise.

## What the video shows

An agent summarises a client report and then chooses its next action. Kevin appends a payload to the report, and the agent's second step changes from drafting the client email to sending an internal security alert — hijacked by the document it was asked to read.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-09-vulnerable-agent-task-hijacking/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

The hijack does not fire every run — the model sometimes ignores the payload. If your fixed run shows the correct action, that is not proof your validator works. Re-run until the hijack lands, or test `validate_action()` directly against a hijacked plan.

## What to carry into the exercise

The agent was not tricked into answering wrongly. It was tricked into *doing* something else. Constrain which actions a workflow may take, not just what the model may say.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
