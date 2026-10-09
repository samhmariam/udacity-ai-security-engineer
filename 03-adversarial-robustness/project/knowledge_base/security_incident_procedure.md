# Security Incident Reporting Procedure

**Owner:** Security Operations Center (SOC)
**Version:** 3.1 | Last reviewed: 2025-Q4

---

## When to Report

Report any suspected security incident immediately, including:

- Unauthorized access to systems, files, or employee data
- Phishing attempts, credential theft, or social engineering
- Unexpected agent behavior (e.g., the Research Agent producing commands
  you did not request, or referencing data you did not provide)
- Anomalous data access patterns or tool misuse alerts
- Suspected prompt injection or AI system manipulation

**When in doubt, report it.** False positives are preferable to undetected incidents.

---

## How to Report

1. **Stop and preserve.** Do not attempt to remediate the incident yourself.
   Preserve all logs, screenshots, and session transcripts as evidence.

2. **Contact the SOC** at soc@northstar-tech.com

3. **Create an incident ticket** using the internal ticketing system:
   - Category: **Security Incident**
   - Priority: match to severity (see below)
   - Include: date/time, affected systems, description, your contact info

4. **If urgent or critical**, call the Security Hotline: **ext. 9-SECURITY (9-7328)**

---

## Severity Levels and SLAs

| Severity | Examples                                   | SOC Response SLA |
|----------|--------------------------------------------|------------------|
| Critical | Active breach, credential exposure         | 15 minutes       |
| High     | Unauthorized data access, agent hijacking  | 1 hour           |
| Medium   | Suspicious but unconfirmed activity        | 4 hours          |
| Low      | Policy questions, near-miss events         | 24 hours         |

---

## What to Include in Your Report

- Date and time of discovery
- Systems and data affected
- Exact description of what you observed
- Any agent inputs/outputs if AI system is involved
- Your name and contact information

All reports are handled confidentially.
