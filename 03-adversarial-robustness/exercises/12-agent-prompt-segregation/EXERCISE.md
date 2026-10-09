# SP12 — Agent Prompt Segregation

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Prompt segregation is one of the clearest structural defenses in the course. It also provides a direct bridge from simple prompt injection to safer agent construction.

---

## Background

Aria has two ways to build a request:

- `chat_unsafe()` concatenates instructions and user input into one string
- `chat_safe()` is supposed to separate them by role

When system instructions and user content are mixed into the same unstructured block, the model has a much weaker signal about what is instruction versus what is data. Your job is to fix that.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP12
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp12.py`
- Function: `chat_safe(user_input)`

Steps:

1. Run the script once and observe the unsafe injection case.
2. Edit only `chat_safe(user_input)`.
3. Put `ARIA_SYSTEM` in a `system` message.
4. Put `user_input` in a `user` message.
5. Do not concatenate them into a single string.
6. Re-run the script and compare the unsafe and safe outputs.

---

## Goal

The safe version should respond differently to the injection attempt because the model receives a clearer structural boundary between instruction and user content.

---

## Security Note

Role-level separation is stronger than raw concatenation because the model has been trained to treat the `system` role as instructions and the `user` role as input. When those are kept structurally separate, the model has a clearer signal about which content it should obey versus which it should process. When they are concatenated into one string, that signal disappears — everything looks like it could be an instruction. Separation does not make injection impossible, but it meaningfully raises the bar compared to flat text.

It still needs surrounding controls such as output validation, tool restrictions, and safer handling of retrieved content.

---

## Deliverable

`aria_sp12_results.json` — auto-saved. Compare `unsafe_response` and `safe_response` for the injection case.

---

## Discussion Questions

1. Why does role separation provide a stronger signal than plain text labels?
2. Why is prompt segregation still not enough by itself?
3. Where else in an agent pipeline should you preserve structure instead of flattening data into free text?
