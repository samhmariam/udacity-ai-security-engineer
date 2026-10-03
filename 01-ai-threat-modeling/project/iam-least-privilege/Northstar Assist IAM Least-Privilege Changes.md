# Northstar Assist: IAM Least-Privilege Changes

| Field | Value |
|---|---|
| System | Northstar Assist (harness `NorthstarAssist-yH4PMorNwm`, gateway `northstar-assist-gateway-bkdy1kxxxm`, KB `ZCAWWBRBXU`) |
| Account / Region | `911470903119` / `us-east-1` |
| Date applied | 2026-10-02 |
| Applied by | Samuel H. Mariam |
| Roles changed | Harness execution role `AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869` and gateway service role `AmazonBedrockAgentCoreGatewayDefaultServiceRole1790959690216` |
| Related findings | ML-BOM **F-07**, threat model **E-02** (and the gateway-role gaps noted in ML-BOM S6) |
| Evidence in this folder | `before/` (original policy and trust documents), `after/` (applied documents), `policy-evaluation-results.json` (31-case before/after evaluation) |

## 1. Summary

The console created both roles with "default" policies that cover every feature a harness or gateway *might* use. Northstar Assist uses one model, one gateway and one knowledge base, so most of those permissions were unnecessary attack surface.

| Role | Policy | Before | After | Net effect |
|---|---|---|---|---|
| Harness execution role | `AmazonBedrockAgentCoreHarnessExecutionPolicy_5o3kt` | v1: 21 statements | **v2: 12 statements**. Now **v3** (13 statements, adding the guardrail grant; default), plus the inline Deny `NorthstarRequireGuardrail` | Model invocation narrowed from *any model in any Region, plus every Bedrock resource in the account* to **Claude Haiku 4.5 through the global inference profile only**. Browser, Code Interpreter, EFS, S3 Files, Memory and Bedrock Mantle permissions removed. Logs scoped to Northstar's own runtime log group. |
| Harness execution role | `AmazonBedrockAgentCoreHarnessGatewayPolicy_0vzcg` | v1 | v1 (unchanged) | Already allowed `InvokeGateway` on the Northstar gateway only |
| Harness execution role | Trust policy | Any AgentCore resource in the account | **Only the NorthstarAssist harness and its runtime** | Another AgentCore agent in the account can no longer assume this role |
| Gateway service role | `AmazonBedrockAgentCoreGatewayKBAccessProd_3C50B7` | v1: 7 statements | **v2: 2 statements** (now default) | Retrieval limited to **KB `ZCAWWBRBXU` only**. Model use limited to **Titan Text Embeddings V2**. Guardrail, Rerank and inference-profile permissions removed. |
| Gateway service role | `AmazonBedrockAgentCoreGatewayBasePolicyProd_7C8E46` | v1 | **v2** (now default) | `GetGateway` narrowed from `northstar-assist-gateway-*` to the exact gateway |
| Gateway service role | Trust policy | Any gateway named `northstar-assist-gateway-*` | **Only `northstar-assist-gateway-bkdy1kxxxm`** | A new gateway with a look-alike name can no longer assume this role |

All changes were made as **new policy versions**, so v1 is kept and rollback is a single command (section 8). Trust policies were updated in place, and the originals are saved in `before/`.

------------------------------------------------------------------------

## 2. Harness Execution Role: Before vs After

`arn:aws:iam::911470903119:role/service-role/AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869`

### 2.1 Statement-by-statement comparison (`AmazonBedrockAgentCoreHarnessExecutionPolicy_5o3kt`)

| # | Original statement (v1) | Original scope | Change in v2 | Rationale |
|---|---|---|---|---|
| 1 | `BedrockModelInvocation`: `bedrock:InvokeModel`, `InvokeModelWithResponseStream` | **`arn:aws:bedrock:*::foundation-model/*`** (every foundation model, every Region) **and `arn:aws:bedrock:us-east-1:911470903119:*`** (every Bedrock resource in the account: all inference profiles, custom and imported models, provisioned throughput) | **Replaced with two statements.** `InvokeHaikuGlobalInferenceProfile` allows only `inference-profile/global.anthropic.claude-haiku-4-5-20251001-v1:0`. `InvokeHaikuFoundationModelOnlyThroughProfile` allows only `foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0` (the Region-less global ARN and the Regional ARNs the global profile routes to), **with the condition `bedrock:InferenceProfileArn` = the Haiku global profile** | The harness is configured with exactly one model ID. Global cross-Region inference requires permission on the profile and on the underlying foundation model in the destination Regions, which is why the foundation-model statement keeps a Region wildcard. The condition stops that wildcard from being used to call Haiku directly or through any other profile. Nothing else in Bedrock is reachable. |
| 2 | `BedrockMantleInference`: `bedrock-mantle:CreateInference` | `bedrock-mantle:us-east-1:911470903119:*` | **Removed** | The harness uses `apiFormat: converse_stream` (the Bedrock Runtime ConverseStream API), not the Bedrock Mantle inference endpoint |
| 3 | `BedrockMantleCallWithBearerToken`: `bedrock-mantle:CallWithBearerToken` | **`*`** | **Removed** | Bearer-token (API key) model access isn't used. A bearer-token path to inference bypasses SigV4 request signing and is a common credential-leak vector. |
| 4 | `EcrPublicTokenAccess`: `ecr-public:GetAuthorizationToken` | `*` | **Kept** (merged into `EcrAuthorizationTokens`) | The managed harness runtime pulls its container image. These token APIs only support `*`, and a token gives no access by itself. |
| 5 | `StsForEcrPublicPull`: `sts:GetServiceBearerToken` | **`*`, for any service** | **Scoped** with the condition `sts:AWSServiceName = ecr-public.amazonaws.com` | Keeps the ECR Public pull working, and stops the role from minting bearer tokens for any other service that accepts them |
| 6 | `EcrManagedImagePull`: `ecr:BatchGetImage`, `GetDownloadUrlForLayer`, `BatchCheckLayerAvailability` | `arn:aws:ecr:us-east-1:*:repository/harness-*` | **Kept** | Needed to pull the AWS-managed harness image. The account is a wildcard because the image lives in an AWS-owned account. |
| 7 | `EcrManagedImageToken`: `ecr:GetAuthorizationToken` | `*` | **Kept** (merged into `EcrAuthorizationTokens`) | The API supports only `*`. It is needed for the image pull. |
| 8 | `XRayTracingAccess`: `xray:PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`, `GetSamplingTargets` | `*` | **Kept** | Observability (tracing). X-Ray doesn't support resource-level permissions for these actions, and they are write-only telemetry. |
| 9 | `CloudWatchLogsGroup`: `logs:CreateLogGroup`, `DescribeLogStreams` | `log-group:/aws/bedrock-agentcore/runtimes/*` (**every agent's runtime logs**) | **Scoped** to `log-group:/aws/bedrock-agentcore/runtimes/harness_NorthstarAssist-*` | Northstar Assist should only touch its own log group |
| 10 | `CloudWatchLogsDescribeGroups`: `logs:DescribeLogGroups` | `log-group:*` | **Kept** | Read-only metadata (group names, no log contents). The runtime uses it to find its log group. |
| 11 | `CloudWatchLogsStream`: `logs:CreateLogStream`, `PutLogEvents` | `…/runtimes/*:log-stream:*` (**could write into any agent's logs**) | **Scoped** to `…/runtimes/harness_NorthstarAssist-*:log-stream:*` | A compromised harness could otherwise inject forged entries into other agents' logs, which undermines audit integrity |
| 12 | `CloudWatchLogsPutResourcePolicy` | `…/runtimes/harness_NorthstarAssist-*` | **Kept** | Already scoped to Northstar |
| 13 | `CloudWatchMetricsPublish`: `cloudwatch:PutMetricData` | `*`, with condition namespace `bedrock-agentcore` | **Kept** | Already constrained to the AgentCore metric namespace |
| 14 | `AgentCoreWorkloadIdentity`: `GetWorkloadAccessToken*` | The default directory and `workload-identity/harness_NorthstarAssist-*` | **Kept** | Already scoped to Northstar's own workload identity. It is used by the runtime for outbound authentication. |
| 15 | `AgentCoreBrowserDefault`: `StartBrowserSession`, `ConnectBrowserAutomationStream`, … (7 actions) | `aws:browser/*` | **Removed** | **Browser isn't configured.** Combined with the per-call tool override in `InvokeHarness`, this gave a hijacked agent an internet-capable browser, which is a ready-made exfiltration and SSRF channel. |
| 16 | `AgentCoreCodeInterpreterDefault`: `StartCodeInterpreterSession`, `InvokeCodeInterpreter`, … (5 actions) | `aws:code-interpreter/*` | **Removed** | **Code Interpreter isn't configured.** It would let an attacker run arbitrary code on Northstar's account and budget. |
| 17 | `EFSClientAccess`: `elasticfilesystem:ClientMount`, `ClientWrite` | **Every EFS file system in the account** (through any access point) | **Removed** | No file system is mounted. Write access to every EFS volume in the account has nothing to do with answering policy questions. |
| 18 | `EFSDescribe` | Every file system and access point | **Removed** | Same as #17 |
| 19 | `S3FilesClientAccess`: `s3files:ClientMount`, `ClientWrite`, **`ClientRootAccess`** | **Every S3 Files file system in the account** | **Removed** | Not configured, and root-level write access to shared file systems is especially dangerous |
| 20 | `S3FilesDescribe`: `s3files:GetAccessPoint`, `ListMountTargets` | Every S3 Files file system and access point | **Removed** | Same as #19 |
| 21 | `AgentCoreMemory`: `CreateEvent`, `DeleteEvent`, `GetEvent`, `ListEvents`, `RetrieveMemoryRecords` | `memory/NorthstarAssist-*` | **Removed** | Not configured: the harness has `memory: disabled`. Removing it also prevents silent cross-session persistence (and deletion) of conversation data if memory were added later without review. |
| - | **Guardrail** (`bedrock:ApplyGuardrail`) | Not present in v1 | **Not granted in v2. Added in v3** (2026-10-03) on `guardrail/bzgydako86r9` only | v2 granted nothing, because no guardrail existed. Once the Northstar guardrail was created, v3 granted it on that guardrail alone, and a Deny made it mandatory (section 6). |

### 2.2 Trust policy

| | Before | After |
|---|---|---|
| Principal | `bedrock-agentcore.amazonaws.com` | `bedrock-agentcore.amazonaws.com` (unchanged) |
| `aws:SourceAccount` | `911470903119` | `911470903119` (unchanged) |
| `aws:SourceArn` (ArnLike) | `arn:aws:bedrock-agentcore:us-east-1:911470903119:*`, meaning **any AgentCore resource in the account** | `…:harness/NorthstarAssist-yH4PMorNwm*` and `…:runtime/harness_NorthstarAssist-4tSgy4Clrq*` |
| Rationale | | Confused-deputy protection. Without it, anyone who can create an AgentCore runtime or harness in the account could point it at this role and inherit Northstar's model and gateway access. |

### 2.3 Unchanged: `AmazonBedrockAgentCoreHarnessGatewayPolicy_0vzcg`

Allows `bedrock-agentcore:InvokeGateway` on `gateway/northstar-assist-gateway-bkdy1kxxxm` only. This already meets the requirement that the harness can invoke only our gateway.

------------------------------------------------------------------------

## 3. Gateway Service Role: Before vs After

`arn:aws:iam::911470903119:role/service-role/AmazonBedrockAgentCoreGatewayDefaultServiceRole1790959690216`

### 3.1 `AmazonBedrockAgentCoreGatewayKBAccessProd_3C50B7`

| # | Original statement (v1) | Original scope | Change in v2 | Rationale |
|---|---|---|---|---|
| 1 | `AllowBedrockGetKnowledgeBaseFromKnowledgeBase`: `bedrock:GetKnowledgeBase` | `knowledge-base/ZCAWWBRBXU` | **Kept** (merged into `ReadAndRetrieveNorthstarKnowledgeBaseOnly`) | Already scoped. The connector reads the KB configuration. |
| 2 | `AllowBedrockRetrieveFromKnowledgeBase`: `bedrock:Retrieve` | `knowledge-base/ZCAWWBRBXU` | **Kept** (merged) | Already scoped. This is the gateway's only job. |
| 3 | `AllowBedrockAgenticRetrieveFromKnowledgeBase`: `bedrock:AgenticRetrieveStream` | **`*` (every knowledge base in the account)** | **Scoped** to `knowledge-base/ZCAWWBRBXU` | This was a side door around statements 1 and 2. A misconfigured or added gateway target could use the agentic retrieve API to read **any** knowledge base in the account through this role. It is kept, scoped, because the managed-search connector may use it. |
| 4 | `AllowBedrockInvokeModelForKnowledgeBase`: `bedrock:InvokeModel`, `InvokeModelWithResponseStream` (only when `aws:CalledVia = bedrock.amazonaws.com`) | **Every foundation model in every Region, plus every inference profile, provisioned model and custom model in the account** | **Scoped** to `InvokeModel` on `foundation-model/amazon.titan-embed-text-v2:0` in `us-east-1` only, keeping the `CalledVia` condition | The only model needed on the retrieval path is the KB's embedding model, to embed the query. Streaming isn't supported by Titan Embeddings, so it is removed. |
| 5 | `AllowBedrockRerankForKnowledgeBase`: `bedrock:Rerank` | `*` | **Removed** | Reranking isn't configured in the target's `retrievalConfiguration` |
| 6 | `AllowBedrockGetInferenceProfileForKnowledgeBase`: `bedrock:GetInferenceProfile` | Every inference profile in the account | **Removed** | The KB embeds with a foundation-model ARN, not an inference profile |
| 7 | `AllowBedrockApplyGuardrailForKnowledgeBase`: `bedrock:ApplyGuardrail` | **Every guardrail in the account** | **Removed** | No guardrail is applied on the retrieval path. If one is added later, grant it on that single guardrail ARN. |

### 3.2 `AmazonBedrockAgentCoreGatewayBasePolicyProd_7C8E46`

| Statement | Before | After | Rationale |
|---|---|---|---|
| `GetGateway` | `gateway/northstar-assist-gateway-*` | `gateway/northstar-assist-gateway-bkdy1kxxxm` | A name wildcard covers any future gateway that reuses the prefix |
| `GetConfigurationBundleVersion` | `configuration-bundle/*` (same account and Region condition) | Unchanged | Needed by the gateway runtime, and already conditioned to this account and Region |

### 3.3 Trust policy

| | Before | After |
|---|---|---|
| `aws:SourceArn` (ArnLike) | `…:gateway/northstar-assist-gateway-*` | `…:gateway/northstar-assist-gateway-bkdy1kxxxm` |
| Rationale | | A new gateway created with a look-alike name (for example `northstar-assist-gateway-evil`) could otherwise assume this role and read the Northstar KB |

------------------------------------------------------------------------

## 4. Attacker's View: Original vs Scoped Roles

The realistic ways to gain control of these roles' permissions are:
- **A:** a direct or indirect prompt injection that hijacks the agent loop (threat model E-01, T-01).
- **B:** a caller using the per-call `InvokeHarness` override to supply its own model, system prompt and tools (E-02).
- **C:** another AgentCore resource in the account assuming the role (a confused deputy).

| Attacker goal | With the original roles | With the scoped roles |
|---|---|---|
| Run any model on Northstar's bill (for example an expensive frontier model, or a custom or imported model planted in the account) | **Possible.** Every foundation model in every Region, every inference profile, and every custom, imported or provisioned model in the account | **Blocked.** Only Haiku 4.5 through the global profile. Direct foundation-model calls without the profile are denied too. |
| Turn the agent into a web-browsing exfiltration tool (override tools to add AgentCore Browser) | **Possible.** The role could start and drive Browser sessions | **Blocked.** No Browser permissions |
| Run arbitrary code (add Code Interpreter) | **Possible** | **Blocked** |
| Read or tamper with shared file systems | **Possible.** Mount and write any EFS volume, and root write on any S3 Files file system in the account | **Blocked** |
| Persist or erase conversation data in AgentCore Memory | **Possible** (`memory/NorthstarAssist-*`) | **Blocked** |
| Use bearer-token inference or mint STS bearer tokens for arbitrary services | **Possible** (`*`) | **Blocked.** Only an ECR Public token |
| Forge or pollute other agents' runtime logs | **Possible.** Write to any `/aws/bedrock-agentcore/runtimes/*` group | **Blocked.** Only Northstar's own group |
| Read a different knowledge base through the gateway (for example by adding a gateway target, or by abusing agentic retrieve) | **Possible** via `AgenticRetrieveStream` on `*` | **Blocked.** Every retrieval action is pinned to `ZCAWWBRBXU` |
| Use the gateway role to call other models or apply or probe guardrails | **Possible** (with `CalledVia` Bedrock) | **Blocked.** Only Titan V2 embeddings |
| Have another agent in the account assume the harness role | **Possible.** `SourceArn` was `…:*` | **Blocked.** Only the NorthstarAssist harness and its runtime |
| Read the Northstar KB through the agent | Possible | **Still possible.** This is the system's purpose. Restricting *who* can call `InvokeHarness` and *what* the KB contains is handled outside these roles (see section 7). |

**Bottom line.** Before the change, a successful injection or harness override could turn Northstar Assist into a general-purpose, internet-connected, code-executing agent with access to any model and to shared file systems. After the change, the worst case is limited to what the intended design already allows: calling Haiku 4.5 and retrieving from the Northstar knowledge base.

------------------------------------------------------------------------

## 5. Verification

### 5.1 Policy evaluation: 31 cases, before vs after

The IAM policy simulator (`iam:SimulateCustomPolicy`) is denied in the Cloud Lab account. The same test matrix was therefore evaluated against the **exact JSON documents** in `before/` and `after/`, using a local evaluator. It implements IAM's Allow, Action, Resource (segment-wise ARN wildcard) and Condition (`StringEquals`, `StringLike`, `ArnLike`, `ForAnyValue:StringEquals`) semantics, which are the only features these policies use. Full results are in `policy-evaluation-results.json`.

| ID | Test | Before | After | Expected |
|---|---|---|---|---|
| H1 | Invoke Haiku 4.5 global profile | allowed | **allowed** | ✅ allowed |
| H2 | Invoke Haiku FM (global ARN) via the profile | allowed | **allowed** | ✅ allowed |
| H3 | Invoke Haiku FM in us-west-2 via the profile (cross-Region routing) | allowed | **allowed** | ✅ allowed |
| H4 | Invoke Haiku FM directly, without the profile | allowed | **denied** | ✅ denied |
| H5 | Invoke a different model (Claude Opus 4.1) | allowed | **denied** | ✅ denied |
| H6 | Invoke another inference profile in the account | allowed | **denied** | ✅ denied |
| H7 | Invoke a custom or imported model in the account | allowed | **denied** | ✅ denied |
| H8 | Invoke the Northstar gateway | allowed | **allowed** | ✅ allowed |
| H9 | Invoke any other gateway | denied | **denied** | ✅ denied |
| H10 | Start a Code Interpreter session | allowed | **denied** | ✅ denied |
| H11 | Start a Browser session | allowed | **denied** | ✅ denied |
| H12 | Mount and write an EFS file system | allowed | **denied** | ✅ denied |
| H13 | Write to an S3 Files file system | allowed | **denied** | ✅ denied |
| H14 | Write AgentCore Memory events | allowed | **denied** | ✅ denied |
| H15 | Bedrock Mantle bearer-token call | allowed | **denied** | ✅ denied |
| H16 | Get an STS bearer token for another service | allowed | **denied** | ✅ denied |
| H17 | Write logs to its own runtime log group | allowed | **allowed** | ✅ allowed |
| H18 | Write logs to another agent's runtime log group | allowed | **denied** | ✅ denied |
| G1 | Retrieve from the Northstar KB | allowed | **allowed** | ✅ allowed |
| G2 | Get the Northstar KB | allowed | **allowed** | ✅ allowed |
| G3 | Agentic retrieve from the Northstar KB | allowed | **allowed** | ✅ allowed |
| G4 | Retrieve from any other KB | denied | **denied** | ✅ denied |
| G5 | Agentic retrieve from any other KB | allowed | **denied** | ✅ denied |
| G6 | Embed the query with Titan V2 (via Bedrock) | allowed | **allowed** | ✅ allowed |
| G7 | Invoke Claude Opus 4.1 (via Bedrock) | allowed | **denied** | ✅ denied |
| G8 | Invoke a custom model (via Bedrock) | allowed | **denied** | ✅ denied |
| G9 | Apply any guardrail in the account | allowed | **denied** | ✅ denied |
| G10 | Rerank | allowed | **denied** | ✅ denied |
| G11 | Read any inference profile | allowed | **denied** | ✅ denied |
| G12 | Get its own gateway | allowed | **allowed** | ✅ allowed |
| G13 | Get a look-alike `northstar-assist-gateway-*` | allowed | **denied** | ✅ denied |

**Result: 31/31 pass.** Every legitimate path stays allowed, and **19 over-broad paths that were allowed before are now denied**.

### 5.2 Live functional tests (after the change)

| Test | Method | Result |
|---|---|---|
| Gateway → KB retrieval under the scoped gateway role and trust policy | A SigV4-signed MCP `tools/list` and `tools/call` to `https://northstar-assist-gateway-bkdy1kxxxm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`, query `"hybrid work policy"` | ✅ The tool `northstar-kb___Retrieve` is listed. The call returns `isError: false` with chunks citing `company_policies_handbook.html`. Repeated 4 times over several minutes after the change, all successful. |
| Harness assumes the scoped role and passes the IAM check for the model | `InvokeHarness` with a new session ID | ⚠️ **Partially verified on 2026-10-02.** The call reached `ConverseStream` and failed with the **same AWS Marketplace subscription error seen before any change**, which showed the role was assumed and the model grant passed IAM. A full answer couldn't be produced, because the lab account couldn't activate Claude Haiku 4.5 for any identity at the time. |
| Full end-to-end answer under the scoped roles | `InvokeHarness`: "What is Northstar's hybrid work policy? Name the source document." | ✅ **Verified on 2026-10-03**, once the Marketplace issue had resolved. The harness called `Retrieve` through the gateway, answered from `company_policies_handbook.html` and ended with `end_turn`, all under the scoped harness and gateway roles (guardrail test E1 in `guardrail/harness-e2e-results.json`). No IAM permission was missing, including the removed Bedrock Mantle statements. |

**Earlier blocker, now resolved.** Claude Haiku 4.5 needs an account-level AWS Marketplace subscription. On 2026-10-02 no principal in the lab account could create it, so every Haiku call failed regardless of IAM. By 2026-10-03 the subscription was active, and the end-to-end check above passed.

------------------------------------------------------------------------

## 6. Guardrail Permissions (applied 2026-10-03)

The Northstar guardrail (`bzgydako86r9`) was created and attached in the next task (see `../guardrail/Northstar Assist Safety Controls.md`). Two changes were made to the harness role:

- **Policy v3** of `AmazonBedrockAgentCoreHarnessExecutionPolicy_5o3kt` adds `ApplyNorthstarGuardrailOnly`, which allows `bedrock:ApplyGuardrail` on `guardrail/bzgydako86r9` and `guardrail/bzgydako86r9:*` only. The `after/` file shows v3.
- **Inline Deny `NorthstarRequireGuardrail`** (`after/harness-role.NorthstarRequireGuardrail.inline.json`) denies `bedrock:InvokeModel*` unless `bedrock:GuardrailIdentifier` is this guardrail (`ArnNotLike`). A per-call `InvokeHarness` model override without the guardrail ran unguarded before this Deny, and fails with `AccessDeniedException` after it.

```json
{
  "Sid": "ApplyNorthstarGuardrailOnly",
  "Effect": "Allow",
  "Action": "bedrock:ApplyGuardrail",
  "Resource": [
    "arn:aws:bedrock:us-east-1:911470903119:guardrail/bzgydako86r9",
    "arn:aws:bedrock:us-east-1:911470903119:guardrail/bzgydako86r9:*"
  ]
}
```

------------------------------------------------------------------------

## 7. What These Changes Don't Cover

These items are outside the two service roles. They remain open in the threat model.

- **Who may call `InvokeHarness`** (S-01, E-02). The per-call model, prompt and tool override is still available to any principal with `bedrock-agentcore:InvokeHarness`. The scoped role now limits *what an override can do*, but `InvokeHarness` should also be restricted to the client app's dedicated role.
- **`allowedTools: ["*"]` on the harness.** Pin it to the Retrieve tool so that new gateway targets aren't exposed automatically.
- **What the KB contains** (I-01). Least privilege on roles doesn't stop authorized retrieval of PII. Fix that with data minimization or document-level access control.
- **Remaining wildcard resources.** `ecr:GetAuthorizationToken`, `ecr-public:GetAuthorizationToken`, the X-Ray actions and `logs:DescribeLogGroups` stay on `*` or `log-group:*`. These APIs don't support narrower resources (or only expose metadata), and they give no data access by themselves.
- **Console regeneration.** Editing the harness or gateway in the console may regenerate or reattach "default" policies. Re-check these roles after any console change.

------------------------------------------------------------------------

## 8. Rollback

Each policy keeps its original version as `v1`, and the original trust policies are saved in `before/`. Run these from the `iam-least-privilege` folder.

```bash
P=arn:aws:iam::911470903119:policy/service-role
# Remove the mandatory-guardrail Deny first: v1 has no ApplyGuardrail grant, so with the Deny
# still in place every model call would be refused.
aws iam delete-role-policy --role-name AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869 --policy-name NorthstarRequireGuardrail
aws iam set-default-policy-version --policy-arn $P/AmazonBedrockAgentCoreHarnessExecutionPolicy_5o3kt  --version-id v1
aws iam set-default-policy-version --policy-arn $P/AmazonBedrockAgentCoreGatewayKBAccessProd_3C50B7  --version-id v1
aws iam set-default-policy-version --policy-arn $P/AmazonBedrockAgentCoreGatewayBasePolicyProd_7C8E46 --version-id v1
aws iam update-assume-role-policy --role-name AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869 \
  --policy-document file://before/harness-role.trust-policy.json
aws iam update-assume-role-policy --role-name AmazonBedrockAgentCoreGatewayDefaultServiceRole1790959690216 \
  --policy-document file://before/gateway-role.trust-policy.json
```
