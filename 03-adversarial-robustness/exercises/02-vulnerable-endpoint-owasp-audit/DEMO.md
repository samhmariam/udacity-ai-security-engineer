# Demo — OWASP Audit of a Vulnerable LLM App

**Lesson 05** · video topher `207033` · watch before you start the exercise.

## What the video shows

The same endpoint, now assessed rather than attacked. Kevin walks the OWASP LLM Top 10, probes one category at a time, and records a verdict against stated pass criteria — including output handling, where the risk is not in the model but in whatever renders what it returns.

## Following along

This pair has no `demo/` folder, because there is no stub to fill in — SP02 is an
audit, not a code exercise. The script you watch is the script you run.

SP01's target must be running. If it is not:

```bash
cd /voc/startercode/course_materials/target
./start_target.sh
```

Then, in a second terminal:

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP02
```

## What to carry into the exercise

An audit is evidence plus a verdict, not a feeling. Every FAIL you record needs the response text that justifies it — and expect at least one genuine PASS, because a rubric where everything fails teaches nothing.

## Your turn is not a repeat of the video

The video hands you a working control. The exercise asks you to find where it
fails. Read `EXERCISE.md` next.
