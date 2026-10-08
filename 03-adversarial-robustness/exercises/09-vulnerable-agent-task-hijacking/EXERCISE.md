# SP09 — Vulnerable Agent Task Hijacking

**Estimated time:** 20 minutes
**Platform:** vulnerable-agent lab
**Capstone connection:** This is the point where Course 3 shifts from prompt problems to action-selection problems. The capstone agent has the same fundamental risk: a corrupted intermediate step can push the system toward the wrong action.

---

## Background

Earlier in the course, most failures were about what the model said.

In this SP, the more important question is what the agent **chooses to do next**.

The lab simulates an agent that:

1. summarizes a report
2. chooses the next action based on that intermediate result

The clean report should lead to a client-update workflow. The poisoned report tries to redirect the agent into an internal-security-alert workflow instead.

Your job is to add a small structural check between those two steps.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP09
```

---

## Instructions

The exercise runs in two steps.

**Step 1 — Craft your injection payload (interactive, no file edits needed)**

Run the script. It shows you the clean report and explains what a task hijacking payload looks like. Write your own injection text at the prompt — this text will be appended to the report document and fed to the agent. Observe how the agent's action choice changes between the clean and poisoned scenarios.

**Step 2 — Write the validator (requires a file edit)**

- File: `starter/agent_sp09.py`
- Function: `validate_action(plan, original_intent)`

Edit only `validate_action(plan, original_intent)` so that it catches the hijack you just crafted. Re-run the script.

You are done when:

- the clean scenario still passes
- the poisoned scenario prints `HIJACK DETECTED`

---

## What To Check

Your validator should reject plans that:

- select an action inconsistent with the original task
- contain clear signs of phishing or credential collection
- redirect the workflow into an unrelated internal-alert path

---

## Security Note

This is still a narrow teaching control. A real agentic defense would also constrain action schemas, preserve original intent explicitly across steps, and avoid trusting model-generated intermediate plans without verification.

---

## Deliverable

`agent_sp09_results.json` — auto-saved. The poisoned scenario should end with `"valid": false`.

---

## Discussion Questions

1. Why is this more dangerous than a simple bad chat response?
2. What changed: the user's request, the intermediate state, or the selected action?
3. What architectural control would you add beyond a validator?
