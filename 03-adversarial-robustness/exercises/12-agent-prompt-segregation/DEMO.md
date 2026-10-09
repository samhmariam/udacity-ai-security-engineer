# Demo — Agent Prompt Segregation

**Lesson 25** · video topher `206715` · watch before you start the exercise.

## What the video shows

Kevin shows an extraction attempt against a prompt that concatenates system instructions and user text into one message, then the correct version where each stays in its own role. The boundary is structural rather than written in prose.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-12-agent-prompt-segregation/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

Kevin points out this stub is deliberately not empty: `chat_unsafe()` is fully implemented so you can watch unsafe input reach the model. Your job is **`chat_safe()`**, which is the same call with the two parts kept apart.

## What to carry into the exercise

Every earlier defense told the model what to do. This one changes what the model can see as an instruction in the first place. That is why it is last.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
