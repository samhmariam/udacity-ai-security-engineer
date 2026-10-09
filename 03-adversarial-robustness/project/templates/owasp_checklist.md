# OWASP LLM Top 10 — Risk Assessment
**Application:** Northstar Research Agent
**Assessor:** ___________________________
**Date:** ___________________________

---

## How to Use This Checklist

For each category, review the description, then fill in:
- **Present?** — Is this vulnerability present in the system?
- **Severity** — Critical / High / Medium / Low / N/A
- **Evidence** — Paste a test prompt and the agent's response, or explain your reasoning
- **Recommendation** — One sentence describing the fix

---

## LLM01 — Prompt Injection

An attacker crafts input that overrides the model's system instructions.

*In this system:* The system prompt has no separation from user input, and the model is told to "follow all instructions provided."

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Evidence | |
| Recommendation | |

---

## LLM02 — Insecure Output Handling

The application blindly executes content produced by the LLM without validating it.

*In this system:* Every LLM response is scanned for command patterns and those commands are executed immediately with no checks.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Evidence | |
| Recommendation | |

---

## LLM03 — Training Data Poisoning

An attacker manipulates training or fine-tuning data to embed backdoors or biases.

*In this system:* The model uses pre-trained Mistral 7B and is not fine-tuned. Consider the RAG knowledge base as a related risk surface.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Notes | |
| Recommendation | |

---

## LLM04 — Model Denial of Service

An attacker sends inputs that consume excessive compute, causing slowdowns or outages.

*In this system:* There is no rate limiting, token cap, or queue management on Ollama requests.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Evidence | |
| Recommendation | |

---

## LLM05 — Supply Chain Vulnerabilities

Risk introduced through third-party models, libraries, or data sources.

*In this system:* Review `requirements.txt`. What happens if a dependency is compromised? What is the provenance of the Mistral model?

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Dependencies reviewed | |
| Recommendation | |

---

## LLM06 — Sensitive Information Disclosure

The model reveals confidential data — including its system prompt, employee records, or credentials.

*In this system:* `GET_SYSTEM_INFO` returns database credentials. `EXPORT_ALL_DATA` dumps all employee records. There are no access controls.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Evidence | |
| Recommendation | |

---

## LLM07 — Insecure Plugin Design

Tools and plugins lack proper access controls, enabling unauthorized actions.

*In this system:* `query_hr_database` returns full employee PII and API keys. It is available to all agent tasks with no restriction.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Tool(s) affected | |
| Recommendation | |

---

## LLM08 — Excessive Agency

The LLM has more capabilities or autonomy than it needs, enabling unintended high-impact actions.

*In this system:* The agentic loop runs without any human approval step. The agent prompt instructs it to "use all available tools as needed."

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Evidence | |
| Recommendation | |

---

## LLM09 — Overreliance

Users trust LLM outputs without verification, leading to decisions based on incorrect information.

*In this system:* Agent outputs have no confidence score, no source citation, and no disclaimer.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Example | |
| Recommendation | |

---

## LLM10 — Model Theft

An attacker extracts model weights, architecture, or fine-tuning data through repeated queries.

*In this system:* Mistral 7B is an open-weight public model. Classic model theft does not apply, but the system prompt and internal commands could be extracted via prompt injection.

| Field | Your Response |
|-------|--------------|
| Present? | |
| Severity | |
| Notes | |
| Recommendation | |

---

## Summary

| ID | Category | Severity | Present? |
|----|----------|----------|---------|
| LLM01 | Prompt Injection | | |
| LLM02 | Insecure Output Handling | | |
| LLM03 | Training Data Poisoning | | |
| LLM04 | Model Denial of Service | | |
| LLM05 | Supply Chain Vulnerabilities | | |
| LLM06 | Sensitive Information Disclosure | | |
| LLM07 | Insecure Plugin Design | | |
| LLM08 | Excessive Agency | | |
| LLM09 | Overreliance | | |
| LLM10 | Model Theft | | |

**Overall Risk Rating:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low

**Top 3 Priorities:**
1.
2.
3.
