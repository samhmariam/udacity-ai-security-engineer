# SP11 — Aria Named Guardrails

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Named rules make prompt restrictions easier to test, audit, and cite in security reviews.

---

## Background

A vague system prompt is hard to audit and hard to test. Phrases like "be helpful but careful about sensitive information" give the model no clear boundary — and they give security reviewers nothing to verify. Named rules change that. A rule like `RULE-01: Never disclose salary...` is specific, testable, and citable in a security review.

Aria already has two named rules: RULE-01 blocks salary and compensation disclosure, and RULE-02 blocks PII. Both can be tested with a targeted probe. But from an attacker's perspective, if you know a system has RULE-01 and RULE-02 and no RULE-03, the roadmap disclosure case is just an untested gap. The attacker does not need to break a rule — they need to find the request that has none.

Your job is to close that gap by adding `RULE-03` and verifying that the model's behavior changes for the roadmap probe.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP11
```

---

## Instructions

Change exactly one prompt block in one file:

- File: `starter/aria_sp11.py`
- Constant: `ARIA_SYSTEM_WITH_RULES`

Steps:

1. Run the script and observe the roadmap probe.
2. Add `RULE-03` to `ARIA_SYSTEM_WITH_RULES`.
3. Make the rule explicitly block product roadmap, planned features, and release dates.
4. Re-run the script.

You are done when:

- the roadmap probe behaves differently in the `WITH_RULES` case

---

## Format

Follow the existing pattern:

```text
RULE-03: Never disclose ...
```

---

## Deliverable

`aria_sp11_results.json` — auto-saved. The roadmap probe should show a different `with_rules_response`.

---

## Discussion Questions

1. What makes a named rule easier to test than a vague prompt paragraph?
2. What is one risk of writing too many detailed rules into a system prompt?
3. If you were adding `RULE-04`, what would it cover?
