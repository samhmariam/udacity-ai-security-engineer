# OpsGuide — Monitoring Plan

**Author:**
**Date:**
**System:** OpsGuide (RAG assistant on an AgentCore harness)

---

## Instructions

For each log source below, complete the two columns:

- **What to Log** — the specific fields or event types that matter for security. "All API calls" is not enough — what fields would you need to reconstruct an incident?
- **Alert Condition** — the specific threshold or pattern that triggers an alert. Include a concrete threshold (e.g., "`InvocationsIntervened` with `GuardrailContentSource=Input` and `GuardrailPolicyType=ContentPolicy` > 5 in 10 minutes") rather than "unusual activity."

---

## Monitoring Plan

| # | Log / Metric Source | What to Log | Alert Condition |
|---|---|---|---|
| 1 | **Bedrock Model Invocation Logs** | _Your answer_ | _Your answer_ |
| 2 | **Bedrock Guardrails Metrics** | _Your answer_ | _Your answer_ |
| 3 | **S3 Access Logs (KB source bucket)** | _Your answer_ | _Your answer_ |
| 4 | **CloudWatch Cost Alarms** | _Your answer_ | _Your answer_ |

---

**Which of these four sources is most unique to AI systems — it wouldn't appear in a standard web app monitoring plan?**

_Your answer here_

**What could go wrong that none of these four sources would catch?**

_Your answer here_
