# Least Privilege Worksheet: ResearchBot IAM Roles

Fill in each row as you complete the review and rewrite tasks in the exercise. Add one row per violation found per role.

---

## Violation Inventory

| Role | Statement Sid | Violation Found | What an Attacker Can Do (Original) | Fixed Action(s) | Fixed Resource(s) |
|---|---|---|---|---|---|
| `agent_execution_role` (harness execution) | BedrockFullAccess | | | | |
| `agent_execution_role` (harness execution) | S3FullAccess | | | | |
| `agent_execution_role` (harness execution) | AgentCoreFullAccess | | | | |
| `kb_sync_role` (KB service) | S3FullAccess | | | | |
| `kb_sync_role` (KB service) | BedrockFullAccess | | | | |
| `streamlit_app_role` | BedrockFullAccess | | | | |
| `streamlit_app_role` | CloudWatchFullAccess | | | | |
| `streamlit_app_role` | CloudWatchLogsFullAccess | | | | |

---

## Blast Radius Analysis

For each role, describe the worst-case impact of a credential compromise under the original policy and under your fixed policy.

### agent_execution_role

**Original policy blast radius:**

_What can an attacker do if this role's credentials are stolen?_

> (fill in)

Consider: data exfiltration, model invocation abuse, harness and guardrail changes, service disruption, lateral movement, cost impact.

**Fixed policy blast radius:**

_After your remediation, what is the attacker limited to?_

> (fill in)

**Blast radius reduction summary** (one sentence):

> (fill in)

---

### kb_sync_role

**Original policy blast radius:**

> (fill in)

**Fixed policy blast radius:**

> (fill in)

**Blast radius reduction summary** (one sentence):

> (fill in)

---

### streamlit_app_role

**Original policy blast radius:**

> (fill in)

**Fixed policy blast radius:**

> (fill in)

**Blast radius reduction summary** (one sentence):

> (fill in)

---

## Reflection Questions

Answer these after completing all three roles.

**1. Which role had the highest blast radius under the original policy, and why?**

> (fill in)

**2. The `kb_sync_role` originally had `s3:*` scoped to just the `gencore-research-kb` bucket. Is that sufficient? Why or why not?**

> (fill in)

**3. The `streamlit_app_role` needs to write logs. The original policy uses `logs:*` on `*`. What is the minimum set of CloudWatch Logs actions actually needed, and what resource should they be scoped to?**

> (fill in)

**4. Any caller that can invoke the harness can pass a per-request `model` override. Why can't the app's caller policy block that, and how does the Deny with `bedrock:GuardrailIdentifier` on the harness execution role help?**

> (fill in)

**5. The original `streamlit_app_role` grants `bedrock:*`. Could the app call the harness with that policy? What does the grant expose instead?**

> (fill in)

**6. If you were integrating IAM policy review into a CI/CD pipeline for ResearchBot, what tool would you use and at what pipeline stage would you place it?**

> (fill in)

---

## Console Notes: Record Your AWS Resources

Fill in these values as you work through the IAM configuration. You'll need them when applying least privilege to your capstone project.

| Resource | Your Value |
|---|---|
| Harness execution role name | |
| Harness execution role ARN | |
| Gateway service role name | |
| Knowledge base service role name | |
| App caller role name (only if you create one; in the Udacity lab, you call the harness with the lab's `voclabs` role) | |
| App caller role ARN (only if you create one) | |
| Harness ARN | |
| Gateway ARN | |
| Knowledge base ID | |
| Guardrail ARN | |
| S3 bucket name | |
| AWS region | |

**Notes / observations:**

_Anything surprising, a policy decision you debated, or a question to follow up on_
