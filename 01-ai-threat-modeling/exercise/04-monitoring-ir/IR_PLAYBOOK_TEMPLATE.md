# OpsGuide — Incident Response Playbook

**System:** OpsGuide (RAG assistant on an AgentCore harness)
**Owner:** _Your name / team_
**Last updated:** _Date_

---

## How to Use This Playbook

Fill in each section so that an on-call IT analyst who has never handled an AI incident could follow it at 2 AM. "Check the logs" is not actionable — name the AWS service, the console path, or the CLI command.

**General principles:**
- Export logs before taking containment actions that might clear them
- Document every action with a timestamp
- Assume the incident is worse than it looks until investigation proves otherwise

---

## Incident: Suspected Prompt Injection Attack

**Definition:** A user is sending inputs designed to override OpsGuide's system prompt, extract unauthorized information, or cause the model to ignore its Guardrails configuration.

**Severity:** High — active attack in progress

---

### Detection Signals

What would you see that tells you this incident is happening? Be specific enough that an analyst who has never seen an AI attack can recognize it.

| Signal | Where to find it | Threshold / Pattern that triggers this playbook |
|---|---|---|
| _Your answer_ | _Your answer_ | _Your answer_ |
| _Your answer_ | _Your answer_ | _Your answer_ |

---

### Immediate Containment (First 15 Minutes)

- [ ] **Step 1:**
  Action: _What you do_
  Where: _AWS console path or CLI command_

- [ ] **Step 2:**
  Action: _What you do_
  Where: _AWS console path or CLI command_

- [ ] **Step 3:**
  Action: _What you do_
  Where: _AWS console path or CLI command_

**Decision point:** If the attack is still ongoing at 15 minutes and you cannot isolate the user without taking OpsGuide offline — is a temporary outage acceptable? Who makes that call?

_Your answer here_

---

### Investigation (First Hour)

- [ ] **Retrieve the full session log** — what are you looking for, and where is it?

- [ ] **Determine if any injection attempt succeeded** — what does "success for the attacker" look like in logs?

- [ ] **Identify the scope** — was this one user or multiple? How would you check?

---

### Escalation Criteria

Escalate to on-call security lead immediately if:
- [ ] _Your criterion_
- [ ] _Your criterion_

Notify CISO within 4 hours if:
- [ ] _Your criterion_

---

### Recovery

- [ ] **Step 1:** _How you return the system to normal operation_
- [ ] **Step 2:** _Verification — what confirms the attack vector is closed?_

**How do you define "resolved" for this incident?**

_Your answer here_

---

## Post-Incident Review

Complete after every incident:

- [ ] Timeline documented (detection → containment → resolution)
- [ ] Root cause identified
- [ ] Logs exported before rotation
- [ ] Monitoring gaps noted — what would have caught this earlier?
- [ ] Guardrails or IAM changes implemented to prevent recurrence
