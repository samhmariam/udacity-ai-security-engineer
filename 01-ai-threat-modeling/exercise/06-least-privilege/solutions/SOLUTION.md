# SOLUTION: Exercise 06, Right-Size the ResearchBot IAM Roles

This document is the answer key for skill-pair-06. Open it after you've completed every task. Its task numbers match `EXERCISE.md`. The three fixed policy files are in `solutions/iam_roles/`:
- `agent_execution_role_fixed.json` (harness execution role)
- `kb_sync_role_fixed.json` (knowledge base service role)
- `streamlit_app_role_fixed.json` (app caller role)

ResearchBot runs on an Amazon Bedrock AgentCore harness. The harness calls a knowledge base Retrieve tool through an AgentCore Gateway, and the gateway searches a Managed Knowledge Base.

---

## Task 1: Review all three roles and identify violations

### `agent_execution_role.json` (harness execution role)

**Violation 1: `bedrock:*` on `*`**
- What's wrong: every Bedrock action on every Bedrock resource in the account.
- What an attacker can do: invoke any foundation model at GenCore Pharma's expense, change or delete guardrails, delete the knowledge base, change model invocation logging, and enumerate Bedrock resources. A caller can also pass a per-request `model` override, and a role that can invoke any model lets that override run anything.
- What it should be: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on the Claude Sonnet 4.5 inference profile and its foundation model ARNs, a Deny unless the ResearchBot guardrail is applied, and `bedrock:ApplyGuardrail` on that guardrail.

**Violation 2: `s3:*` on `*`**
- What's wrong: every S3 action on every bucket in the account.
- What an attacker can do: read, write, and delete objects in any bucket, including log, backup, and deployment buckets, and change bucket policies.
- What it should be: **nothing**. The harness doesn't read S3. It calls the gateway, the gateway calls Retrieve, and the knowledge base returns chunks.

**Violation 3: `bedrock-agentcore:*` on `*`**
- What's wrong: every AgentCore action on every AgentCore resource.
- What an attacker can do: update the harness, including its system prompt, model, and guardrail settings (`UpdateHarness`); invoke any harness or gateway; and use AgentCore Browser, Code Interpreter, and Memory.
- What it should be: `bedrock-agentcore:InvokeGateway` on the one gateway ARN.

### `kb_sync_role.json` (knowledge base service role)

**Violation 1: `s3:*` on the knowledge base bucket**
- What's wrong: scoping it to the bucket still allows `DeleteObject`, `PutObject`, and `PutBucketPolicy`.
- What an attacker can do: plant or delete documents, which then flow into ResearchBot's answers on the next sync, and change the bucket policy.
- What it should be: `s3:ListBucket` on the bucket and `s3:GetObject` on `gencore-research-kb/*`. The role needs only list and read.

**Violation 2: `bedrock:*` on `*`**
- What's wrong: every Bedrock action on every Bedrock resource.
- What an attacker can do: delete the knowledge base, change guardrails, and call any model.
- What it should be: `bedrock:InvokeModel` on the embedding model only.

### `streamlit_app_role.json`

**Violation 1: `bedrock:*` on `*`**
- What's wrong: the app never calls Bedrock directly. It also **doesn't cover the harness**. A role with only `bedrock:*` is denied `bedrock-agentcore:InvokeHarness`, yet it can still read guardrails and call models directly. So the original grant was both too broad and missing the one permission the app needs.
- What it should be: `bedrock-agentcore:InvokeHarness` and `bedrock-agentcore:InvokeAgentRuntime` on the harness ARN.

**Violation 2: `cloudwatch:*` on `*`**
- What's wrong: includes deleting alarms and dashboards, which the app never needs.
- What it should be: nothing. The app writes logs only.

**Violation 3: `logs:*` on `*`**
- What's wrong: the app needs only three log actions.
- What it should be: `logs:CreateLogStream`, `logs:PutLogEvents`, and `logs:DescribeLogStreams` on the one log group.

All resources in the original were `*`; the fix scopes them to specific ARNs.

### Why the Deny matters

Anyone who can invoke the harness can pass a per-request `model` override. `InvokeHarness` has no condition keys, so the caller's policy can't stop that. An override without guardrail settings runs with no guardrail. The Deny with `bedrock:GuardrailIdentifier` makes the guardrail required at the IAM layer. The `ArnNotLike` list of the guardrail ARN plus `ARN:*` also stops a caller from swapping in a weaker guardrail. Use the ARN condition operator `ArnNotLike`. `bedrock:GuardrailIdentifier` holds an ARN, and IAM Access Analyzer flags a string operator such as `StringNotLike` on it as a security warning.

Note: Bedrock has no `bedrock:ModelId` condition key. Scope models by resource ARN, or use `bedrock:ModelArn` or `bedrock:InferenceProfileArn`.

---

## Task 2: Write the three corrected policies

### `agent_execution_role_fixed.json`

Key design decisions:

- **Model allow-list:** the inference profile ARN plus the foundation model ARN in each Region the profile routes to (us-east-1, us-east-2, us-west-2). The profile ARN alone isn't enough.
- **Deny without the guardrail:** a model call that doesn't carry the ResearchBot guardrail fails with `AccessDeniedException`. The Deny uses `ArnNotLike`, because `bedrock:GuardrailIdentifier` holds an ARN.
- **`bedrock:ApplyGuardrail`** scoped to the one guardrail.
- **`bedrock-agentcore:InvokeGateway`** scoped to the one gateway.
- **No S3, no Retrieve.** Retrieval belongs to the gateway service role, which is outside this exercise.
- **Out of scope:** a deployed harness role also needs runtime statements for its own logs, ECR image pulls, X-Ray, and workload identity tokens. The lesson demo shows them. This exercise covers only the request path.

### `kb_sync_role_fixed.json` (knowledge base service role)

Bedrock assumes this role while a sync runs. During a sync it does two things:

1. **Lists and reads documents from S3** → `s3:ListBucket` on the bucket and `s3:GetObject` on `gencore-research-kb/*`
2. **Creates embeddings** → `bedrock:InvokeModel` on Titan Text Embeddings V2

A Managed Knowledge Base has no customer-managed vector store, so this role has no vector store permissions. It also doesn't need `bedrock:StartIngestionJob`. Whoever starts the sync (a person or a scheduled job) needs that permission under their own identity.

Stretch: if the data source uses one prefix, you can narrow `s3:GetObject` to that prefix and add an `s3:prefix` condition on `s3:ListBucket`.

### `streamlit_app_role_fixed.json`

The Streamlit app needs:

1. **Invoke the harness** → `bedrock-agentcore:InvokeHarness` and `bedrock-agentcore:InvokeAgentRuntime`, both on the **harness ARN**. `InvokeHarness` alone is denied, with an error naming `InvokeAgentRuntime` on the harness.
2. **Write application logs** → `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogStreams` on the one log group.

The app needs no model, knowledge base, or S3 permissions. The harness and gateway roles do that work.

---

## Task 3: Fill in the blast radius comparison

These answers go in the worksheet's **Blast Radius Analysis** section.

### `agent_execution_role`

**Original:** The attacker can call any model directly, change or delete guardrails, delete the knowledge base, and turn off invocation logging. They can also reconfigure the harness through `bedrock-agentcore:*` and read, write, or delete any object in any S3 bucket.

**Fixed:** The attacker can invoke Claude Sonnet 4.5 only with the ResearchBot guardrail applied, and call the one gateway. They can't change configuration, reach S3, or switch models.

---

### `kb_sync_role`

**Original:** The attacker can plant, overwrite, or delete documents in the knowledge base bucket and change its policy. They can also do anything in Bedrock: delete the knowledge base, change guardrails, and call any model.

**Fixed:** The attacker can list and read the documents ResearchBot already serves, and create embeddings with Titan. They can't write documents or reach any other Bedrock resource.

---

### `streamlit_app_role`

**Original:** The attacker can call any model directly, change guardrails, delete the knowledge base, and delete CloudWatch alarms, dashboards, and log groups, which would disable monitoring.

**Fixed:** The attacker can ask ResearchBot questions (the same capability any authenticated employee has) and write to one log group. If they pass a `model` override, the harness role's allow-list and Deny still apply.

---

## Reflection Question Answers

**1. Which role had the highest blast radius under the original policy, and why?**
`agent_execution_role`. It combined `bedrock:*`, `s3:*`, and `bedrock-agentcore:*` on `*`. An attacker could call any model, change or delete guardrails, delete the knowledge base, reach every S3 bucket, and reconfigure the harness, including its system prompt.

**2. Is `s3:*` scoped to the `gencore-research-kb` bucket sufficient?**
No. It limits which bucket, but it still allows every S3 action on that bucket, including `PutObject`, `DeleteObject`, and `PutBucketPolicy`. An attacker could plant or delete documents that reach ResearchBot's answers after the next sync. The role needs only `s3:ListBucket` and `s3:GetObject`.

**3. Minimum CloudWatch Logs actions for `streamlit_app_role`, and the resource?**
`logs:CreateLogStream`, `logs:PutLogEvents`, and `logs:DescribeLogStreams`, scoped to the `/aws/researchbot/app-logs` log group ARN.

**4. Why can't the app's caller policy block a model override, and how does the Deny help?**
`InvokeHarness` has no condition keys, so the caller's policy has nothing to check. The harness execution role makes the model call, so the control belongs on that role. Its model allow-list limits which models an override can run. The Deny on `bedrock:GuardrailIdentifier` blocks any model call that leaves out the ResearchBot guardrail or names a different guardrail.

**5. Could the app call the harness with `bedrock:*`? What does the grant expose instead?**
No. Harness actions are in the `bedrock-agentcore` service, so `bedrock:*` doesn't include `InvokeHarness`. The grant instead exposes guardrails, the knowledge base, and direct model calls.

**6. Which tool, and at what pipeline stage, for IAM policy review in CI/CD?**
IAM Access Analyzer policy validation, the same check the IAM JSON editor runs. Run it on every policy change at the build or pull request stage, before deployment, and fail the pipeline when validation reports Security or Errors findings. Validation alone doesn't catch over-permission: it reported 0 findings for the original `bedrock:*` and `s3:*` policies. So also run IAM Access Analyzer custom policy checks at the same stage, such as `check-no-new-access` against a reviewed baseline policy and `check-access-not-granted` for actions like `bedrock:DeleteGuardrail`.

---

## Console Walkthrough: IAM Least Privilege in the AWS Console

### 1. Create the policy with validation

1. Open **IAM → Roles** and choose the role.
2. Choose **Add permissions → Create inline policy**, then the **JSON** tab.
3. Paste the fixed policy.
4. Read the Access Analyzer validation counts under the editor: **Security**, **Errors**, **Warnings**, **Suggestions**. Fix anything flagged. The fixed harness policy uses `ArnNotLike` in its guardrail Deny, because `StringNotLike` on `bedrock:GuardrailIdentifier` is flagged as a security warning.
5. Choose **Next**, name the policy (for example `researchbot-harness-execution-scoped`), and create it.

### 2. Remove the over-permissive policy

1. On the role's **Permissions** tab, select the broad policy and choose **Remove** (for customer managed policies, detach them).
2. Confirm that only the scoped policy, plus any guardrail inline policy you intend to keep, remains.

### 3. Find unused permissions with Last Accessed

1. Open the role's **Last Accessed** tab.
2. Compare services granted with services used. On the Aria harness role, it showed 11 granted and 5 used.
3. Treat the unused list as candidates to remove, then re-test.

> **Lab note:** IAM Policy Simulator and **Generate policy based on CloudTrail events** are denied in the Udacity Cloud Lab. Use Last Accessed and a live re-test instead.

### 4. Re-test the scoped roles

Wait about a minute after changing policies, then:

1. Ask ResearchBot a knowledge base question. Expect a Retrieve tool call and an answer.
2. Send a prompt the guardrail should block. Expect the blocked message.
3. Invoke with a per-request `model` override to a model that isn't on the allow-list. The override is a `model` argument on the `invoke_harness` call, for example `model={"bedrockModelConfig": {"modelId": "us.amazon.nova-2-lite-v1:0", "apiFormat": "converse_stream"}}`. Expect `runtimeClientError` wrapping `AccessDeniedException` on `ConverseStream`.

If step 1 fails, a permission on the request path is missing. If step 3 succeeds, the model allow-list isn't in effect.
