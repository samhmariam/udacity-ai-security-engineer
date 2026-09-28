# Guardrail PII Configuration — MyHealth Assistant

**Exercise:** Lesson 12 — Privacy-Preserving Design (`skill-pair-09-differential-privacy` folder)
**Your Name:** ___________________________________
**Date:** ___________________________________

---

## Background

Amazon Bedrock Guardrails can detect PII types in user input and in model output, and take one of three actions:

- **BLOCK** — The request or response is blocked entirely if this PII type is detected. The user receives the guardrail's configured blocked message instead.
- **ANONYMIZE** (shown as **Mask** in the console) — The PII value is replaced with a type placeholder such as `{EMAIL}`, `{PHONE}`, or `{NAME}`. The response is still delivered, but the sensitive value is redacted. On a streaming assistant, fragments of the original value can appear next to the placeholder, even when the invocation log records the entity as `ANONYMIZED`. When a value must never reach a patient, use BLOCK, or keep the data out of the knowledge base.
- **ALLOW** — No action is taken. This PII type may appear in model outputs.

The console also offers **Detect**, which is `NONE` in the API. It records a match without changing the text.

When selecting an action, consider:

1. **Is this PII type likely to appear in the MyHealth Assistant knowledge base?** (Based on your classification decisions in Task 1)
2. **Is a patient likely to type it into a question?** The guardrail checks the patient's input as well as the model's output.
3. **What is the harm if it appears in a response?**
4. **Would BLOCK break legitimate use cases?** (If the model can't answer without mentioning a clinic address, does blocking help or just frustrate patients?)
5. **Does data minimization reduce the need for this guardrail?** (If you removed `phone_extension` before upload, a phone guardrail is still useful — but it's defense in depth, not a primary control)

---

## Task 3: PII Guardrail Configuration Table

Complete the table for all 10 PII types.

| PII Type | Action (BLOCK / ANONYMIZE / ALLOW) | Justification | Notes for Westfield Health Use Case |
|---|---|---|---|
| Social Security number (SSN) | | | |
| Credit/debit card number | | | |
| Bank account number | | | |
| AWS access key | | | |
| AWS secret key | | | |
| Password | | | |
| Email | | | |
| Phone | | | |
| Name | | | |
| Address | | | |

---

### Guidance Notes

**SSN, credit/debit card number, bank account number, and password:** None of these should appear in any document you include in the knowledge base. Patients may still type them into a question, for example a card number when asking about a bill, or a portal password when asking for login help. Does that make the guardrail unnecessary — or is it still worth configuring?

**AWS access key and AWS secret key:** A key in a response would mean a key was embedded in a knowledge base document. What should happen to the response, and to the key?

**Email and Phone:** You made a column removal decision in Task 2. How does that decision affect your guardrail choice here? Also look at the patient guides: they list department phone numbers such as Central Scheduling. What happens to those numbers under each action?

**Name:** This is a nuanced one. Patients often include their own name in a question ("My name is Pat, and I need to move my appointment"). Staff names appear in `staff_directory.csv`. The demo showed that anonymizing names on an assistant that calls tools can stop the request before the tool runs, so the patient gets no answer. Think about what you are actually trying to protect.

**Address:** The patient guides list clinic addresses, which patients need to find their appointment. A patient may also type a home address into a question. How do you weigh those two cases?

**Health information and salary data:** Neither is on this PII type list. `discharge_followup_call_log.csv` holds health information, and `staff_directory.csv` holds `salary_band`. Which of your other decisions protects that data?

---

## Task 4: Written Response

**Question:** Why is "anonymize the PII in the model's output" not as strong a privacy control as "don't put PII in the knowledge base in the first place"?

Write 3-5 sentences. Address at least two of the following:
- What data minimization prevents that output filtering cannot
- What happens if a guardrail is misconfigured or bypassed
- The relationship between query volume and privacy risk
- How these two controls relate to the concept of defense in depth

---

**Your Answer:**

> _Your response here_

---

_This completes the Lesson 12 exercise. Both worksheets (DATA_CLASSIFICATION_WORKSHEET.md and this file) are your deliverables._
