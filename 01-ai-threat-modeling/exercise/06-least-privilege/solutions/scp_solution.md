# Solution: Write an SCP for Enterprise Bedrock Governance

This is an example answer for the lesson 13 exercise. Your wording can differ. Check that your answer makes the same decisions.

The inputs are:

- `starter/iam_roles/` (permission policies)
- `starter/iam_roles/trust_policies/` (trust policies)
- `starter/access_analyzer_findings.md` (the three findings)

> **Not tested in the lab.** The Cloud Lab account can't use AWS Organizations, so this SCP couldn't be created or attached. Read it and reason about what it blocks.

---

## 1. The Trust Policies

| Role | Who can assume it | What the role allows after someone assumes it |
|---|---|---|
| `agent_execution_role` | The AgentCore service (`bedrock-agentcore.amazonaws.com`), and **any principal in account `111122223333`** that its own account allows (`arn:aws:iam::111122223333:root`, no condition) | `bedrock:*`, `s3:*`, and `bedrock-agentcore:*` on `*` |
| `streamlit_app_role` | The ECS tasks service (`ecs-tasks.amazonaws.com`), and one role, `arn:aws:iam::111122223333:role/ResearchBotDeployPipeline`, only with the external ID `gencore-researchbot-deploy` | `bedrock:*`, `cloudwatch:*`, and `logs:*` on `*` |
| `kb_sync_role` | The Bedrock service (`bedrock.amazonaws.com`) only | `s3:*` on the `gencore-research-kb` bucket, and `bedrock:*` on `*` |

The two cross-account trust policies differ in how precisely they name the external principal:

- `agent_execution_role` names the whole account. So anyone in the shared-services account who has `sts:AssumeRole` permission there can become the harness execution role. That role can invoke any model, change guardrails, read or delete any S3 bucket in the account, and reconfigure the harness.
- `streamlit_app_role` names one role and requires an external ID.

The broader principal on `agent_execution_role`, combined with service-wide permissions, is the most serious problem.

The permissions each role allows are also too broad. Scoping them is account-level least-privilege work. The SCP below doesn't fix them, but it limits which models any of them can invoke.

---

## 2. The Service Control Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnapprovedModels",
      "Effect": "Deny",
      "Action": "bedrock:InvokeModel*",
      "NotResource": [
        "arn:aws:bedrock:us-east-1:*:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
      ]
    },
    {
      "Sid": "DenyUnapprovedRegions",
      "Effect": "Deny",
      "Action": "bedrock:InvokeModel*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-east-2", "us-west-2"]
        }
      }
    }
  ]
}
```

### How It Works

- **`DenyUnapprovedModels`** denies `bedrock:InvokeModel*` on every resource except the ARNs in `NotResource`. The approved list has:
  - The US Claude Sonnet 4.5 inference profile
  - The Claude Sonnet 4.5 foundation model in each Region the profile routes to (`us-east-1`, `us-east-2`, `us-west-2`)
  - Titan Text Embeddings V2, which the knowledge base service role uses to create embeddings during sync. If you leave it out, knowledge base sync fails.
- **`DenyUnapprovedRegions`** denies `bedrock:InvokeModel*` in any Region outside the list. This addresses data residency, meaning rules about where data is stored and processed. This statement covers only model invocation. You can widen it to other `bedrock:*` and `bedrock-agentcore:*` actions, so that no one creates harnesses or knowledge bases in an unapproved Region. Both scopes are defensible.
- **Both statements are denies.** The policy sets a ceiling. It doesn't grant anyone permission to invoke a model. Each role still needs its own IAM policy that allows the call. Deny-only SCPs like this one also assume that the default `FullAWSAccess` SCP stays attached.
- **An explicit deny overrides any allow.** A business unit administrator who attaches `bedrock:*` to a role in their account still can't invoke a model outside the list.

### Why the Region List Has Three Regions

The inference profile `us.anthropic.claude-sonnet-4-5-20250929-v1:0` is a cross-Region inference profile. It can send a request to a Region other than the one you call. A Region allow-list must include every Region the inference profile uses, or the ceiling blocks the approved model.

In the lab, Aria's invocation logs recorded inference in `us-east-2`, and a scoped harness role that allowed the foundation model in `us-east-1`, `us-east-2`, and `us-west-2` kept working. The demo's example policy uses the same three Regions.

### Another Way to Restrict Models

Instead of `NotResource`, you can match the `bedrock:ModelArn` and `bedrock:InferenceProfileArn` condition keys. Bedrock has no `bedrock:ModelId` condition key.

---

## 3. The Findings

| Finding | Resource | External principal | Access | Decision | Remediation |
|---|---|---|---|---|---|
| 1 | `gencore-research-kb` bucket (`AWS::S3::Bucket`) | Account `111122223333` | Read and list (`s3:GetObject`, `s3:ListBucket`), not public | **Never intended.** No approved job needs knowledge base documents. | Remove the statement from the bucket policy. Run an access preview on the new bucket policy to confirm no external-access finding remains. |
| 2 | `agent_execution_role` (`AWS::IAM::Role`) | `arn:aws:iam::111122223333:root` | `sts:AssumeRole`, then `bedrock:*`, `s3:*`, `bedrock-agentcore:*` | **Intended, but broader than necessary.** Only `ResearchBotEvalRunner` needs this role. | Change the principal to `arn:aws:iam::111122223333:role/ResearchBotEvalRunner` and add an `sts:ExternalId` condition. Scope the role's permission policy to the approved model. |
| 3 | `streamlit_app_role` (`AWS::IAM::Role`) | `arn:aws:iam::111122223333:role/ResearchBotDeployPipeline` with an external ID | `sts:AssumeRole`, then `bedrock:*`, `cloudwatch:*`, `logs:*` | **Appropriate trust.** It names the one approved role and requires an external ID. | Document the finding and its approved purpose so the next reviewer doesn't treat it as an anomaly. Record that the role's permission policy still needs scoping. |

---

## 4. The Governance Model

| Layer | Controls | Who maintains them |
|---|---|---|
| Organization | The SCP above: approved models and approved Regions for model invocation | Platform team |
| Account | IAM permission policies and trust policies for each workload role, and resource policies such as bucket policies | The team that owns the workload |
| Monitoring | IAM Access Analyzer external-access findings for buckets and roles, access previews before resource policy changes, and review of each role's Last Accessed data and policy validation results | Platform team reviews findings. Workload teams fix their own roles. |

### What the Monitoring Detects

- **Access Analyzer findings** show when a bucket or role becomes reachable from outside the account, as in findings 1 and 2.
- **Access previews** catch that exposure before a new resource policy is applied.
- **Last Accessed data and policy validation** show when a role can do far more than its workload uses.

Without this monitoring, the SCP stays in place, but the permissions below it drift.
