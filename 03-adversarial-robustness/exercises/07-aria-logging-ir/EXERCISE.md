# SP07 — Aria Logging and IR

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** A secure system needs evidence, not just intentions. Logging and incident response are part of the Northstar capstone because attacks that cannot be reconstructed are much harder to contain.

---

## Background

Aria currently handles suspicious requests without leaving a usable audit trail. If an attack attempt happens, there is no durable structured record of what was asked, how Aria responded, or whether the interaction looked anomalous.

The script runs four interactions: a PTO policy question, an expense submission question, a malicious query attempting salary disclosure, and a performance review question. Three are routine. One is a prompt injection attempt. Without logging, all four look identical from the outside — there is nothing to reconstruct, escalate, or hand to an IR team.

Your job is to implement structured JSON logging so each interaction leaves behind evidence that can be analyzed, filtered, and acted on.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP07
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp07.py`
- Function: `log_interaction(user_id, query, response)`

Steps:

1. Run the script once and confirm that no useful log is written yet.
2. Edit only `log_interaction(user_id, query, response)`.
3. Re-run the script.

You are done when:

- `aria_sp07.log` exists
- it contains four JSON lines
- the suspicious interaction is marked `anomalous: true`

---

## What To Log

Each entry should include:

- timestamp
- user ID
- query
- response excerpt
- anomaly flag

---

## Deliverable

`aria_sp07.log` — four JSON lines, with one suspicious entry marked anomalous.

---

## Discussion Questions

1. Why is JSON logging better than free-form text for downstream analysis?
2. What is the limitation of flagging anomalies only from the response instead of the query?
3. What other fields would you add for a real IR workflow?
