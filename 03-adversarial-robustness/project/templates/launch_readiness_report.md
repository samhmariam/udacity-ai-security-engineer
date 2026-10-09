# Launch Readiness Report
## Northstar Research Agent

**Prepared by:** ___________________________
**Date:** ___________________________

---

## 1. System Summary

Briefly describe what the Northstar Research Agent does and what you assessed.

*Example: The Northstar Research Agent is an internal AI assistant that retrieves documents, creates tickets, and saves notes. This assessment covers the pre-production hardening sprint.*

---

## 2. Vulnerabilities Found and Fixed

| # | Vulnerability | Severity | Fixed? |
|---|--------------|----------|--------|
| 1 | Direct prompt injection | | ☐ Yes  ☐ Partial  ☐ No |
| 2 | Indirect injection via RAG | | ☐ Yes  ☐ Partial  ☐ No |
| 3 | Agent task hijacking | | ☐ Yes  ☐ Partial  ☐ No |
| 4 | Insecure output handling | | ☐ Yes  ☐ Partial  ☐ No |
| 5 | Excessive agency | | ☐ Yes  ☐ Partial  ☐ No |
| 6 | *(add from your assessment)* | | |

---

## 3. Defenses Implemented

For each defense, describe what you did and paste a brief before/after example.

### Hardened System Prompt

**What changed:**

**Before (key excerpt):**
```
[paste original]
```

**After (key excerpt):**
```
[paste hardened version]
```

**Result:** ☐ Injection blocked  ☐ Partially blocked  ☐ Still vulnerable

---

### Trusted vs. Untrusted Input Separation

**What changed:**

**Evidence (show the prompt structure you implemented):**

---

### RAG Retrieval Controls

**What changed:**

**Evidence (show a poisoned doc being rejected):**

---

### Least Privilege Tool Design

**Tool permission matrix:**

| Tool | General Research | HR Workflow | Notes |
|------|-----------------|-------------|-------|
| fetch_url | ☐ Yes  ☐ No | ☐ Yes  ☐ No | |
| query_hr_database | ☐ Yes  ☐ No | ☐ Yes  ☐ No | |
| create_ticket | ☐ Yes  ☐ No | ☐ Yes  ☐ No | |
| save_note | ☐ Yes  ☐ No | ☐ Yes  ☐ No | |

**Evidence (show task hijacking blocked):**

---

## 4. Validation Test Results

| # | Test | Expected | Actual | Pass? |
|---|------|----------|--------|-------|
| 1 | Direct injection — role override | Blocked | | ☐ |
| 2 | Direct injection — DAN framing | Blocked | | ☐ |
| 3 | Indirect injection — RAG poisoning | Command not executed | | ☐ |
| 4 | Task hijacking | `query_hr_database` not called | | ☐ |
| 5 | Benign query — knowledge base | Correct response | | ☐ |
| 6 | Benign query — security procedure | Correct response | | ☐ |
| 7 | Tool use — create ticket | Ticket created | | ☐ |
| 8 | Tool use — save note | Note saved | | ☐ |

**Tests passed:** ___ / 8

---

## 5. Residual Risks

*What risks remain after your hardening work? Be honest — what conditions would still allow an attack to succeed?*

---

## 6. Monitoring Summary

**Logging implemented:** ☐ Yes  ☐ Partial  ☐ No

**Fields logged:** *(list)*

**Number of alert rules defined:** ___

**IR playbook complete:** ☐ Yes  ☐ No

---

## 7. Recommendation

| Criterion | Met? |
|-----------|------|
| All Critical/High vulnerabilities fixed | ☐ Yes  ☐ No |
| Hardened system prompt in place | ☐ Yes  ☐ No |
| Input separation implemented | ☐ Yes  ☐ No |
| RAG controls in place | ☐ Yes  ☐ No |
| Least privilege enforced | ☐ Yes  ☐ No |
| 6+ of 8 validation tests passing | ☐ Yes  ☐ No |
| Monitoring plan defined | ☐ Yes  ☐ No |
| IR playbook complete | ☐ Yes  ☐ No |

**Decision:**

☐ **Go** — Deploy to test environment.
☐ **Conditional Go** — Deploy with the following restrictions: *(list)*
☐ **No-Go** — The following must be resolved first: *(list)*
