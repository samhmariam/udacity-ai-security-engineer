# IAM Access Analyzer Findings: GenCore ResearchBot Account

Use this file for the lesson 13 exercise, "Write an SCP for Enterprise Bedrock Governance". Save your trust policy review, SCP, finding remediations, and governance model in `starter/SCP_GOVERNANCE_MODEL.md`.

These findings are example data for the exercise. They weren't produced by a live analyzer. Finding 1 follows the same pattern as the access preview in the lesson demo.

- **Account:** `123456789012` (GenCore Pharma, ResearchBot workload)
- **Analyzer type:** Account
- **External account in every finding:** `111122223333` (GenCore shared-services account)

The permission policies for the two roles are in `starter/iam_roles/`. The trust policies are in `starter/iam_roles/trust_policies/`.

---

## Context: Approved Relationships With the Shared-Services Account

The platform team has approved exactly two jobs that run in account `111122223333`:

| Job | Role in account 111122223333 | Approved purpose |
|---|---|---|
| Deployment smoke test | `ResearchBotDeployPipeline` | After each deployment, assumes the app role to confirm the app can call the harness |
| Nightly model evaluation | `ResearchBotEvalRunner` | Assumes the harness execution role to run evaluation prompts against the approved model |

No approved job gives the shared-services account access to knowledge base documents.

---

## Finding 1

| Field | Value |
|---|---|
| Resource | `arn:aws:s3:::gencore-research-kb` |
| Resource type | `AWS::S3::Bucket` |
| Holds | The documents behind the ResearchBot knowledge base |
| External principal | Account `111122223333` |
| Actions | `s3:GetObject`, `s3:ListBucket` |
| Access level | Read and list |
| Public | No |
| Condition | None |
| Granted by | Bucket policy |
| Status | Active |

## Finding 2

| Field | Value |
|---|---|
| Resource | `agent_execution_role` (harness execution role) |
| Resource type | `AWS::IAM::Role` |
| External principal | `arn:aws:iam::111122223333:root` (any principal in account `111122223333` that its own account allows to assume the role) |
| Action | `sts:AssumeRole` |
| Condition | None |
| Granted by | Trust policy statement `AllowSharedServicesAccount` |
| Status | Active |

## Finding 3

| Field | Value |
|---|---|
| Resource | `streamlit_app_role` |
| Resource type | `AWS::IAM::Role` |
| External principal | `arn:aws:iam::111122223333:role/ResearchBotDeployPipeline` |
| Action | `sts:AssumeRole` |
| Condition | `sts:ExternalId` equals `gencore-researchbot-deploy` |
| Granted by | Trust policy statement `AllowDeployPipelineRole` |
| Status | Active |

---

## Why `kb_sync_role` Has No Finding

The `kb_sync_role` trust policy trusts only the Bedrock service (`bedrock.amazonaws.com`). It doesn't trust any external account, so it has no external-access finding.

---

## For Each Finding, Record

1. Which resource is exposed
2. Which external principal can reach it
3. What access the principal has, including what the role's permission policy allows after the principal assumes it
4. Whether the access was never intended, intended but broader than necessary, or appropriate
5. Your remediation
