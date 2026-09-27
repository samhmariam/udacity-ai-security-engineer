# SOLUTION — Exercise 03: Audit the CaseAssist API Configuration

This document is the answer key for skill-pair-03. Open it after you've completed every task. CaseAssist runs on an Amazon Bedrock AgentCore harness.

The exercise has two tasks. Task 1 is the written security review of `app_config_review.py` (Part A), `iam_policy_overpermissive.json` (Part B), and `bedrock_invocation.py` (Part C). Task 2 is the checklist.

---

## Task 1 — Security Review

## Part A: `app_config_review.py`

### Issue 1: Hardcoded credentials
**Lines:** `AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"` and `AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"`

**Why it's a problem:** Static credentials in source code get committed to version control and are visible to anyone with repo access. They can't be rotated without a code change. If the repo is ever made public, scanners find them quickly. AWS scans for exposed keys and will alert you, but the damage is done.

**Fix:** Remove credentials from code entirely. On AWS compute (EC2, ECS, Lambda), use the attached instance, task, or execution role. boto3 uses it automatically with no credentials in code.

### Issue 2: No input length limit or validation
**Line:** `messages=[{"role": "user", "content": [{"text": user_input}]}]  # No length limit, no sanitization`

**Why it's a problem:** An attacker can submit a 100,000-character input, filling the context window and generating maximum-cost responses. At scale this is a financial DoS attack. Long inputs also give an attacker more room to build a prompt injection payload.

**Fix:**
```python
MAX_INPUT_CHARS = 2000

def query_agent(user_input: str) -> str:
    if not user_input or not user_input.strip():
        raise ValueError("Input cannot be empty.")
    if len(user_input) > MAX_INPUT_CHARS:
        raise ValueError(f"Input exceeds maximum length of {MAX_INPUT_CHARS} characters.")
    # ... proceed with API call
```

### Issue 3: Configuration values hardcoded (not from environment variables)
**Lines:** `HARNESS_ARN = "arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/CaseAssist-ABC123DEF4"` and `region_name='us-east-1'`

**Why it's a problem:** The harness ARN and Region are deployment-specific. Hardcoding them means the same code can't serve dev, staging, and prod without edits, and it commits deployment detail (account ID, harness ID) to version control. It's more a configuration management problem than a security one, and it still belongs in the findings.

**Fix:**
```python
import os

HARNESS_ARN = os.environ["AGENTCORE_HARNESS_ARN"]       # required — raise if missing
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")  # optional with default
```

### Issue 4: No error handling — raw exceptions expose internal details
**Problem:** The function has no try/except. If the call fails (throttling, access denied, invalid harness ARN), the raw boto3 exception, with ARNs, Region, and internal configuration, propagates to the caller and possibly the user interface. A harness can also report failures inside the stream as a `runtimeClientError` event, for example an IAM denial on the model call, so the stream needs checking too.

**Fix:**
```python
import logging
import botocore.exceptions

logger = logging.getLogger(__name__)

try:
    response = client.invoke_harness(...)
    answer = ""
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                answer += delta["text"]
        elif "runtimeClientError" in event:
            logger.error("Harness runtime error: %s", event["runtimeClientError"])
            raise RuntimeError("An error occurred processing your request.")
except botocore.exceptions.ClientError as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "ThrottlingException":
        raise RuntimeError("Service is temporarily unavailable. Please try again.") from None
    elif error_code == "ValidationException":
        raise ValueError("Invalid request. Please check your input.") from None
    else:
        # Log the full error internally; return a generic message to the user
        logger.error("Harness API error: %s", str(e))
        raise RuntimeError("An error occurred processing your request.") from None
```

### Issue 5: Raw response returned directly
**Line:** `return response`

**Why it's a problem:** `invoke_harness` returns a response whose `stream` is an event stream, not a string, so a UI can't use it directly. Returning it raw forces callers to know the harness event format, and it exposes response metadata (HTTP headers, request ID) to code that should only see the answer text.

**Fix:** Parse the stream and return only the text from `contentBlockDelta` events (as in `bedrock_invocation.py`, plus the error handling above).

---

## Part B: `iam_policy_overpermissive.json`

### What's wrong with the original policy
The original policy (`iam_policy_overpermissive.json`) grants:
- `bedrock:*` on `*`: every Bedrock action on every Bedrock resource
- `s3:*` on `*`: every S3 action on every bucket in the account
- `logs:*` and `cloudwatch:*` on `*`: every CloudWatch and Logs action on every resource

### Bedrock actions the wildcard exposes
The app needs to call one harness: `bedrock-agentcore:InvokeHarness` and `bedrock-agentcore:InvokeAgentRuntime`, both on the harness ARN. Those actions are in the `bedrock-agentcore` service prefix, not `bedrock`, so the wildcard grants nothing the app needs. What it does grant:
- `bedrock:InvokeModel` on any foundation model: call any model at Apex Legal's expense. There's no model access step to stop this, so IAM is the only gate.
- `bedrock:UpdateGuardrail` / `bedrock:DeleteGuardrail`: weaken or remove the guardrail that controls what CaseAssist returns (privilege escalation)
- `bedrock:DeleteKnowledgeBase`: destroy production resources
- `bedrock:PutModelInvocationLoggingConfiguration` / `bedrock:DeleteModelInvocationLoggingConfiguration`: turn off or redirect the audit trail
- `bedrock:ListFoundationModels`: enumerate the models the account can reach

### What the S3 wildcard exposes
`s3:*` on `*` lets the application role read, write, and delete objects in *every S3 bucket in the account*, including buckets with CloudTrail logs, deployment artifacts, backups, and other sensitive data. An attacker who compromises this role can exfiltrate across all buckets and delete log objects to cover their tracks.

On a harness, the app role doesn't need S3 at all. The knowledge base and gateway roles read the documents, and the caller only talks to the harness. Remove the S3 statement.

### Corrected policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeCaseAssistHarnessOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeHarness",
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-east-1:123456789012:harness/CaseAssist-ABC123DEF4"
    },
    {
      "Sid": "AppLogsWrite",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/caseassist/app-logs:*"
    }
  ]
}
```

Notes:
- Both invoke actions are required on the **harness** ARN. `InvokeHarness` alone is denied with an error naming `InvokeAgentRuntime` on the harness, and granting `InvokeAgentRuntime` on the underlying runtime ARN doesn't fix it.
- The caller needs no `bedrock:InvokeModel`, `bedrock:Retrieve`, or S3 permissions.

### Beyond the caller policy: the harness role
A caller with only the two invoke actions can still send a per-request `model` override. `InvokeHarness` has no condition keys, so the caller policy can't prevent it. An override without `additionalParams.guardrailConfig` runs with no guardrail at all. Enforcement belongs on the harness execution role:

1. Scope `bedrock:InvokeModel*` to the inference profile and foundation model ARNs the harness uses. The console's default role allows `foundation-model/*` and every Bedrock resource in the account.
2. Add an inline Deny. Use the ARN condition operator `ArnNotLike`. `bedrock:GuardrailIdentifier` holds an ARN, and IAM Access Analyzer flags a string operator such as `StringNotLike` on it as a security warning.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyModelCallsWithoutCaseAssistGuardrail",
      "Effect": "Deny",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "bedrock:GuardrailIdentifier": [
            "arn:aws:bedrock:us-east-1:123456789012:guardrail/<guardrail-id>",
            "arn:aws:bedrock:us-east-1:123456789012:guardrail/<guardrail-id>:*"
          ]
        }
      }
    }
  ]
}
```

With this in place, an override without the guardrail fails with `AccessDenied`, and normal guarded calls keep working. Add this Deny only after a guardrail is attached to the harness. With no guardrail attached, it blocks every model call. This isn't a required answer. It's a stretch finding for Task 1.

---

## Part C: `bedrock_invocation.py` and Credential Handling

### The correct way to get credentials on AWS compute

On EC2, ECS, or Lambda, **use the attached IAM role** and never pass credentials explicitly. Each compute service has its own role mechanism:
- **EC2:** attach an instance profile; the instance metadata service (IMDS) provides temporary credentials
- **ECS/Fargate:** assign a task role in the task definition; credentials come from the ECS credentials provider
- **Lambda:** assign an execution role to the function

With an attached role, boto3 needs no credential configuration:
```python
import boto3
client = boto3.client("bedrock-agentcore", region_name="us-east-1")
# That's it — boto3 resolves credentials automatically from the role
```

Check which identity the SDK resolved with `aws sts get-caller-identity`. In the Udacity lab it returns the voclabs assumed role, because the lab supplies credentials rather than a compute role.

### Why passing keys explicitly is wrong: the boto3 credential chain (in order)

boto3 checks these sources in order and stops at the first one that provides credentials:

1. Credentials passed explicitly to `boto3.client()` (`aws_access_key_id=...`). **This is what `bedrock_invocation.py` does, and why it overrides everything else.**
2. Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
3. Assumed role providers: a `role_arn` profile in `~/.aws/config`, or `AWS_ROLE_ARN` + `AWS_WEB_IDENTITY_TOKEN_FILE` (OIDC/web identity)
4. AWS SSO credentials from `aws sso login`
5. AWS credentials file: `~/.aws/credentials` (profile section)
6. AWS config file: `~/.aws/config`
7. Container credentials, such as the Amazon ECS task role (via the ECS credential endpoint)
8. Amazon EC2 instance profile credentials (via IMDS at `169.254.169.254`)

For production on AWS compute, you want the chain to reach step 7 or 8: nothing configured above it, so the role is used automatically.

### Local development without credentials in source code

Two safe approaches, both without long-lived keys:

1. **AWS SSO (recommended for teams):** `aws sso login` with an SSO profile grants short-lived tokens tied to your identity. No long-lived keys.
2. **Assume a role locally:** set a `role_arn` in `~/.aws/config` that your user or SSO identity can assume. boto3 resolves it automatically.

What developers should **never** do: copy production credentials into `.env` files, hardcode them in source, keep long-lived IAM user access keys on a laptop, or use the production role's keys on a laptop.

---

## Beyond the Exercise (Not Required)

The exercise doesn't ask these questions. Use them to check your understanding after you finish Tasks 1 and 2.

### Question 1: "TLS is handled for us — we don't need to think about transport security"

Partly right, but incomplete. TLS protects data in transit between the app and the AWS endpoint. It ends at the endpoint, where the payload is decrypted and processed. What TLS does **not** cover:
- The payload once it reaches AWS, including what gets written to invocation logs
- A compromised signing key. Requests signed with stolen credentials are still valid over TLS.
- Input validation. A malicious prompt travels safely over TLS and arrives intact at the model.

**What you should still think about:** use the SDK so SigV4 signing is correct, keep unnecessary sensitive data out of request payloads, and protect the logs those payloads end up in.

### Question 2: Logging trade-off — disable vs. enable with controls

Disabling model invocation logging to avoid storing user data is the wrong trade-off. Without logs you can't investigate a suspected prompt injection, prove what the model said in a disputed exchange, audit for data exposure, or detect abuse.

Be clear about what the logs hold. Harness calls are logged as `ConverseStream` records with the full prompt, the system prompt, and the text of retrieved chunks. When a guardrail blocks an answer, the original answer is still in `trace.guardrail.modelOutput`. For CaseAssist that means client matter content lands in the logs.

So **enable logging with controls:**
- Store logs with **server-side encryption** (SSE-KMS for S3, or a KMS key on the log group)
- Restrict write access to the Bedrock logging role and read access to the security team
- Enable **S3 Object Lock** (WORM) if logs go to S3, to prevent tampering
- Set a **retention period** (e.g., 90 days for operational logs, longer where compliance requires)
- If logs contain PII or privileged content, add a **redaction step** before long-term storage

### Question 3: Two attack scenarios enabled by `s3:*` on `*`

**Scenario A — Cross-bucket exfiltration:** The role can call `s3:ListBuckets` to enumerate every bucket, then `s3:GetObject` on any of them: CloudTrail logs, database backups, deployment secrets. The CaseAssist app role needs no S3 access at all, so removing the statement closes this completely.

**Scenario B — Log tampering to cover tracks:** With `s3:*`, the compromised role can call `s3:DeleteObject` on the CloudTrail log bucket (if it's in the same account) and delete the entries covering the attack window. A policy with no S3 access prevents it.

---

## Task 2 — API Security Checklist (Model Answers)

| Item | Status | Note |
|---|---|---|
| No hardcoded credentials in source code | **FAIL** | `app_config_review.py` has `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` hardcoded as string literals |
| IAM role used for authentication | **FAIL** | Both files pass static credentials explicitly to `boto3.client()` instead of relying on the SDK credential chain and an attached role |
| Credentials never written to logs or error output | **FAIL** | No error handling, so a boto3 exception can surface credential or configuration details |
| Harness ARN stored in environment variable | **FAIL** | `HARNESS_ARN` is hardcoded in `app_config_review.py`, and `bedrock_invocation.py` falls back to a hardcoded ARN |
| Harness endpoint qualifier stored in environment variable | **N/A** | Both files call the DEFAULT endpoint and pass no qualifier |
| AWS region stored in environment variable | **FAIL** | `region_name='us-east-1'` is hardcoded in `app_config_review.py`, and `bedrock_invocation.py` defaults to it |
| Minimum required IAM actions only | **FAIL** | `iam_policy_overpermissive.json` uses `bedrock:*`, `s3:*`, `logs:*`, `cloudwatch:*`, and none of them are the `bedrock-agentcore` invoke actions the app needs |
| Resource ARNs are specific | **FAIL** | All three statements use `"Resource": "*"` |
| No S3 access beyond what the application needs | **FAIL** | `s3:*` on `*` reaches every bucket, and the app needs no S3 access at all |
| CloudWatch Logs access scoped to minimum required actions | **FAIL** | `logs:*` and `cloudwatch:*` are far broader than the two actions needed to write app logs |
| Input length limits enforced at application layer | **FAIL** | `app_config_review.py` passes `user_input` directly with no length check |
| User input is not passed directly without validation | **FAIL** | No validation of any kind before the harness call |
| Error responses do not expose stack traces or internal details | **FAIL** | No error handling in either file; raw exceptions propagate and `runtimeClientError` events are ignored |
| Raw API response objects are not returned to the UI | **FAIL** | `app_config_review.py` returns `response` directly |
| Model invocation logging enabled in Bedrock settings | **FAIL** | The scenario says logging isn't turned on in the account's Bedrock settings. It's an account-level setting (see Console Walkthrough) |
| HTTPS enforced for all API calls | **PASS** | boto3 uses HTTPS for all AWS API calls |

**Total: 16 items. Pass 1 / Fail 14 / N/A 1**

---

## Console Walkthrough: Implementing Secure Configuration in the AWS Console

### 1. Create and attach a least-privilege IAM policy for the app

1. Go to **IAM > Policies > Create policy**
2. Choose the **JSON** tab and paste the corrected policy
3. Choose **Next**, name the policy (e.g., `caseassist-app-policy`), and choose **Create policy**
4. Go to **Roles**, open the role attached to your EC2 instance, ECS task, or Lambda function
5. Choose **Add permissions > Attach policies**, then attach `caseassist-app-policy`
6. Remove any overly permissive managed policies (e.g., `AmazonBedrockFullAccess`)

### 2. Scope the harness execution role

1. Go to **Amazon Bedrock AgentCore > Harness**, open the harness, and choose the **IAM role** link
2. Edit the execution policy so `bedrock:InvokeModel*` covers only the inference profile and foundation model the harness uses
3. After the guardrail is attached to the harness, choose **Add permissions > Create inline policy**, paste the Deny policy from Task 1, Part B, and save
4. Wait about a minute, then test: a normal call still works, and a call with a `model` override and no guardrail fails with `AccessDenied`

### 3. Enable Bedrock model invocation logging

Create the log group before you turn on logging. The role that Bedrock creates for logging can write to an existing log group, but it can't create one.

1. In **CloudWatch**, choose **Logs > Log groups > Create log group**, and create the log group for CaseAssist's invocation logs
2. Go to **Amazon Bedrock > Settings** and turn on **Model invocation logging**
3. Choose **CloudWatch Logs only** as the destination and enter the log group name
4. Choose **Save settings**. If saving fails with **Failed to validate permissions for log group**, the log group doesn't exist yet
5. Send a test question and confirm a `ConverseStream` record appears under the harness role

### 4. Find unused permissions with Last Accessed

IAM Policy Simulator is denied in the Udacity lab, so use the role's access history instead.

1. Open the role in **IAM > Roles** and choose the **Last Accessed** tab
2. Compare services granted with services used. On a default harness role after a round of testing, it showed 11 services granted and 5 used.
3. Remove grants for services the role never uses, then re-test the application

### 5. Use IAM Access Analyzer

1. Go to **IAM > Access Analyzer** and create an account analyzer if one doesn't exist
2. Review **Findings** for resources shared outside the account, and remediate each one
3. An **Unused access** analyzer also flags unused roles and permissions. It's billed per IAM role or user per month, so delete it when you're done.
