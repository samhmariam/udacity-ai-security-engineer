# Demo — Aria Defensive Prompting

**Lesson 09** · video topher `206703` · watch before you start the exercise.

## What the video shows

Kevin starts on the weak system prompt — one sentence, no rules — and runs three attack families against it: persona replacement (become VEGA), authority impersonation (I am the CISO), and false premise (thanks for sharing the salary figures earlier). Then he runs the hardened version and reads all five rules out loud.

## Following along in this folder

```bash
cd /voc/startercode/course_materials/exercises/skill-pair-04-aria-defensive-prompting/demo
python3 aria_vulnerable.py    # the stub is empty — the attack lands
python3 aria_fixed.py         # the stub is filled in — the attack is stopped
```

Those two files are **one program in two states**. `aria_vulnerable.py` is exactly
the starter you are about to edit. `aria_fixed.py` is that same file with the one
stub completed. Both are generated from `starter/` and `solutions/`, so what you
watch and what you edit can never drift apart.

## Where the video's wording differs from your files

The video reads the finished hardened prompt aloud, so you will hear the answer before you write anything. That is deliberate — see the last section.

## What to carry into the exercise

Note which attack succeeded and which one Aria refused *by luck*. Kevin says it on camera: "there weren't really any protections in place. We just got lucky this time." A defense you cannot explain is not a defense.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
