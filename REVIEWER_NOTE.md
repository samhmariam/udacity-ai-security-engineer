# Note to the Reviewer: Northstar Assist Capstone

Thank you for reviewing my project. This repository holds my work for the whole nanodegree. **The capstone for _AI Threat Modeling and Operational Defense_ (Northstar Assist: Build and Secure an AWS Bedrock RAG AI Agent) is entirely in [`01-ai-threat-modeling/project/`](01-ai-threat-modeling/project/).** Its [README](01-ai-threat-modeling/project/README.md) gives an overview, and the table below maps each rubric criterion to the evidence for it.

Every deliverable is based on the **live deployment** in my Cloud Lab account (`911470903119`, `us-east-1`): the configuration was read through the AWS APIs, the controls were applied there, and every test ran against the real harness. Nothing is hypothetical.

---

## Where to find each rubric item

### Build the Agent and Harness

| Criterion | Evidence |
|---|---|
| Harness accepts a prompt and returns a foundation-model response | [Build Evidence §0](01-ai-threat-modeling/project/evidence/Build%20Evidence.md): a live end-to-end capture with Claude Haiku 4.5. Also the [playground screenshot](01-ai-threat-modeling/project/images/agentcore_harness.png) (§1). |
| Agent retrieves from the knowledge source and uses it in the answer | [Build Evidence §0](01-ai-threat-modeling/project/evidence/Build%20Evidence.md): the `northstar-kb___Retrieve` call, 5 retrieved chunks with sources and scores, and an answer quoting the top chunk and citing `company_policies_handbook.html` |
| Knowledge base sync completes without errors | [Build Evidence §0 and §4](01-ai-threat-modeling/project/evidence/Build%20Evidence.md): ingestion job `ZPFE9LWPAN` is COMPLETE, with 30 scanned, 30 indexed and **0 failed** |
| ML-BOM covers the foundation model, embedding model, knowledge source, storage, retrieval services and IAM roles | [ML-BOM](01-ai-threat-modeling/project/Northstar%20Assist%20ML-BOM.md): Model 1 (Haiku 4.5), Model 2 (Titan V2), and S1–S6 (documents, S3, managed KB and vector store, gateway, harness, 3 IAM roles) |
| Each entry has type, provider, intended use and limitations or transparency gaps | [ML-BOM](01-ai-threat-modeling/project/Northstar%20Assist%20ML-BOM.md): the model sections, plus explicit rows in S1–S6. Undisclosed training data is recorded as findings F-01 and F-02. |
| System overview | [ML-BOM, System Overview](01-ai-threat-modeling/project/Northstar%20Assist%20ML-BOM.md#system-overview): diagram, step-by-step flow, and each component's distinct failure mode |

### Secure the Agent and Harness

| Criterion | Evidence |
|---|---|
| Assets and trust boundaries along the request path | [STRIDE-ML threat model §1–§2](01-ai-threat-modeling/project/Northstar%20Assist%20STRIDE-ML%20Threat%20Model.md): 8 trust boundaries (TB-1 to TB-8) and 10 data assets |
| At least 3 prioritized risks: prompt injection, indirect injection, data exposure | [Threat model §3](01-ai-threat-modeling/project/Northstar%20Assist%20STRIDE-ML%20Threat%20Model.md): E-01, T-01 and I-01, plus 13 more threats, ranked in the §3.7 risk register |
| Likelihood, impact and mitigation per risk | Each threat in §3 has an L × I table with reasons, and a mitigation |
| At least two types of safety control, each with its effect and the threat it mitigates | [Safety Controls §2–§4](01-ai-threat-modeling/project/guardrail/Northstar%20Assist%20Safety%20Controls.md): prompt attack detection, content filters, denied topics, PII and secret filters, regex, URL masking, grounding, IAM enforcement |
| Handles both untrusted input and untrusted output | Safety Controls §2 (input) and §3 (output). 39/39 control tests pass, and the guardrail is verified on live traffic (§5). |
| Original vs scoped permissions of the agent execution role | [IAM changes §2–§3](01-ai-threat-modeling/project/iam-least-privilege/Northstar%20Assist%20IAM%20Least-Privilege%20Changes.md): statement-by-statement comparison, with the policy documents in `before/` and `after/` |
| Scoped to only the required models, knowledge sources and services | IAM changes §4 (attacker's view) and §5 (31/31 policy evaluation cases, plus live tests) |
| No wildcards unless justified | [IAM changes §5.3](01-ai-threat-modeling/project/iam-least-privilege/Northstar%20Assist%20IAM%20Least-Privilege%20Changes.md): **no wildcard actions**, and each of the 14 remaining wildcard resources is listed with its justification |

### Operate and Validate the Agent

| Criterion | Evidence |
|---|---|
| Logs and metrics, with AI-specific signals | [Monitoring Plan §A1–§A4](01-ai-threat-modeling/project/monitoring/Northstar%20Assist%20Monitoring%20Plan.md): guardrail intervention counts, zero-chunk and no-retrieval answers, token anomalies, guardrail bypass |
| A concrete alert with a threshold | Monitoring Plan §A4.1, AL-1: **more than 5 PROMPT_ATTACK blocks in 1 hour from a single session**. Deployed, and it fired in a live simulation (§A8). |
| Incident response playbook with containment and investigation | [IR Playbook PB-01](01-ai-threat-modeling/project/monitoring/Northstar%20Assist%20IR%20Playbook%20PB-01.md): triage (B3), containment C1–C6 (B4), investigation (B6), escalation and recovery. Dry-run tested (B10). |
| At least 3 edge-case prompts across risk categories | [Launch-Readiness Report §3](01-ai-threat-modeling/project/launch-readiness/Northstar%20Assist%20Launch-Readiness%20Report.md): 14 prompts in 4 categories, **each run 3 times** |
| Observed behaviour, guardrail intervention and appropriateness per prompt | Report §3.2: the exact prompt, the guardrail policy from the logs, the response and a verdict for each case. Inconsistency across runs is recorded as finding F-A (§3.3). |
| Final recommendation with rationale | Report §5: **Approve with conditions**, with reasons, four launch-gating conditions and the accepted residual risks |

---

## Things that may help when reading

- **The recommendation isn't a plain "approve" on purpose.** The controls stopped every injection, misuse and exfiltration attempt, but testing showed that confidential sales and infrastructure data in the knowledge base was still disclosed to any employee. Guardrails can't fix that, so it became a launch condition.
- **Limitations are reported where I found them, not hidden.** Examples: the guardrail doesn't screen retrieved chunks, grounding isn't evaluated on harness traffic, and a base64-encoded injection got past the input filter. Each is documented with evidence and a compensating control.
- **Cloud Lab constraints.** CloudTrail and CloudShell weren't available, and the IAM policy simulator was denied, so I used equivalent API calls and a local policy evaluator. The lab revoked credentials between sessions. These are noted where they affected a test.
- **The `.py` and `.json` files are supporting evidence.** Scripts and raw results sit next to each report, so every number can be traced back. You don't need to run anything to review the work.
- **Data.** The knowledge base documents are the fictional course data, but the reports treat them as real confidential data. No credentials are committed.
