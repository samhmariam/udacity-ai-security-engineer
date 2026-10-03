# Northstar Assist: Build and Secure an AWS Bedrock RAG AI Agent

Capstone project for the course **AI Threat Modeling and Operational Defense**.

Northstar Assist is an internal employee assistant. It answers questions about Northstar Technologies' policies and internal documents using Retrieval-Augmented Generation (RAG) on **Amazon Bedrock AgentCore**:

```
Employee ─▶ Streamlit app ─▶ AgentCore harness ─▶ Claude Haiku 4.5 (global inference profile)
                                   │   ▲
                                   ▼   │ retrieved chunks
                           AgentCore gateway ─▶ Managed Knowledge Base (Titan Text Embeddings V2) ◀─ S3 (30 documents)
```

This folder contains the deliverables for each project task, the scripts used to apply and verify the controls in the live AWS account, and the original starter files.

---

## Deliverables

| Task | Deliverable | What it covers |
|---|---|---|
| Build the agent and harness | [evidence/Build Evidence.md](evidence/Build%20Evidence.md) | Playground screenshot and live `InvokeHarness` transcripts showing Claude Haiku 4.5 answering from retrieved knowledge base content. The knowledge base sync job (30/30 documents indexed, 0 failed). |
| AI asset inventory | [Northstar Assist ML-BOM.md](Northstar%20Assist%20ML-BOM.md) | Both models (Claude Haiku 4.5, Titan Text Embeddings V2), with what is and isn't known about their training data. The knowledge source, S3, the vector store, the gateway, the harness and the three IAM roles, all read from the deployed account. Findings F-01 to F-09. |
| Threat model | [Northstar Assist STRIDE-ML Threat Model.md](Northstar%20Assist%20STRIDE-ML%20Threat%20Model.md) | Data assets, 8 trust boundaries along the request and retrieval path, and 16 threats across all STRIDE categories, scored and ranked (direct and indirect injection, data exposure, misuse). Mitigations, residual risks and recommendations. |
| Least-privilege access | [iam-least-privilege/Northstar Assist IAM Least-Privilege Changes.md](iam-least-privilege/Northstar%20Assist%20IAM%20Least-Privilege%20Changes.md) | Before and after comparison of the harness and gateway roles, with the reason for each change and an attacker's-eye view. A 31-case policy evaluation (all pass), and a mandatory-guardrail IAM Deny. |
| Safety and response controls | [guardrail/Northstar Assist Safety Controls.md](guardrail/Northstar%20Assist%20Safety%20Controls.md) | Bedrock Guardrail `northstar-assist-guardrail` attached to the harness: input and output controls, thresholds and their reasoning, and known limitations. 39/39 core tests pass, plus live harness tests. |
| Monitoring and incident response | [monitoring/Northstar Assist Monitoring and IR Playbook.md](monitoring/Northstar%20Assist%20Monitoring%20and%20IR%20Playbook.md) | Log sources checked against the live account, baselines, and 11 alarms on AI-specific signals (guardrail interventions, retrieval anomalies, token anomalies, guardrail bypass). Playbook PB-01 for prompt injection, dry-run tested against a simulated attack. |
| Launch readiness | [launch-readiness/Northstar Assist Launch-Readiness Report.md](launch-readiness/Northstar%20Assist%20Launch-Readiness%20Report.md) | 14 edge-case prompts × 3 runs against the hardened harness, the threat status after hardening, and the recommendation. |

**Recommendation: approve with conditions.** The controls stopped direct injection, misuse and exfiltration in every deterministic test. However, two edge cases disclosed confidential data (sales deal data and infrastructure identifiers) in every run, because that data is still in the knowledge base. Launch is gated on four conditions:
1. Remove sensitive datasets from the knowledge base.
2. Put single sign-on in front of the app, with per-user logging.
3. Restrict who can write to the S3 source bucket.
4. Route alerts to an on-call team.

See section 5 of the launch-readiness report.

---

## What Was Changed in AWS

All changes are in account `911470903119`, `us-east-1`, and every one can be rolled back as described in its deliverable.

| Change | Rollback |
|---|---|
| Harness execution policy v2 (scoped) → v3 (adds the guardrail grant), plus the inline Deny `NorthstarRequireGuardrail` | IAM report, section 8 |
| Gateway KB-access and base policies v2, and narrowed trust policies on both roles | IAM report, section 8 |
| Guardrail `bzgydako86r9` (version 1) attached to the harness, creating harness version 2 | Safety controls report, section 8 |
| Metric filters, Contributor Insights rule, 11 alarms, SNS topic `northstar-assist-security-alerts`, dashboard `NorthstarAssist-Security`, and 11 saved queries | Delete the `northstar-assist-*` resources (all created by `monitoring/deploy_monitoring.py`) |

---

## Repository Layout

| Path | Contents |
|---|---|
| `evidence/` | Build evidence: harness, retrieval and knowledge base sync outputs, and `capture_build_evidence.py` to re-capture them |
| `Northstar Assist ML-BOM.md`, `Northstar Assist STRIDE-ML Threat Model.md` | Inventory and threat model deliverables |
| `ML-BOM Template.md`, `STRIDE-ML Template.md` | The course templates, converted from `.docx` |
| `iam-least-privilege/` | IAM report, original (`before/`) and applied (`after/`) policy documents, and policy evaluation results |
| `guardrail/` | Safety controls report, guardrail configuration (`northstar-guardrail-config.json`), and scripts to deploy, attach and test it, with their results |
| `monitoring/` | Monitoring plan and playbook, `deploy_monitoring.py`, metric filter patterns, saved queries, the attack simulation, the kill-switch test and the playbook dry run, with their results |
| `launch-readiness/` | Launch-readiness report, the edge-case test runner and its results, and the script that builds the report tables |
| `northstar-knowledge-base/` | The 30 Northstar company documents (CSV, DOCX, HTML, PDF, TXT, XLSX) uploaded to S3 and indexed by the managed knowledge base. `docx/` also holds Markdown copies of the five Word files, which aren't uploaded to S3. |
| `streamlit_app/` | Optional reference web app that calls the harness with `InvokeHarness` (see [streamlit_app/README.md](streamlit_app/README.md)) |
| `images/` | Screenshot of the harness playground |

---

## Re-running the Tests

The scripts read AWS credentials and `HARNESS_ARN` from the `.env` file at the repository root. That file is git-ignored; never commit it. They need Python 3.10+, and they install their own dependencies when run with [`uv`](https://docs.astral.sh/uv/), for example:

```bash
uv run --no-project --with boto3 --with python-dotenv python guardrail/test_guardrail.py bzgydako86r9 1   # guardrail controls (39 core cases)
uv run --no-project --with boto3 --with python-dotenv python guardrail/test_harness_e2e.py                # live harness checks, including the override bypass
uv run --no-project --with boto3 --with python-dotenv python monitoring/simulate_prompt_attack.py         # triggers and watches the per-session alarm
uv run --no-project --with boto3 --with python-dotenv python launch-readiness/run_edge_cases.py 3         # 14 edge cases × 3 runs
```

These scripts send real requests to the harness. The attack tests deliberately trigger the security alarms.

---

## Security Notes

- **Never commit AWS credentials.** Root `.env` and `streamlit_app/.env` are git-ignored, and `streamlit_app/setup_aws.py` clears the keys from `aws-credentials.txt` after saving them outside the repository.
- Incident-response evidence exports (`**/dryrun-case/`) contain retrieved personal data and are git-ignored. Keep any new exports out of the repository.
- The knowledge base documents are fictional course data, but the reports treat them as real confidential data.

---

## Original Starter Instructions

Follow the project instructions in the classroom. Before starting, work through the course lessons and the Bedrock setup walkthrough in the course exercises (`skill-pair-00-bedrock-setup/WALKTHROUGH.md`); the project repeats the same console steps for Northstar Assist. To run the reference app, install the packages in `streamlit_app/requirements.txt` (the harness API needs boto3 1.43.52 or later), paste your Cloud Lab credentials into `streamlit_app/aws-credentials.txt`, and run `python setup_aws.py` in that folder.
