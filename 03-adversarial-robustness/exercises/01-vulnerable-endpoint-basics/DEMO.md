# Demo — Reliable Prompt Injection Basics

**Lesson 03** · video topher `207031` · watch before you start the exercise.

## What the video shows

Kevin opens the vulnerable SecureBank endpoint and works through a warmup on `/chat-no-protection` — no system prompt at all, so there is nothing to bypass — then three injection challenges against `/chat`, which does carry a system prompt with a secret in it. Each attempt is saved to a results file as he goes.

## Following along

This pair has no `demo/` folder, because there is no stub to fill in — SP01 is an
attack session, not a code exercise. The script you watch is the script you run.

Start the target first, in its own terminal:

```bash
cd /voc/startercode/course_materials/target
bash setup_target.sh
./start_target.sh
```

Then, in a second terminal:

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP01
```

## What to carry into the exercise

The endpoint's only defense is a politely worded system prompt. Watch how little it takes to get past that, and notice that the prompts which work best do not look like attacks.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
