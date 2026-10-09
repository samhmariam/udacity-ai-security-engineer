# Incident Response Playbook
## Northstar Research Agent

**Version:** 1.0
**Owner:** Security Operations Center
**Completed by:** Samuel H.Mariam
**Date:** 2026-10-09

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

> Worked scenario (P1): **`EXPORT_ALL_DATA` fires in production** — the bulk
> employee-record export command executed and records (including `internal_api_key`
> values) were returned in a response. This is the concrete procedure for that case;
> the same flow applies to `GET_SYSTEM_INFO` (credential exposure).

### Minutes 0–5: Confirm and Classify

- [ ] Pull the agent logs for the session in question (see **Log location** below).
- [ ] Confirm the trigger: search the structured request log for
      `commands_executed` containing `EXPORT_ALL_DATA`, and cross-check the
      guard log for a `COMMAND-BLOCKED EXPORT_ALL_DATA` line.
      - If **BLOCKED** appears and no records were returned → the hardened guard
        caught it: this is a **P4 near-miss**, not a breach. Log and monitor.
      - If records were actually returned in the response → confirmed **P1**.
- [ ] Capture: session ID, user ID, timestamp, exact user input, retrieved doc IDs,
      and the full response payload (what data left the system).
- [ ] Assign severity. A real export of records = **P1**.
- [ ] **Page on-call immediately** (P1). Start an incident timeline document now.

**Log location:** structured request log (production: Axiom stream
`northstar-agent`); local/lab guard log: `student_work/reports/rag_guard.log`.
**On-call contact:** SOC on-call via soc@northstar-tech.com / Security Hotline
ext. 9-SECURITY (9-7328).

### Minutes 5–15: Contain

If the session is still active:

```bash
# Stop the agent (halts any in-flight export/agentic loop)
sudo pkill -f northstar_agent

# Block the originating user/session at the gateway
# [access control: disable the Better-Auth session + org membership for the user ID;
#  add the session token to the gateway denylist]
```

Preserve all logs before restarting anything. Snapshot `rag_guard.log`, the
structured request log for the window, and the ChromaDB `chroma_data/` directory
(in case the knowledge base was poisoned to cause this).

Because this is a confirmed data export / credential exposure:
- [ ] Notify the Data Privacy team immediately (privacy@northstar-tech.com).
- [ ] Do **not** attempt to hide or undo the access — preserve evidence.
- [ ] Begin credential rotation prep for every secret in scope:
      all `internal_api_key` values for exported employees, and — if
      `GET_SYSTEM_INFO` also fired — the production DB password and admin token.

### Minutes 15–30: Assess and Notify

Answer these questions and document the answers:

| Question | Answer |
|----------|--------|
| Which records were accessed? | *(enumerate from the response payload: employee IDs/emails)* |
| Were credentials exposed? | *(API keys always; DB password/admin token if GET_SYSTEM_INFO also ran)* |
| Was the knowledge base modified? | *(diff `chroma_data` doc set vs. approved baseline; check guard log for prior `EXCLUDED` entries from the same session — indicates an injection source)* |
| Is the attack ongoing? | *(any further sessions from the same user/IP? other sessions emitting protected commands?)* |
| How was it triggered? | *(direct injection in user input, or indirect via a poisoned retrieved doc?)* |

Notify based on severity:
- **P1/P2:** CISO, Legal, HR (employee data was exposed → HR + Data Privacy are mandatory here).
- **P3:** SOC team lead.
- **P4:** Log and monitor.

---

## Remediation Before Restarting

- [ ] Audit and purge malicious documents from the knowledge base:
  ```bash
  sudo python3 load_knowledge_base.py --reset
  sudo python3 load_knowledge_base.py
  ```
- [ ] Rotate any exposed credentials (employee API keys; DB password + admin token
      if system info was exposed). Do not reuse old values.
- [ ] Confirm the hardened agent is the deployed build (`northstar_agent_hardened.py`):
      hardened prompt, trusted/untrusted separation, RAG content scan, and the
      command/tool allowlists are all active.
- [ ] Rerun the validation suite and require 8/8 before going back online:
  ```bash
  python student_work/defenses/test_step10_validation.py
  ```
- [ ] File a post-incident review within 48 hours; add any new injection phrasing
      observed to `INJECTION_PATTERNS` and add a regression test for it.

---

## What to Log for Every Agent Interaction

These fields must be captured for every request, as structured JSON (one record
per request). Per the AI Usage Policy, queries and responses are logged for
security review — this is that log.

| Field | Why It Matters |
|-------|---------------|
| `timestamp` (ISO 8601, UTC) | Forensic timeline |
| `request_id` | Correlate request → tool calls → response across systems |
| `user_id` | Attribution (who) |
| `session_id` | Group multi-turn activity; detect trust-building escalation |
| `env` | Separate prod vs. staging alerts |
| `source_ip` | Rate/abuse correlation |
| `user_input` (full) | Evidence of the attack prompt |
| `rag_enabled` (bool) | Context for whether RAG path was in play |
| `retrieved_document_ids` + distances | Detect RAG poisoning / anomalous retrieval |
| `guard_events` (`EXCLUDED` / `COMMAND-BLOCKED` / `TOOL-DENIED` + reason) | Detections fired by the hardened controls |
| `commands_executed` | Alert on unauthorized actions (should be empty or `CREATE_TICKET` only) |
| `tools_called` | Alert on privilege violations (e.g. `query_hr_database`) |
| `response` (or hash + size if large) | What left the system |
| `response_time_ms` | Detect denial-of-service / abuse patterns |

**Logging safety:** logs must not themselves leak secrets. Redact `internal_api_key`,
DB passwords, and tokens in stored log payloads (store a hash + the fact that a
secret-shaped value appeared, not the value). No raw customer PII beyond the
identifiers needed for attribution.

---

## Alert Rules

Severities use the criteria above. Trigger conditions reference the structured
log fields and the hardened agent's guard events.

| Alert Name | Trigger Condition | Severity | First Action |
|-----------|-------------------|----------|-------------|
| *Example:* Bulk export triggered | `EXPORT_ALL_DATA` executed | P1 | Page on-call, suspend session |
| **Sensitive command executed** | `commands_executed` contains `EXPORT_ALL_DATA` or `GET_SYSTEM_INFO` **and** the result is not a `BLOCKED` refusal (i.e. data was actually returned), in `env=production` | **P1** | Page on-call; run First-30 P1 flow; begin credential rotation |
| **HR tool invoked** | `tools_called` contains `query_hr_database` **and** it executed (no `TOOL-DENIED`) | **P2** | Page on-call; identify user; confirm whether PII left the system |
| **Guard blocked a protected command** | guard event `COMMAND-BLOCKED` (`EXPORT_ALL_DATA`/`GET_SYSTEM_INFO`/`SEARCH_EMPLOYEE`) **or** `TOOL-DENIED query_hr_database` | **P3** | A defense worked, but someone/something tried it — investigate source (direct vs. RAG); correlate by user/session |
| **RAG poisoning detected** | one or more `EXCLUDED ... injection patterns=[...]` guard events, especially the same poisoned doc ID across multiple sessions | **P3** (single) / **P2** (recurring or same doc to multiple users) | Pull and quarantine the flagged document; audit how it entered the knowledge base; diff vs. approved baseline |
| **Repeated injection attempts (campaign)** | ≥ 5 requests from one `user_id`/`session_id`/`source_ip` within 10 min each raising a guard event (`COMMAND-BLOCKED`/`TOOL-DENIED`/`EXCLUDED`) | **P3** | Rate-limit/suspend the source; preserve the sequence; review for any success among the attempts |
| **System-prompt extraction attempt** | `user_input` matches patterns like "ignore (all )?previous instructions", "reveal your system prompt", "you are DAN", "diagnostic/admin mode" | **P4** | Confirm the agent refused; log; add phrasing to pattern lists if novel |
| **Possible model DoS** | `response_time_ms` above threshold (e.g. > 120000) repeatedly, or a single user driving many concurrent long requests | **P3** | Check Ollama load; apply per-user rate limit; investigate oversized/looping inputs |

(Seven rules defined beyond the example; the first two are P1/P2 and the rest
cover detection-of-attempts and abuse.)

---

## Contacts

| Role | Name | Contact |
|------|------|---------|
| SOC | SOC On-Call | soc@northstar-tech.com / ext. 9-SECURITY (9-7328) |
| AI Enablement | AI Enablement Team | ai-team@northstar-tech.com |
| Data Privacy | Data Privacy Team | privacy@northstar-tech.com |
| Legal | Legal | legal@northstar-tech.com |
