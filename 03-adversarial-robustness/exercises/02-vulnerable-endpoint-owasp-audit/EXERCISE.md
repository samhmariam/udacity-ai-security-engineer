# SP02 — OWASP Audit of a Vulnerable LLM App

**Estimated time:** 15 minutes
**Platform:** vulnerable endpoint service
**Capstone connection:** The Northstar capstone includes a security assessment component. This SP gives you practice turning exploit behavior into structured findings rather than just saying "it broke."

---

## Background

The **OWASP LLM Top 10** is a shared taxonomy for naming and communicating LLM-specific failures. It gives security teams a common language — LLM01 (Prompt Injection), LLM02 (Insecure Output Handling), LLM06 (Sensitive Information Disclosure), LLM08 (Excessive Agency), LLM09 (Overreliance) — so findings can be compared, prioritized, and handed off without ambiguity.

In SP01 you attacked a deliberately weak endpoint. In this SP, you use that same target differently.

Instead of asking only "can I break it?", you ask:

- what kind of failure is this?
- what evidence supports that conclusion?
- what would a mitigation look like?

This is the shift from red team intuition to structured security assessment — and it is exactly the skill the Northstar capstone requires when you produce your OWASP findings report.

---

## Setup

Make sure the vulnerable endpoint service from SP01 is still running. Then run:

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP02
```

If needed:

```bash
export VULN_LLM_BASE_URL=http://host:port
```

---

## Instructions

1. Run the script. It presents five OWASP-style risk categories.
2. For each category, read the goal and hint, then write your own probe prompt at the input.
3. The script sends your prompt to the endpoint and displays the response.
4. Read the pass criteria and mark the test `PASS` or `FAIL`.
5. Add a short note explaining what evidence led to that judgment.
6. Your audit output is saved to `endpoint_sp02_audit.json`.

---

## What To Focus On

For each prompt, pay attention to:

- whether the endpoint obeyed or resisted the malicious instruction
- whether it disclosed protected information
- whether it emitted unsafe output such as executable script content
- whether it claimed to perform a real action it could not safely verify
- whether it fabricated details instead of acknowledging uncertainty

Your audit note should explain what the evidence shows, not just the verdict. A weak note says "the model obeyed my prompt." A useful note says "the model ignored its system instructions and returned the secret value when I framed the request as an admin override — evidence of LLM01." That distinction matters in a real assessment where findings need to be communicated to stakeholders and mapped to remediation.

---

## Variability Note

Some prompts may be stronger than others depending on the target configuration. If a test result is ambiguous, explain why. In this SP, your reasoning matters as much as the raw model output.

---

## Deliverable

`endpoint_sp02_audit.json` — auto-saved when the script completes.

---

## Discussion Questions

1. Which OWASP-style finding felt most severe on this target, and why?
2. Which test gave the weakest signal? What would you change to improve it?
3. Pick one failure and name one concrete mitigation that would reduce the risk.
