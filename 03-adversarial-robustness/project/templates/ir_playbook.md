# Incident Response Playbook
## Northstar Research Agent

**Version:** 1.0
**Owner:** Security Operations Center
**Completed by:** ___________________________
**Date:** ___________________________

---

## When to Activate This Playbook

Activate when any of the following occur:

- The agent executes a command that was not requested by the user
- Employee records or credentials appear in an agent response unexpectedly
- A user reports unusual agent behavior
- An alert fires from one of the monitoring rules below

---

## Incident Severity Levels

| Level | Criteria | Examples |
|-------|----------|---------|
| **P1 — Critical** | Active breach or confirmed credential exposure | `GET_SYSTEM_INFO` or `EXPORT_ALL_DATA` executed in production |
| **P2 — High** | Unauthorized data access | Employee PII returned to wrong user, `query_hr_database` called for non-HR task |
| **P3 — Medium** | Suspicious but unconfirmed | Repeated injection attempts with no confirmed success |
| **P4 — Low** | Near-miss or policy violation | User trying injection, agent correctly refused |

---

## First 30 Minutes

### Minutes 0–5: Confirm and Classify

- [ ] Pull the agent logs for the session in question
- [ ] Identify: which command or tool was called? What data was returned?
- [ ] Assign a severity level (P1 / P2 / P3 / P4)
- [ ] Page on-call if P1 or P2

**Log location:** *(fill in)*
**On-call contact:** *(fill in)*

---

### Minutes 5–15: Contain

If the session is still active:

```bash
# Stop the agent
sudo pkill -f northstar_agent

# If needed, block the user's access
# [fill in your access control method]
```

Preserve all logs before restarting anything.

If data was exported or credentials were exposed:
- [ ] Notify the Data Privacy team immediately
- [ ] Do not attempt to hide or undo the access — preserve evidence

---

### Minutes 15–30: Assess and Notify

Answer these questions and document the answers:

| Question | Answer |
|----------|--------|
| Which records were accessed? | |
| Were credentials exposed? | |
| Was the knowledge base modified? | |
| Is the attack ongoing? | |

Notify based on severity:
- P1/P2: CISO, Legal, HR (if employee data)
- P3: SOC team lead
- P4: Log and monitor

---

## Remediation Before Restarting

- [ ] Audit and purge malicious documents from the knowledge base:
  ```bash
  sudo python3 load_knowledge_base.py --reset
  sudo python3 load_knowledge_base.py
  ```
- [ ] Rotate any exposed credentials
- [ ] Apply hardened system prompt and guardrails
- [ ] Rerun the validation test suite before bringing the agent back online

---

## What to Log for Every Agent Interaction

These fields must be captured for every request:

| Field | Why It Matters |
|-------|---------------|
| Timestamp | Forensic timeline |
| User ID / Session ID | Attribution and correlation |
| Full user input | Evidence |
| Retrieved document IDs | Detect RAG poisoning |
| Commands executed | Alert on unauthorized actions |
| Tools called | Alert on privilege violations |
| Response time (ms) | Detect denial-of-service patterns |

---

## Alert Rules

Define at least 5 rules of your own. Use the severity criteria above to assign a
priority to each, and base your trigger conditions on the commands, tools, and
attack behavior you observed in Phase 2.

One row is filled in as a formatting example — it does not count toward your 5.

| Alert Name | Trigger Condition | Severity | First Action |
|-----------|-------------------|----------|-------------|
| *Example:* Bulk export triggered | `EXPORT_ALL_DATA` executed | P1 | Page on-call, suspend session |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

---

## Contacts

| Role | Name | Contact |
|------|------|---------|
| SOC | | soc@northstar-tech.com |
| AI Enablement | | ai-team@northstar-tech.com |
| Data Privacy | | privacy@northstar-tech.com |
| Legal | | legal@northstar-tech.com |
