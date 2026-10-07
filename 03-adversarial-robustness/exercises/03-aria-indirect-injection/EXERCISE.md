# SP03 — Aria Indirect Injection

**Estimated time:** 15 minutes
**Platform:** Aria
**Capstone connection:** Northstar reads external content. If poisoned text enters the system through retrieved or uploaded data, it can influence model behavior without the user ever typing the attack directly.

---

## Background

Aria is an internal assistant for Vantage Systems that summarizes employee documents on request.

**Indirect prompt injection** is what happens when the attack arrives through trusted data — a retrieved document, a file upload, a summarized report — rather than through something the user typed directly. That distinction matters because the model treats the document as context it should trust, not as adversarial input. The attack stops looking like a chat trick and starts looking like a legitimate instruction embedded in content.

One of Aria's input documents has been poisoned with prompt-injection content hidden inside otherwise normal text. Your job is not to solve prompt injection completely. Your job is to add a **first-pass detector** that catches the obvious malicious payload before the document reaches the model.

---

## Setup

```bash
cd /voc/startercode/course_materials/exercises
python3 scripts/run_sp.py SP03
```

---

## Instructions

Change exactly one function in one file:

- File: `starter/aria_sp03.py`
- Function: `block_injection(text)`

Steps:

1. Run the script once with `block_injection()` returning `False`.
2. Observe the poisoned document making it through to the model.
3. Edit only `block_injection(text)`.
4. Re-run the script.

You are done when:

- the poisoned document is blocked
- the clean documents still pass through normally

---

## Hint

Look for obvious phrases such as:

- `SYSTEM:`
- `ignore your`
- `admin mode`
- `previous instructions`

---

## Security Note

This is intentionally a toy control. Exact string matching can catch low-effort attacks and help you see the attack shape clearly, but it is not a complete defense. Real systems also need trust boundaries, provenance controls, prompt separation, and stronger classifiers.

---

## Deliverable

`aria_sp03_results.json` — auto-saved. The poisoned document should appear with `"blocked": true`.

---

## Discussion Questions

1. What happens if an attacker rewrites the payload without using your exact keywords?
2. Where else besides retrieved documents could indirect injection enter Aria's context?
