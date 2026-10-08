# SP08 — Aria Human Risk Gates

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** The capstone's tool permission design (Step 9) asks you to decide which agent actions require human sign-off before executing. The escalation logic you build here is the thinking behind that decision — not every high-risk request should be denied, but some should never proceed without a human in the path.

---

## Background

Aria currently auto-processes all requests, including ones that obviously should not be handled without review.

The script runs four requests: a remote work policy question, a $6,400 server hardware expense approval, a salary range query, and a request to delete Q2 contractor records from the HR system. The first is routine. The other three carry financial, privacy, or data integrity risk that should never be handled by an AI without human review.

The key distinction here is escalation versus denial. A human-in-the-loop gate does not automatically block the request — it pauses processing and routes the request to a human reviewer. The human decides. That matters in practice: not every high-risk query is malicious, but all of them deserve a human in the decision path.

Your job is to implement a lightweight escalation rule so high-risk requests pause for human approval instead of flowing straight through the system.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP08
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp08.py`
- Function: `risk_gate(query)`

Steps:

1. Run the script once and observe all requests being handled automatically.
2. Edit only `risk_gate(query)`.
3. Re-run the script.

You are done when:

- the high-risk requests are escalated
- the routine policy question is not escalated

---

## Hint

Start by checking for:

- large dollar amounts
- salary or compensation requests
- delete/remove/purge requests

---

## Security Note

This exercise uses a text-based gate so the approval pattern is easy to see. Real systems would combine structured request data, identity, risk scoring, and workflow controls.

---

## Deliverable

`aria_sp08_results.json` — auto-saved. Risky entries should show `"escalated": true`.

---

## Discussion Questions

1. Where should an escalated request go in a real organization?
2. How could an attacker try to bypass your gate by rephrasing the request?
3. What structured inputs would make this control stronger?
