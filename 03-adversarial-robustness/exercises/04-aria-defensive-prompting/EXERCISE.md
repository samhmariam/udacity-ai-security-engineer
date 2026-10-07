# SP04 — Aria Defensive Prompting

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Writing a hardened system prompt is one of the first practical defenses students usually reach for. You need to know both what it can do and what it cannot do.

---

## Background

In SP01 you saw direct prompt injection work against a deliberately vulnerable endpoint. Aria is a more structured target, but the same attack families still apply:

- **Persona replacement** — tell the model it is a different system with different rules
- **Authority impersonation** — claim to be an admin, a developer, or an override mechanism
- **False-premise continuation** — assert something incorrect and prompt the model to continue from that premise

This SP runs in two steps. First, you craft your own attacks interactively so you understand exactly what each family looks like in practice. Then you write a hardened system prompt designed to resist the attacks you just used. Both steps matter — you cannot write a useful defense without first understanding what you are defending against.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP04
```

---

## Instructions

The exercise runs in two steps.

**Step 1 — Craft your attacks (interactive, no file edits needed)**

Run the script. It presents three attack families — Persona Replacement, Authority Impersonation, and False Premise. For each one, read the goal and hint, then write your own attack prompt at the input. The script stores your prompts and will use them in the comparison.

**Step 2 — Write the hardened system prompt (requires a file edit)**

- File: `starter/aria_sp04.py`
- Constant: `HARDENED_SYSTEM`

Rewrite `HARDENED_SYSTEM` in 4-8 sentences with explicit prohibitions for the three attack families, then re-run the script. The comparison will show your attacks against both the weak and hardened prompts side by side.

---

## What To Aim For

Your hardened prompt should make Aria:

- refuse attempts to redefine its role
- reject text-only authority claims it cannot verify
- challenge false assumptions instead of continuing from them

Keep in mind that prompting raises the bar — it does not eliminate it. A well-crafted prompt will reduce success rates, but a determined attacker with enough attempts can still find gaps. The goal here is to understand both what hardened prompting achieves and where it runs out.

---

## Variability Note

Prompt hardening is not perfectly deterministic. If one attack looks weaker on your run, compare the weak and hardened responses carefully and explain the difference you still see.

---

## Deliverable

`aria_sp04_results.json` — auto-saved. It should show a clear before/after difference between weak and hardened behavior.

---

## Discussion Questions

1. Which attack family was hardest to suppress with prompt wording alone?
2. What attack would you try next if you wanted to break your own hardened prompt?
3. What control besides prompting would you pair with this defense?
