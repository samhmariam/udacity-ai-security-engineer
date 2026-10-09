# Security Findings Report
**Application:** Northstar Research Agent
**Assessor:** ___________________________
**Date:** ___________________________

---

## Executive Summary

*Briefly describe the overall security posture — how many vulnerabilities were found, which are most critical, and whether the system is safe to deploy as-is.*

---

## Finding 1 — Direct Prompt Injection

**Severity:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low

**What happened:**
*Describe the vulnerability in 2–3 sentences.*

**Attack prompt:**
```
[paste your exact prompt here]
```

**Agent response:**
```
[paste the response, including any commands executed]
```

**Impact:**
*What can an attacker do with this? What data or actions are at risk?*

**Recommendation:**
*One to two sentences on what would fix this.*

---

## Finding 2 — Indirect Prompt Injection (RAG Poisoning)

**Severity:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low

**What happened:**
*Describe how a poisoned document caused the agent to execute an unauthorized command.*

**Trigger query used:**
```
[paste the query that retrieved the malicious document]
```

**Document retrieved:**
```
[document ID and the relevant excerpt]
```

**Agent response / commands executed:**
```
[paste result]
```

**Impact:**
*What can an attacker who controls knowledge base content achieve?*

**Recommendation:**
*How should retrieved content be handled differently?*

---

## Finding 3 — Agent Task Hijacking

**Severity:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low

**What happened:**
*Describe how the agent was tricked into calling an unauthorized tool.*

**Task prompt used:**
```
[paste the task prompt]
```

**Tools called:**
- Expected: fetch_url, save_note
- Actual: [list all tools that ran]

**Unauthorized tool output:**
```
[paste the data that should not have been returned]
```

**Impact:**
*What unauthorized action did the agent take?*

**Recommendation:**
*What tool permission change would prevent this?*

---

## Additional Findings

*Use this section for any other vulnerabilities identified during the OWASP assessment.*

**Finding 4 — [Title]**
- **Category:** [OWASP ID]
- **Severity:**
- **Description:**
- **Evidence:**
- **Recommendation:**

---

## Vulnerability Summary

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | Direct Prompt Injection | | Open |
| 2 | Indirect Prompt Injection | | Open |
| 3 | Agent Task Hijacking | | Open |
| 4 | | | |

**Overall Risk Rating:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low

**Recommendation:** ☐ Do not deploy  ☐ Deploy with mitigations  ☐ Deploy as-is
