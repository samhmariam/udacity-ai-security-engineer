# SP06 — Aria Agent Boundaries

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Multi-agent systems only stay safe if each component has a narrow role and code-level enforcement for that role.

---

## Background

Aria routes work to two sub-agents:

- `ResearchAgent` — answers questions about internal policies and technical topics
- `ApprovalAgent` — handles expense review and approval following a defined policy

An attacker abuses that boundary by framing a $12,000 expense approval as a research question. The query is worded to look like it belongs to ResearchAgent — but the underlying action is a financial approval that should only go through ApprovalAgent with proper review. If the system trusts the wording of the request instead of enforcing the boundary in code, the wrong agent handles the wrong task and a significant financial control fails silently.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP06
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp06.py`
- Function: `enforce_role(agent_name, query)`

Steps:

1. Run the script once and observe the attack case.
2. Edit only `enforce_role(agent_name, query)`.
3. Re-run the script.

You are done when:

- the abusive approval request is blocked
- the legitimate research case still works
- the legitimate approval case still works

---

## Security Note

Keyword matching is only the demo implementation here. The real lesson is that the boundary belongs in code and policy, not just in model instructions.

---

## Deliverable

`aria_sp06_results.json` — auto-saved. The abusive case should show `"blocked": true`.

---

## Discussion Questions

1. Why is code-level role enforcement more trustworthy than a prompt-only rule?
2. How could an attacker evade a naive keyword-based boundary?
3. What stronger boundary would a production system use?
