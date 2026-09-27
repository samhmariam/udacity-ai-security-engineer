# STRIDE-ML Threat Model — FinQuery

**Modeler(s):** _[Your name(s)]_
**Date:** _[Today's date]_

---

## System Context

FinQuery is a RAG assistant at Meridian Analytics, built on an Amazon Bedrock AgentCore harness. A query flows through this path:

```
Analyst → Streamlit app → AgentCore harness (Claude Sonnet 4.5) → AgentCore Gateway → Managed Knowledge Base (vector retrieval) → retrieved chunks back to Claude → response
```

Source documents (200+ research reports, SEC filings, investment memos) live in S3 and are synced into the Managed Knowledge Base nightly. **Current state: no active Guardrails, permissive S3 bucket policy, broad `bedrock:*` IAM role, no per-user rate limiting, no query-level audit logging.**

---

## Focus: The Three Highest-Risk STRIDE Categories for RAG Systems

Threat modeling covers six categories, but three matter most for RAG architectures:

- **Tampering** — the KB is a data store that feeds model behavior; modifying it changes what the system tells users
- **Information Disclosure** — retrieved content can be prompted out of the model; access boundaries between analysts matter
- **Elevation of Privilege** — prompt injection (direct from a query, or indirect via a poisoned document) is the most distinctive threat class in AI systems

Complete a threat for each of the three categories below.

---

## Threat 1: Tampering

_Modifying data the system relies on — S3 source documents, the vector index, or the agent's system prompt — without authorization._

| Field | Your Answer |
|---|---|
| **Threat name** | _Short descriptive name (e.g., "S3 Document Replacement via Overly Permissive Bucket Policy")_ |
| **Describe the attack** | _Who does what, using which component, to cause what change in system behavior? Be specific to FinQuery — not generic._ |
| **Which component is exploited** | _S3 bucket? Knowledge base? Gateway? Harness configuration?_ |
| **Likelihood** | _Low / Medium / High — one sentence of reasoning_ |
| **Impact** | _Low / Medium / High — one sentence of reasoning_ |
| **One mitigation** | _The single most effective control. Be specific, not generic._ |

---

## Threat 2: Information Disclosure

_Sensitive content is exposed to a party who should not have access — through prompt manipulation, or the retrieval system surfacing documents across an access boundary._

| Field | Your Answer |
|---|---|
| **Threat name** | _Short descriptive name (e.g., "Cross-Analyst Research Disclosure via Unscoped Retrieval")_ |
| **Describe the attack** | _Which asset is exposed, to whom, through what mechanism? The information barrier angle is worth considering: FinQuery retrieves documents without checking whether the requesting analyst is authorized to see that specific research._ |
| **Which component is exploited** | _Retrieval system? System prompt? Model behavior?_ |
| **Likelihood** | _Low / Medium / High — one sentence of reasoning_ |
| **Impact** | _Low / Medium / High — one sentence of reasoning_ |
| **One mitigation** | _The single most effective control_ |

---

## Threat 3: Elevation of Privilege

_An attacker gains capabilities beyond what they are authorized to have — most commonly by injecting instructions into the model's context directly (in a query) or indirectly (embedded in a document the retrieval system delivers to the model)._

| Field | Your Answer |
|---|---|
| **Threat name** | _Short descriptive name (e.g., "Indirect Prompt Injection via Poisoned Research Document")_ |
| **Describe the attack** | _Walk through the full attack chain. Who does what, in what order, and what does the model do as a result? Distinguish between direct injection (user types malicious instructions) and indirect injection (malicious instructions embedded in a KB document that gets retrieved)._ |
| **Which component is exploited** | _User input? S3 document? Which trust boundary does the attacker cross?_ |
| **Likelihood** | _Low / Medium / High — one sentence of reasoning (consider: no Guardrails, permissive S3)_ |
| **Impact** | _Low / Medium / High — one sentence of reasoning_ |
| **One mitigation** | _The single most effective control_ |

---

## Priority Ranking

Rank your three threats from highest to lowest priority and explain your reasoning in one sentence each.

| Rank | Threat Name | Why This Priority |
|---|---|---|
| 1 (highest) | | |
| 2 | | |
| 3 | | |

**If you had time to implement only one mitigation before this system goes to production, which would it be and why?**

_Your answer here_

---

_Save as `starter/STRIDE_ML_COMPLETED.md` when finished._
