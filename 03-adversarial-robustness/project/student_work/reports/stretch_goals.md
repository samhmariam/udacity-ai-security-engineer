# Suggestions to Make This Project Stand Out

Reference list of optional enhancements beyond the graded requirements. Recorded
for future work; not required for submission.

---

## 1. Implement chain-of-thought logging
Add structured logging to the hardened agent that captures every tool call with
input hashes, output summaries, timestamps, and session IDs. This goes beyond the
written monitoring plan and demonstrates production-ready observability.

> Status in this project: partially started — `rag_guard.log` already records
> `EXCLUDED` / `COMMAND-BLOCKED` / `TOOL-DENIED` events with timestamps. The full
> per-request structured JSON log (request_id, user_id, session_id, input hash,
> output summary, tools_called) is specified in `ir_playbook.md` but not yet
> implemented in code. This item would implement that spec.

## 2. Build a human-in-the-loop approval gate
Add a confirmation step for high-risk commands (e.g., data exports or HR database
queries) that pauses execution and requires explicit user approval before
proceeding. This demonstrates risk-proportional access control.

## 3. Add a multimodal injection test
If LLaVA or another vision model is available, craft an image with embedded hidden
text and test whether the agent processes the hidden instruction. Document the
attack and propose a detection control using OCR preprocessing.

## 4. Create an automated regression test suite
Write a Python script that runs all 8 validation test cases automatically and
outputs a pass/fail summary. This makes it easy to verify defenses after any code
change.

> Status in this project: already done — `student_work/defenses/test_step10_validation.py`
> runs all 8 cases and prints a `RESULT: N/8 passed` summary with per-case
> PASS/FAIL. The separate attack harnesses (`direct_injection_test.py`,
> `rag_poisoning_test.py`, `task_hijack_test.py`) and the per-step defense tests
> could be unified into one regression runner as a further step.

## 5. Personalize the scenario
Adapt the project to a domain you care about (healthcare, finance, education,
etc.). Rewrite the knowledge base documents to reflect your chosen domain and
document how the same attack patterns apply in your context.

---

### Quick self-assessment of where this project already stands

| Suggestion | Status |
|-----------|--------|
| 1. Chain-of-thought logging | Partial (guard-event logging done; full structured log specced in IR playbook) |
| 2. Human-in-the-loop approval gate | Not started |
| 3. Multimodal injection test | Not started (no vision model in this setup) |
| 4. Automated regression suite | Done (`test_step10_validation.py`) |
| 5. Personalize the scenario | Not started (kept the Northstar scenario) |
