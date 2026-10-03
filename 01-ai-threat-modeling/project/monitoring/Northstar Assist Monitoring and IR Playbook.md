# Northstar Assist: Monitoring Plan and Incident Response Playbook

| Field | Value |
|---|---|
| System | Northstar Assist (harness `NorthstarAssist-yH4PMorNwm`, runtime `harness_NorthstarAssist-4tSgy4Clrq`, guardrail `bzgydako86r9` v1, gateway `northstar-assist-gateway-bkdy1kxxxm`, KB `ZCAWWBRBXU`) |
| Account / Region | `911470903119` / `us-east-1` |
| Owner | Samuel H. Mariam (system owner) |
| Last updated | 2026-10-03 |
| Deployed monitoring | 11 metric filters (namespace `NorthstarAssist`), 1 Contributor Insights rule, 11 alarms, SNS topic `northstar-assist-security-alerts`, dashboard `NorthstarAssist-Security`, 11 saved Logs Insights queries (folder **NorthstarAssist**). All are created by `deploy_monitoring.py` in this folder, and every filter pattern and query was tested against real Northstar logs (section 6). |

**Part A** is the monitoring plan: what to collect, what normal looks like, and what alerts. **Part B** is the playbook PB-01 for a suspected prompt injection.

------------------------------------------------------------------------

# Part A: Monitoring Plan

## A1. Log and Metric Sources

Each source below was inspected in the live account, and the "Verified contents" column describes what the source actually records, not what the documentation suggests.

| # | Source | Where | Verified contents | Security use | Limits |
|---|---|---|---|---|---|
| S1 | **Bedrock model invocation logs** | The account's model invocation log group. Look up its name with `aws bedrock get-model-invocation-logging-configuration --query loggingConfig.cloudWatchConfig.logGroupName --output text`. | **One `ConverseStream` record per model turn.** A question normally produces 2 records: a `tool_use` turn and an `end_turn` answer. Each record has the full `input.inputBodyJson.messages` (user text, `toolUse` with the retrieval query, `toolResult` with every retrieved chunk and its S3 URI), `system` (the system prompt), `toolConfig`, `inputTokenCount` and `outputTokenCount`, `stopReason`, `inferenceRegion`, and **`output.outputBodyJson.trace.guardrail`** (`inputAssessment` and `outputAssessments`, recording which policy fired and with what action). The identity is `identity.arn = …:assumed-role/AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869/BedrockAgentCore-<uuid>`, where **`<uuid>` identifies one harness runtime session**. It is stable across all turns of that session, but **it is not the client's `runtimeSessionId`.** Each retrieval also writes a separate **`InvokeModel` record for Titan V2** under `…/AmazonBedrockExecutionRoleForKnowledgeBase_6s5f0/MANAGED_KB_EMBED-911470903119-ZCAWWBRBXU`, with the **retrieval query text** in `input.inputBodyJson.inputText`. | Main forensic source: what was asked, retrieved and answered, and what the guardrail did. Also the source of all AI-specific metric filters. | Contains PII from retrieved chunks and blocked answers. The group is shared at account level and has no retention limit, so restrict access to it (ML-BOM F-09). There is no end-user identity in it. |
| S2 | **Harness runtime log** | `/aws/bedrock-agentcore/runtimes/harness_NorthstarAssist-4tSgy4Clrq-DEFAULT`, streams `…[runtime-logs]…` and `otel-rt-logs` | JSON lines with **`sessionId` (equal to the client's `runtimeSessionId`)**, `requestId`, `level`, `message`. Messages cover request start ("Returning streaming response"), credential loading, MCP protocol negotiation, the tool filter ("allowedTools filter: wildcard"), the conversation window, warnings and errors. `otel-rt-logs` adds `otelTraceID` and `otelSpanID`. **No prompts, answers, tool arguments or token counts.** | The only place the client session ID appears, which makes it the link from an attack to `StopRuntimeSession` and to the client app. Also shows runtime errors. | Mostly container noise. It can't be joined to S1 by ID, only **by timestamp** (section A3). |
| S3 | **KB application log** | `/aws/vendedlogs/bedrock/knowledge-base/APPLICATION_LOGS/ZCAWWBRBXU` | Log delivery is configured (delivery source `WdDeliverySource-515363508`), but the group **contains no events**, including none for the 2026-10-02 ingestion job that ran after it was created. Retrieval at query time isn't logged here. | Intended for ingestion and sync events (document added, deleted or failed) | **Gap.** Until events appear, use `aws bedrock-agent list-ingestion-jobs` (A2, row 14). |
| S4 | **Guardrail metrics** `AWS/Bedrock/Guardrails` | CloudWatch metrics | `Invocations`, `InvocationsIntervened`, `InvocationLatency`, `TextUnitCount`, by `GuardrailArn`+`GuardrailVersion` (totals only), or by `GuardrailPolicyType` / `GuardrailContentSource` / `Operation=ApplyGuardrail` (**account-wide, not per guardrail**) | Trends and capacity | **There is no `PROMPT_ATTACK` dimension**: prompt attacks are counted inside `ContentPolicy` with hate, violence and so on. The per-policy series also include other guardrails in the account. Northstar's prompt-attack alerting therefore uses metric filters on S1. |
| S5 | **AgentCore runtime and gateway metrics** `AWS/Bedrock-AgentCore` | CloudWatch metrics | Runtime: `Invocations`, `Sessions`, `SystemErrors`, `UserErrors`, `Throttles`, `Latency` with `Name=harness_NorthstarAssist::DEFAULT`, `Operation=InvokeAgentRuntime`. Gateway tool: the same metrics with `Name=northstar-kb___Retrieve`, `Operation=InvokeGateway`, `Method=tools/call` | Availability, plus **retrieval failures** (tool errors) | Delayed by a few minutes |
| S6 | **Model metrics** `AWS/Bedrock` | CloudWatch metrics, `ModelId=global.anthropic.claude-haiku-4-5-20251001-v1:0` | `Invocations`, `InputTokenCount`, `OutputTokenCount`, `InvocationLatency`, `InvocationClientErrors`, `EstimatedTPMQuotaUsage` | Cost, quota and volume | Covers every caller of the model, not just the harness |
| S7 | **Harness OTel metrics** `bedrock-agentcore` | CloudWatch metrics | `strands.tool.call_count`, `strands.tool.success_count`, `gen_ai.client.token.usage`, `strands.event_loop.cycle_count` | Tool-use and agent-loop behaviour (for example runaway loops) | Dimensions are per cycle or per model, so they suit dashboards more than alarms |
| S8 | **KB and S3 state** | `aws bedrock-agent list-ingestion-jobs`, `aws s3api list-object-versions` | Ingestion statistics (scanned, indexed, deleted, failed) and object versions with timestamps | Detect and scope knowledge base tampering (T-01) | **S3 server access logging is off, and CloudTrail is denied in the Cloud Lab**, so the uploader can't be identified (R-02) |
| S9 | **CloudTrail** | Not available (`cloudtrail:LookupEvents` is denied in the lab) | n/a | In production: identify who called `InvokeHarness`, who changed IAM, guardrail or harness settings, and who wrote to S3 | **Gap**: no caller identity for direct API abuse |
| S10 | **CloudWatch GenAI Observability / Transaction Search** | Not available in the Cloud Lab | n/a | In production: end-to-end traces linking session → model call → tool call | **Gap**. The saved queries in A4 stand in for it. |
| S11 | **Client app (Streamlit) log** | Not implemented | n/a | Should record the authenticated user, `runtimeSessionId`, time and decision for each request | **Gap**: without it, no attack can be attributed to a person (threat model R-01) |

## A2. Baseline: What Normal Looks Like

These figures were measured from Northstar's own invocation logs with Logs Insights over the testing period. It is a small lab sample, so re-baseline after 30 days of real use.

| Measure | Observed | Note |
|---|---|---|
| Model calls per question | 2 (`tool_use` then `end_turn`), 3–4 if the model searches twice | A normal answer is always preceded by a Retrieve call |
| KB retrievals (Titan embed records) per answer | ≈ 1.0–2.0 | An answer with **no** retrieval is abnormal, because the system prompt says "always search" |
| Output tokens per answer (`end_turn`) | avg **161**, max **207** | `tool_use` turns: avg 85, max 95 |
| Input tokens per call | `end_turn` avg 3,348, max 3,918. Overall max **7,925** | Grows with session history (sliding window of 150 messages) |
| Retrieved chunks per Retrieve | Always 5 (`numberOfResults = 5`) | **0 chunks never happens normally**: it means the KB is empty, broken or wiped (D-02) |
| Guardrail interventions | Only in deliberate tests | In production, expect a small number of PII masks (emails and phone numbers in answers) and occasional false positives |
| Inference Region | `ap-southeast-4` and others (global profile) | Expected with the global profile, but note it for data residency (F-05) |

## A3. How to Correlate the Sources

No single ID links all the sources, so analysts follow this chain:

```
Alarm ─▶ Contributor Insights / query 01 gives the session key  BedrockAgentCore-<uuid>        (S1)
      ─▶ query 02 (session timeline): every turn, answer and token count for <uuid>, with timestamps
      ─▶ query 10 on the runtime log for the same minutes: the client runtimeSessionId (S2)
           (match on time: the runtime "Returning streaming response" line comes about 1 s
            before the first ConverseStream record of each request)
      ─▶ StopRuntimeSession(runtimeSessionId) to contain; client app log to find the user (gap S11)
      ─▶ query 08 for the same minutes: the retrieval queries the session sent to the KB (S1, KB role)
```

This was verified on a traced test request. Client session `c8418565-6738-4c6a-baa4-e8befab6d484` logged its runtime request at 06:41:21.574 UTC, and the matching invocation records (`BedrockAgentCore-848a69f1…`) are at 06:41:21 and 06:41:24, with the Titan retrieval for "standard working hours" at 06:41:24.

## A4. AI-Specific Signals and Alerts (deployed)

All alarms notify the SNS topic `northstar-assist-security-alerts`. `TreatMissingData = notBreaching`, so quiet periods don't page anyone. The severity in each alarm description tells the on-call analyst how fast to respond (B1).

### A4.1 Guardrail interventions

| ID | Signal | Implementation | **Alert condition** | Sev | Why this threshold |
|---|---|---|---|---|---|
| **AL-1** | **PROMPT_ATTACK blocks from one session** | Contributor Insights rule `northstar-assist-prompt-attacks-by-session` on S1: key `$.identity.arn` (one session), filter harness role + `inputAssessment.bzgydako86r9.contentPolicy.filters[0].type = PROMPT_ATTACK`. Alarm `northstar-assist-prompt-attack-single-session` on `INSIGHT_RULE_METRIC(rule, 'MaxContributorValue')`, period 1 h. | **ALARM when one session has more than 5 PROMPT_ATTACK blocks in 1 hour** | SEV-2 | One or two blocks can be a curious employee or a false positive (prompt-attack detection is at HIGH). Six or more in one session is deliberate, repeated probing. In testing, a legitimate user produced 0. |
| AL-2 | PROMPT_ATTACK blocks across all sessions | Metric filter `PromptAttackBlocked` (checks content-filter positions 0–2) → alarm `northstar-assist-prompt-attack-burst` | **Sum > 10 in 15 minutes** | SEV-2 | Catches an attacker who rotates sessions to stay under AL-1, or several users running the same jailbreak at once |
| AL-3 | **Guardrail missing (bypass)** | Metric filter `GuardrailMissing`: harness `ConverseStream` record with **no** `trace.guardrail` → alarm `northstar-assist-guardrail-missing` | **Any (≥ 1) in 5 minutes** | **SEV-1** | The IAM Deny `NorthstarRequireGuardrail` should make this impossible, so a hit means the Deny was removed or bypassed. The filter correctly matched the one unguarded override sent in testing before the Deny existed. |
| AL-4 | Denied-topic blocks on input | Metric filter `TopicBlockedInput` → alarm `northstar-assist-topic-blocks` | **Sum > 10 in 1 hour** | SEV-3 | Repeated attempts at bulk data, impersonation or security-bypass content: misuse or harvesting (E-03, I-01) |
| AL-5 | Answers withheld by the output guardrail | Metric filter `OutputBlocked` (answer text = blocked-output message) → alarm `northstar-assist-output-blocked` | **Sum > 5 in 1 hour** | SEV-3 | Output blocks mean the model *did* produce restricted content (PII, secrets, a remote image). Repeats suggest someone is drawing data out, or that a poisoned document is being retrieved (T-01, I-03). |

### A4.2 Retrieval anomalies

| ID | Signal | Implementation | **Alert condition** | Sev | Why |
|---|---|---|---|---|---|
| AL-6 | **Answers without a KB retrieval** | Metric filters `Answers` (`end_turn`) and `KbRetrievals` (Titan embed under the KB role) → alarm `northstar-assist-answers-without-retrieval` on `IF(answers ≥ 10, retrievals / answers, 1)` | **Ratio < 0.8 over 1 hour, with at least 10 answers** | SEV-3 | Baseline ≥ 1.0. Answers produced without searching are ungrounded: a jailbreak that suppressed the tool, an override, or the model answering from its own knowledge. The ≥ 10 floor avoids noise at low volume. |
| AL-7 | **Retrieve tool failing** | `AWS/Bedrock-AgentCore` `SystemErrors` + `UserErrors` for `northstar-kb___Retrieve` → alarm `northstar-assist-retrieval-tool-errors` | **> 2 errors in 15 minutes** | SEV-3 | Failing retrieval leaves the model with nothing to ground on, and can follow IAM tampering or KB deletion |
| Q-04 | Sessions that answered with **zero** tool calls | Saved query **04** | Hunting query (per session) | – | Per-session detail behind AL-6. It found the unguarded override session `0e0227d4…` in testing. |
| Q-05 | **Zero retrieved chunks** or a tool error result | Saved query **05** (`retrievalResults` is `[]`, or `"status":"error"`) | Hunting query. Treat any hit as **SEV-3** and check the KB (D-02) | – | The KB always returns 5 chunks, so an empty result means it has been emptied or broken |
| Q-08 | Retrieval queries sent to the KB | Saved query **08** (Titan embed `inputText`) | Investigation | – | Shows *what* the agent searched for, such as "employee emails", "password" or "all customers". Harvesting shows up here even when the answers are masked. |

### A4.3 Token anomalies

| ID | Signal | Implementation | **Alert condition** | Sev | Why |
|---|---|---|---|---|---|
| AL-8 | Output-token spike | Metric filter `OutputTokens` (value = `$.output.outputTokenCount`) → alarm `northstar-assist-output-token-spike`, statistic **Maximum** | **Any single call > 1,000 output tokens (5 min)** | SEV-3 | About 5× the largest normal answer (207) and about 6× the average. Long outputs signal bulk dumps ("print every document"), jailbreak essays, or a system-prompt or context leak. |
| AL-9 | Input-token spike | Metric filter `InputTokens` → alarm `northstar-assist-input-token-spike` (Maximum) | **Any single call > 20,000 input tokens (5 min)** | SEV-3 | About 2.5× the observed maximum (7,925). It points to context stuffing (a huge pasted payload), a runaway loop, or very long sessions being used to wear down the instructions. |
| Q-06 | **Above the session's own average** | Saved query **06**: per session, `max(output) > 3 × median(output)` with ≥ 3 calls, or the absolute limits above | Hunting query (run daily, and during every incident) | – | Implements "responses significantly above the session average". The median is used because the average includes the outlier itself. |
| AL-10 | Model call volume (cost / automation) | Metric filter `ModelCalls` → alarm `northstar-assist-model-call-volume` | **> 600 harness model calls in 1 hour** | SEV-3 | About 2–3 calls per question, so 600 calls is about 250 questions an hour, well above expected internal use. It catches scripted abuse and denial of wallet (D-01). |

### A4.4 Platform health

| ID | Signal | Alert condition | Sev |
|---|---|---|---|
| AL-11 | Harness runtime `SystemErrors` + `UserErrors` (`AWS/Bedrock-AgentCore`, `InvokeAgentRuntime`) → `northstar-assist-harness-errors` | **> 5 in 15 minutes** | SEV-3 |
| – | KB ingestion jobs (`list-ingestion-jobs`): `numberOfDocumentsDeleted > 0`, `numberOfDocumentsFailed > 0`, or a job nobody scheduled | Daily check until S3 log delivery works. **Any unplanned job → SEV-2** (possible KB poisoning) | SEV-2/3 |

### A4.5 Saved Logs Insights queries (CloudWatch > Logs > Logs Insights > **Saved queries** > NorthstarAssist)

| # | Query | Log group | Used in |
|---|---|---|---|
| 01 | Prompt-attack blocks by session | invocation log | Triage (B3) |
| 02 | Session timeline (edit `SESSION_UUID`) | invocation log | Investigation (B6) |
| 03 | Guardrail interventions by policy, per hour | invocation log | Triage and scope |
| 04 | Sessions that answered without KB retrieval | invocation log | Success check |
| 05 | Zero-chunk or failed retrievals | invocation log | Retrieval anomaly |
| 06 | Token outliers vs session median | invocation log | Success check |
| 07 | Model calls without the guardrail (bypass) | invocation log | SEV-1 check |
| 08 | Retrieval queries sent to the KB | invocation log | Investigation |
| 09 | Runtime log for a client session (edit `RUNTIME_SESSION_ID`) | runtime log | Containment |
| 10 | Client sessions active in a time window | runtime log | Correlation (A3) |
| 11 | Instruction-like text **inside retrieved chunks** (indirect injection hunt) | invocation log | Direct vs indirect |

The text of every query is in `logs-insights-queries.json`.

## A5. Dashboard and Routing

- **Dashboard:** CloudWatch > Dashboards > **NorthstarAssist-Security**. It shows input guardrail blocks, output blocks and bypass, retrieval vs answers, token maxima, call volume, runtime errors, the **top sessions by PROMPT_ATTACK** (Contributor Insights) and the status of every alarm.
- **Routing:** subscribe the security on-call distribution list to the topic, and confirm the email: `aws sns subscribe --topic-arn arn:aws:sns:us-east-1:911470903119:northstar-assist-security-alerts --protocol email --notification-endpoint <security-oncall@…>`. **No subscriber is configured yet**, so alarms currently change state without notifying anyone.
- **Alert-fatigue controls:** per-session and per-hour thresholds rather than single events, except AL-3, which should never fire. `notBreaching` for missing data. A weekly review of the alarm history, and thresholds re-baselined after 30 days.

## A6. Log Protection and Retention

| Item | Requirement |
|---|---|
| Invocation logs | Dedicated, KMS-encrypted log group readable only by a security role, with **90-day retention**. Today the group is shared with no retention limit (ML-BOM F-09). |
| Runtime and KB logs | 90-day retention |
| Evidence exports | Store in an S3 bucket with versioning (and Object Lock if available), plus SHA-256 hashes (PB-01 step C1) |
| Monitoring config | Kept as code (`deploy_monitoring.py`) and redeployed after any change. Don't edit alarms by hand in the console. |

## A7. Monitoring Gaps

| Gap | Impact | Recommendation |
|---|---|---|
| No end-user identity anywhere (S11) | An attack can be traced to a session but not to a person | SSO in the client, plus an app log with user ID, `runtimeSessionId` and time (threat model S-01, R-01) |
| CloudTrail unavailable in the lab (S9) | Direct `InvokeHarness` abuse, IAM changes and S3 writes can't be attributed | In production: a CloudTrail trail with data events for S3 and AgentCore, plus alerts on IAM, guardrail and harness changes |
| KB application log empty (S3) | Ingestion of poisoned content isn't logged | Check delivery after the next sync. Until then, run the daily `list-ingestion-jobs` check |
| Guardrail doesn't see retrieved chunks | Indirect injection is only detectable after the fact (query 11) | Pre-ingestion scanning (T-01). Run query 11 daily. |
| Grounding isn't evaluated on harness traffic | Hallucinations aren't measured | An app-side `ApplyGuardrail` grounding check |
| Hour-aligned Contributor Insights buckets for AL-1 | An attack that spans a clock-hour boundary can split its count | AL-2 (15-minute window) backs it up |

------------------------------------------------------------------------

# Part B: Incident Response Playbook PB-01, Suspected Prompt Injection

**Definition.** Someone is trying to make Northstar Assist ignore its instructions or guardrail, by typing instructions into a question (**direct** injection) or by planting them in a knowledge base document that the agent retrieves (**indirect** injection). Typical goals: reveal the system prompt, dump personal or customer data, produce content outside its scope, or send users to a phishing or exfiltration URL.

**Who runs this.** The on-call analyst. No prior AI incident experience is needed: every step names the console path or command. Work in **AWS CloudShell** (console top bar > CloudShell icon) or any terminal with AWS CLI v2 and credentials for account `911470903119`.

**Ground rules.**
1. **Preserve evidence before changing anything** (step C1).
2. **Write down every action with its UTC time** in the incident log (B9).
3. **Assume it is worse than it looks** until the investigation shows otherwise.
4. Never paste retrieved PII into tickets or chat. Refer to the evidence file instead.

## B0. Set Up Your Shell (2 minutes, copy and paste)

**CLI version.** You need an AWS CLI recent enough to have the AgentCore **harness** commands (`aws bedrock-agentcore-control get-harness`, `aws bedrock-agentcore stop-runtime-session`). Check with `aws bedrock-agentcore-control get-harness help`. CloudShell's CLI is kept current. Locally, AWS CLI v2 2.28 is **too old**: either update it, or use `pip install --upgrade awscli` and run `python -m awscli …`. On **Windows Git Bash**, also run `export MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf-8`. Otherwise Git Bash rewrites log group names that start with `/aws/…` into Windows paths, and exports fail on non-ASCII text.

```bash
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1
export ACCOUNT=911470903119
export HARNESS_ARN=arn:aws:bedrock-agentcore:us-east-1:911470903119:harness/NorthstarAssist-yH4PMorNwm
export HARNESS_ID=NorthstarAssist-yH4PMorNwm
export RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:911470903119:runtime/harness_NorthstarAssist-4tSgy4Clrq
export HARNESS_ROLE=AmazonBedrockAgentCoreHarnessDefaultServiceRole-p0869
export GUARDRAIL_ID=bzgydako86r9 KB_ID=ZCAWWBRBXU DS_ID=NTXBJ668Z7 BUCKET=northstar-assist-kb-chrst
export INV_LOG=$(aws bedrock get-model-invocation-logging-configuration \
  --query loggingConfig.cloudWatchConfig.logGroupName --output text)
export RT_LOG=/aws/bedrock-agentcore/runtimes/harness_NorthstarAssist-4tSgy4Clrq-DEFAULT
export CASE=IR-$(date -u +%Y%m%d-%H%M); mkdir -p ~/$CASE && cd ~/$CASE
echo "Case $CASE | invocation log: $INV_LOG"; aws sts get-caller-identity --query Arn --output text
```

## B1. Severity

| Sev | Meaning | Examples | Response |
|---|---|---|---|
| **SEV-1** | An attack **succeeded** or the guardrail is **bypassed** | AL-3 fired. The system prompt appears in an answer. Bulk PII or customer data was returned unmasked. Instructions are found inside a retrieved chunk (query 11). | Page the Security Lead now. Containment within 15 minutes. CISO and Privacy notified within 4 hours. |
| **SEV-2** | Active, repeated attack, **no evidence of success yet** | AL-1 or AL-2 fired. Several sessions are using the same jailbreak. | Analyst starts PB-01 within 15 minutes. Security Lead informed within 1 hour. |
| **SEV-3** | Probe or anomaly | 1–5 prompt-attack blocks, AL-4 to AL-11 | Triage within 1 business day. Escalate to SEV-2 if B3 confirms an attack. |

## B2. Detection: What Starts This Playbook

| Signal | Where you see it | Trigger |
|---|---|---|
| Alarm **northstar-assist-prompt-attack-single-session** (AL-1) | SNS email, or CloudWatch > Alarms > All alarms | One session has more than 5 PROMPT_ATTACK blocks in 1 hour |
| Alarm **northstar-assist-prompt-attack-burst** (AL-2) | Same | More than 10 PROMPT_ATTACK blocks in 15 minutes |
| Alarm **northstar-assist-guardrail-missing** (AL-3) | Same | **Any**: go straight to SEV-1 |
| Alarms AL-5 (output blocked), AL-6 (answers without retrieval), AL-8 (output token spike) | Same | Possible *successful* or indirect injection. Run B3 and query 11. |
| User report: "the assistant told me to re-verify my password at a link", "it showed me everyone's emails", "it said something strange" | IT Service Desk ticket | Any. Ask for the **time**, and the exact question if the user still has it. |
| Dashboard **NorthstarAssist-Security** > "Top sessions by PROMPT_ATTACK" | CloudWatch > Dashboards | Any single session standing far above the others |

## B3. Triage: Is This Real? (first 10 minutes)

1. **Open the alarm.** CloudWatch > Alarms > select the alarm > **History**. Note the time it went to ALARM. That is **T0**: write it in the incident log.
2. **Find the sessions involved.** CloudWatch > Logs > **Logs Insights** > **Saved queries** > `NorthstarAssist/01 Prompt-attack blocks by session`. Set the time range to **T0 minus 2 hours to now** and choose **Run query**. Each row is one harness session (`session` = the `BedrockAgentCore-<uuid>` value), with its number of blocks and its first and last time. **Copy the top `session` value** into the incident log as `SESSION_UUID`.

   CLI equivalent:
   ```bash
   QID=$(aws logs start-query --log-group-name "$INV_LOG" --start-time $(date -u -d '-2 hours' +%s) --end-time $(date -u +%s) \
     --query-string 'filter identity.arn like /HarnessDefaultServiceRole-p0869/ and @message like /PROMPT_ATTACK/
     | parse identity.arn "/BedrockAgentCore-*" as session | stats count(*) as blocks, min(@timestamp) as first, max(@timestamp) as last by session
     | sort blocks desc' --query queryId --output text); sleep 10; aws logs get-query-results --query-id $QID --output table
   ```
3. **Read what the session actually sent.** Run saved query `02 Session timeline`, replacing `SESSION_UUID` with the value from step 2 (keep the first 8 characters if you like; it is a regex). Expand each row (the ▸ arrow) and read `input.inputBodyJson.messages` (the user's text) and the `answer`.
4. **Decide.**
   - **Real attack (continue PB-01):** two or more distinct injection phrasings ("ignore previous instructions", "you are now…", "system override", "reveal your instructions"); or injection attempts followed by rephrased questions; or any answer that isn't the blocked-input message after an attempt.
   - **Likely a false positive (close as SEV-3 and record it):** one block whose text is an ordinary work question (prompt-attack detection is at HIGH). Add the prompt to the guardrail false-positive list for the weekly review.
5. **Direct or indirect?** Run saved query `11 Instruction-like text inside retrieved chunks` for the last 7 days.
   - **0 rows, and the injection text is in the user's message:** **direct** injection. Continue with C1–C4.
   - **Any row:** a document in the knowledge base contains instructions. This is **indirect injection and SEV-1**. Do C1, then **C5** first.

## B4. Containment (first 15 minutes)

- [ ] **C1: Preserve the evidence (always first).** Export everything about the session and the attack window *before* any change.
  ```bash
  export SESSION_UUID=<from B3 step 2>
  START=$(date -u -d '-6 hours' +%s000)
  # 1. All model turns of the attacker session (prompts, retrieved chunks, answers, guardrail trace)
  aws logs filter-log-events --log-group-name "$INV_LOG" --start-time $START \
    --filter-pattern "{ \$.identity.arn = \"*BedrockAgentCore-${SESSION_UUID}*\" }" --output json > invocations-session.json
  # 2. Every Northstar model call and KB retrieval in the window (for scope)
  aws logs filter-log-events --log-group-name "$INV_LOG" --start-time $START \
    --filter-pattern '{ $.identity.arn = "*HarnessDefaultServiceRole-p0869*" || $.identity.arn = "*MANAGED_KB_EMBED-911470903119-ZCAWWBRBXU" }' \
    --output json > invocations-window.json
  # 3. Runtime log for the window (gives the client runtimeSessionId)
  aws logs filter-log-events --log-group-name "$RT_LOG" --start-time $START --output json > runtime-window.json
  # 4. Configuration snapshots
  aws bedrock-agentcore-control get-harness --harness-id $HARNESS_ID > harness-config.json
  aws bedrock get-guardrail --guardrail-identifier $GUARDRAIL_ID --guardrail-version 1 > guardrail-v1.json
  aws iam list-role-policies --role-name $HARNESS_ROLE > harness-role-inline.json
  aws iam list-attached-role-policies --role-name $HARNESS_ROLE > harness-role-attached.json
  aws bedrock-agent list-ingestion-jobs --knowledge-base-id $KB_ID --data-source-id $DS_ID > ingestion-jobs.json
  aws s3api list-object-versions --bucket $BUCKET > s3-object-versions.json
  sha256sum *.json > SHA256SUMS && ls -la
  ```
  Console alternative for item 1: run saved query 02 and choose **Export results** > **Download table (CSV)**. CloudShell: **Actions > Download file** to keep a copy off the account.

- [ ] **C2: Stop the attacker's session.** This ends the session's microVM and its conversation memory, so a long jailbreak has to start over.
  1. Get the attack window from `invocations-session.json` (or query 02): the first and last timestamps.
  2. Run saved query `10 Client sessions active in a time window`, with the time range set to that window (±1 minute). The `sessionId` whose `first_request` and `last_request` line up with the attack timestamps is the client **`runtimeSessionId`** (see A3).
  3. Stop it:
  ```bash
  export RUNTIME_SESSION_ID=<sessionId from query 10>
  aws bedrock-agentcore stop-runtime-session --runtime-session-id "$RUNTIME_SESSION_ID" \
    --agent-runtime-arn "$HARNESS_ARN" --qualifier DEFAULT
  ```
  Expect `"statusCode": 200`. **Pass the harness ARN, not the runtime ARN.** The runtime is managed by the harness, and using `$RUNTIME_ARN` fails with `ValidationException … is managed by a harness and cannot be invoked directly`.
  > This doesn't stop the person: they can open a new session. C3 and C4 handle the person and the hole. If the same `runtimeSessionId` is reused after the stop, it gets a **new** harness session with an empty history, so a long multi-turn jailbreak can't simply resume.

- [ ] **C3: Close the guardrail bypass (only if AL-3 fired, or query 07 returns rows after 2026-10-03 06:21 UTC).** Earlier records predate the guardrail or the Deny (they include the deliberate override test at 06:20:04). Check that the mandatory-guardrail Deny is still in place:
  ```bash
  aws iam get-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarRequireGuardrail --query PolicyDocument
  ```
  If the call returns `NoSuchEntity` or a changed document, restore it from the project repo:
  `aws iam put-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarRequireGuardrail --policy-document file://iam-least-privilege/after/harness-role.NorthstarRequireGuardrail.inline.json`.
  Then treat **who removed it** as a separate SEV-1 (IAM compromise).

- [ ] **C4: Block the source.**
  - **Via the Streamlit app** (shared password): change `APP_PASSWORD` in the app host's `.env` and restart the app (`streamlit run app.py`). This logs everyone out. The app can't block one user, because it has no per-user identity (gap S11).
  - **Direct API calls** (the invocation log shows sessions but no app traffic matches): someone holds AWS credentials with `bedrock-agentcore:InvokeHarness`. In production, find the caller in CloudTrail (`eventName = InvokeHarness`) and **deactivate their access keys** (IAM > Users > *user* > Security credentials > **Deactivate**) or revoke the role's sessions (IAM > Roles > *role* > **Revoke active sessions**). In the Cloud Lab, CloudTrail is denied, so escalate to the Security Lead.

- [ ] **C5: Indirect injection: quarantine the poisoned document (SEV-1).**
  1. Find the document: `jq -r '.events[].message' invocations-session.json | grep -o 's3://northstar-assist-kb-chrst/[^\\"]*' | sort | uniq -c`. Cross-check it against the row from query 11.
  2. Copy it into the case folder: `aws s3 cp "s3://$BUCKET/<key>" ./evidence-document`, and keep its versions: `aws s3api list-object-versions --bucket $BUCKET --prefix "<key>" > document-versions.json`
  3. Remove it from the source and re-index. The bucket is versioned, so this is recoverable:
     ```bash
     aws s3 rm "s3://$BUCKET/<key>"
     JOB=$(aws bedrock-agent start-ingestion-job --knowledge-base-id $KB_ID --data-source-id $DS_ID --query ingestionJob.ingestionJobId --output text)
     aws bedrock-agent get-ingestion-job --knowledge-base-id $KB_ID --data-source-id $DS_ID --ingestion-job-id $JOB \
       --query 'ingestionJob.[status,statistics.numberOfDocumentsDeleted]'
     ```
     Wait for `COMPLETE` with `numberOfDocumentsDeleted = 1`. **Until the sync completes, the poisoned chunks are still retrievable.**

- [ ] **C6: Emergency stop, if the attack continues and C2–C5 aren't enough.** Both options cause a **full outage** of Northstar Assist (tested, section 6).

  | Option | Effect (observed in testing) | Command | Undo |
  |---|---|---|---|
  | **K1: cut off the knowledge base** | The harness can't load its gateway tool, so **every request fails** ("Failed to load tool 'northstar-assist-gateway-…'"). The model is never called with KB data, so nothing more can leak. | `aws iam put-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarEmergencyNoRetrieval --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"bedrock-agentcore:InvokeGateway","Resource":"*"}]}'` | `aws iam delete-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarEmergencyNoRetrieval` |
  | **K2: stop all model calls** | Every request fails with `AccessDeniedException … ConverseStream` | `aws iam put-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarEmergencyStop --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],"Resource":"*"}]}'` | `aws iam delete-role-policy --role-name $HARNESS_ROLE --policy-name NorthstarEmergencyStop` |

  Each took effect within 50 seconds, and normal answers returned within 45 seconds of the undo. **Use K2 by default**: its error is unambiguous, and it also stops any per-call override. Use K1 when you need to prove that no further KB data reached the model after a given time. Write the apply and undo times in the incident log.

**Decision point: is a temporary outage acceptable?** Yes. Northstar Assist is a convenience tool, not a business-critical system, and every answer it gives is also available in the source documents. **The Security Lead may order K1 or K2 on their own authority for any SEV-1**, or for a SEV-2 still active after 15 minutes, and informs the System Owner afterwards. For SEV-3, the System Owner decides. During the outage, the IT Service Desk tells employees to use the source documents directly.

## B5. Escalation

**Page the Security Lead immediately if any of these apply:**
- [ ] AL-3 fired, or query 07 shows unguarded calls after 2026-10-03 06:21 UTC
- [ ] Query 11 returns any row (a poisoned document is in the KB)
- [ ] Any answer contains the system prompt text, unmasked email addresses or phone numbers, customer revenue, or a non-Northstar URL
- [ ] The attack continues after C2 (new sessions keep appearing in query 01)
- [ ] The IAM policies or the harness configuration differ from the snapshots in the repo

**Notify the CISO and the Privacy Officer within 4 hours if:**
- [ ] Personal data (employee or customer contacts, training scores) or commercially sensitive data was **shown** to a user who shouldn't have it. That may start a regulatory notification clock (for example GDPR's 72 hours).
- [ ] A phishing or exfiltration URL reached users (T-01, I-03)
- [ ] The attacker used AWS credentials directly (an internal credential compromise)

## B6. Investigation (first hour)

Work through these checks for each attacker session (`SESSION_UUID`), using query 02 unless stated.

| # | Question | How to check | What "attacker success" looks like |
|---|---|---|---|
| I-1 | **Did any attempt get through?** | Query 02: look at every turn after the first injection attempt | A turn ending `end_turn` whose `answer` isn't the blocked-input message ("Northstar Assist can't help with that request…") and that follows or answers an injection-style prompt |
| I-2 | **Was the system prompt leaked?** | Run this in Logs Insights (invocation log): `filter output.outputBodyJson.output.message.content.0.text like /internal employee assistant\|Base your answers only\|Do not discuss topics unrelated/` | Any row. These phrases come from the system prompt and should never appear in an answer. |
| I-3 | **Was data harvested through retrieval?** | Query 08 for the attack window | Searches such as "employee directory", "all emails", "customer revenue", "password" or "API key", or many different people's names in sequence |
| I-4 | **Did restricted content reach the output?** | Query 03 for the window, plus the `trace.guardrail.outputAssessments` of each turn in `invocations-session.json` | Output blocks or masks. Masked means the data existed in context, and blocked means the model produced it. Check that no answer contains raw `@northstartech.com` addresses: `grep -c '@northstartech.com' invocations-session.json` counts **any** occurrence, including retrieved chunks, so read the answer fields to confirm. |
| I-5 | **Was the guardrail bypassed?** | Query 07 | Any row in the window |
| I-6 | **Answers without retrieval, or unusually long answers?** | Queries 04 and 06 | The attacker's session appears in either. Ungrounded or bulk output is likely. |
| I-7 | **Was it indirect?** | Query 11 (last 30 days) | Any row. Identify the document (C5) and find **every** session that retrieved it: `filter @message like /<document-key>/ \| parse identity.arn "/BedrockAgentCore-*" as session \| stats count(*) by session` |
| I-8 | **Scope: one attacker or many?** | Query 01 over the **last 7 days**, plus query 10 for the window | More than one session with blocks, or the same jailbreak text in several sessions. Count distinct client `sessionId`s. |
| I-9 | **Who is it?** | The client app log (not yet implemented, gap S11); in production CloudTrail `InvokeHarness` | Without the app log, record "user unknown". This is itself a finding for the post-incident review. |

**Classify the outcome** in the incident log as one of: *Attempted, blocked* (I-1 to I-7 all negative) · *Partial* (masked data in context, or off-scope content shown) · *Successful* (any of I-1, I-2, I-5 or I-7 positive, or unmasked sensitive data shown). *Partial* and *Successful* are SEV-1.

## B7. Eradication and Recovery

- [ ] **R1: Close the hole that worked.**
  - *New jailbreak phrasing got through:* add the pattern to the guardrail (for example as a word filter, or by tightening a denied topic) in `guardrail/northstar-guardrail-config.json`. Then run `python deploy_guardrail.py --version`, then `python test_guardrail.py bzgydako86r9 <new version>` (all 39 core cases must pass), then `python attach_guardrail.py <guardrail ARN> <new version>`. The IAM Deny allows any version of this guardrail (`…:guardrail/bzgydako86r9:*`), so no IAM change is needed.
  - *Indirect injection:* fix the document, or restore its previous version (`aws s3api copy-object --bucket $BUCKET --key <key> --copy-source "$BUCKET/<key>?versionId=<good version>"`), re-sync (C5), and add the payload to the pre-ingestion scanning rules.
  - *Bypass:* restore the Deny (C3), and investigate the IAM change.
- [ ] **R2: Lift the emergency controls (if used).** Run the C6 undo command, and note the time.
- [ ] **R3: Verify.** From the repo (with credentials):
  - `python guardrail/test_harness_e2e.py`: E1 must answer, E2 to E4 must be blocked, and E5 (the override) must be refused.
  - Replay the attacker's successful prompt: it must now be blocked.
  - `python monitoring/simulate_prompt_attack.py`: confirms that detection still fires.
- [ ] **R4: Watch closely for 24 hours.** Keep the dashboard open, and run queries 01, 07 and 11 at T+4 h and T+24 h.

**Resolved means all of these are true:** no new attack sessions for 24 hours; the method that worked (if any) is closed and verified by R3; every affected user and every exposed data item is identified (B6), and the notifications from B5 are sent; emergency controls are lifted; and the evidence is archived with hashes.

## B8. Post-Incident Review (within 5 business days)

- [ ] Timeline: detection (T0) → triage → containment → resolution, all in UTC, taken from the incident log
- [ ] Root cause: direct or indirect, which control failed, and why
- [ ] Logs and exports archived before rotation, with `SHA256SUMS` verified
- [ ] Monitoring gaps: which signal would have caught this earlier? Add or retune alarms in `deploy_monitoring.py` and redeploy.
- [ ] Guardrail, IAM, KB or client changes made, with test evidence
- [ ] Update this playbook with anything that was unclear at 2 AM

## B9. Incident Log Template

```
Case:            IR-YYYYMMDD-HHMM        Severity: SEV-_    Analyst: ________
T0 (UTC):        ________  Trigger: AL-_ / user report / other: ________
SESSION_UUID(s): ________  RUNTIME_SESSION_ID(s): ________
Direct/indirect: ________  Outcome: Attempted-blocked / Partial / Successful
UTC time | Action taken (step ID) | Result / evidence file
-------- | ---------------------- | ----------------------
```

------------------------------------------------------------------------

## 6. Verification (performed 2026-10-03)

Everything in this document was exercised against the live Northstar deployment. The files referenced are in this folder.

### 6.1 Monitoring

| Test | Method | Result |
|---|---|---|
| Metric filter patterns (9 patterns) | `TestMetricFilter` on 27 real Northstar records, compared with the known traffic | ✅ Every pattern matched the expected records: prompt attacks 2, topic blocks 2, input blocks 6, output blocks 2, answers 4, tool calls 7, KB retrievals 7. `GuardrailMissing` matched exactly 1 record, the **real** unguarded override from the guardrail testing at 06:20:04, a true positive. Patterns are in `metric-filter-patterns.json`. |
| Saved Logs Insights queries (11) | Each query run against the last 24 h | ✅ All complete. Query 04 and query 07 both found the unguarded override session (`0e0227d4…`). Query 10 listed client sessions with request times. Query 08 listed the retrieval queries ("standard working hours", "Meridian Healthcare Systems contact email account ID", …). |
| Query 11 (indirect injection hunt) | Regex tested against compact-JSON records with a user-typed injection and with a poisoned chunk, then run on real logs | ✅ It matches instruction text **inside retrieved chunks** only. It ignores injections typed by the user, which an earlier version of the query falsely flagged, and returns 0 rows on real traffic (no poisoned documents). |
| **AL-1 end to end** | `simulate_prompt_attack.py`: one session sent 1 legitimate question and 6 injection attempts (06:58:44–06:58:51 UTC) | ✅ All 6 were blocked by PROMPT_ATTACK. The alarm `northstar-assist-prompt-attack-single-session` went to **ALARM about 30 seconds after the last attempt**, with `MaxContributorValue` **6.0 > 5**, and Contributor Insights named the session `BedrockAgentCore-60365d36…` (count 6). Details in `simulation-results.json`. |
| Other alarms, same traffic | Alarm states after the simulation | ✅ AL-2 saw 6 (≤ 10, stays OK), AL-3 OK (no bypass), AL-11 OK (2 errors from the kill-switch tests ≤ 5). There were no false alarms from the legitimate test traffic. |
| Lesson learned | A first simulation run counted only 2 of 6 | `deploy_monitoring.py` had been re-run (re-putting the rule) while that attack was arriving, and only the attempts before the redeploy were counted. A clean re-run with no redeploy counted all 6, so **re-putting a rule appears to restart its counting**. `deploy_monitoring.py` now writes the rule only when its definition changes. |

### 6.2 Playbook dry run (`playbook_dryrun.sh`, output in `dryrun-output.txt`)

| Step | Result |
|---|---|
| B0 setup | ✅ Variables resolved, including the invocation log group, looked up from the account |
| B3 triage (CLI query) | ✅ Top session `60365d36-1e46-4671-91e1-85f408a77762`, the simulated attacker |
| C1 evidence | ✅ 8 records for the session (1 question × 2 turns + 6 blocks), 52 window records, runtime log, harness, guardrail, IAM, ingestion and S3 snapshots, and `SHA256SUMS`, which verifies. The exports contain retrieved PII, so the dry-run folder was moved out of the repository, and `**/dryrun-case/` was added to `.gitignore`. |
| C2 correlate | ✅ Query 10 for the attack window returned exactly one client session, `sim-6dd85dad-568b-4cbb-a6a5-1e60e3a1bca3` (7 requests, 06:58:37–06:58:51). That is **the `runtimeSessionId` the simulator actually used**, which confirms the time-based correlation in A3. |
| C2 stop | ✅ `stop-runtime-session` with the **harness ARN** returned 200. (With the runtime ARN it fails, and the playbook was corrected.) Reusing the same `runtimeSessionId` afterwards gave a new harness session (`ba1d8ade…`) with **1 message** in context: the 7-turn attack history was gone. |
| C3 Deny check | ✅ `NorthstarRequireGuardrail` is present (`DenyModelCallsWithoutNorthstarGuardrail`) |
| C6 kill switches (`test_kill_switches.py`, `kill-switch-results.json`) | ✅ K1 and K2 each blocked all requests within 50 s, and service returned within 45 s of the undo. K1 turned out to be a full outage (the tool fails to load), and the playbook was corrected. Afterwards the only inline policy on the role is `NorthstarRequireGuardrail`. |
| B6 I-2 leak check | ✅ 0 answers contain system-prompt text |
| C5 (quarantine document and re-sync) | ⚠️ **Not exercised**: it would modify the live knowledge base, and no poisoned document exists. The commands use standard S3 and `bedrock-agent` APIs, and the bucket's versioning (verified on) makes the deletion recoverable. |
| C4 (block the source) | ⚠️ **Not exercisable in the lab**: there's no per-user identity in the app, and CloudTrail is denied. Documented as gaps S9 and S11. |

**CLI findings from the dry run, now written into B0:** AWS CLI v2 2.28 lacks the harness commands (use CloudShell or a current CLI), and Git Bash on Windows needs `MSYS_NO_PATHCONV=1` and `PYTHONIOENCODING=utf-8`.
