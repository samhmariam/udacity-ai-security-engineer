# Northstar Assist: Monitoring Plan

| Field | Value |
|---|---|
| System | Northstar Assist (harness `NorthstarAssist-yH4PMorNwm`, runtime `harness_NorthstarAssist-4tSgy4Clrq`, guardrail `bzgydako86r9` v1, gateway `northstar-assist-gateway-bkdy1kxxxm`, KB `ZCAWWBRBXU`) |
| Account / Region | `911470903119` / `us-east-1` |
| Owner | Samuel H. Mariam (system owner) |
| Last updated | 2026-10-03 |
| Deployed monitoring | 11 metric filters (namespace `NorthstarAssist`), 1 Contributor Insights rule, 11 alarms, SNS topic `northstar-assist-security-alerts`, dashboard `NorthstarAssist-Security`, 11 saved Logs Insights queries (folder **NorthstarAssist**). All are created by `deploy_monitoring.py` in this folder, and every filter pattern and query was tested against real Northstar logs (section A8). |

This plan covers what to collect, what normal looks like, and what alerts. The response to a prompt-injection alert is in the separate playbook [**PB-01: Suspected Prompt Injection**](Northstar%20Assist%20IR%20Playbook%20PB-01.md), which uses the alarm IDs (AL-n), saved queries (01–11) and log sources (S1–S11) defined here.

------------------------------------------------------------------------

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

All alarms notify the SNS topic `northstar-assist-security-alerts`. `TreatMissingData = notBreaching`, so quiet periods don't page anyone. The severity in each alarm description tells the on-call analyst how fast to respond ([PB-01 §B1](Northstar%20Assist%20IR%20Playbook%20PB-01.md)).

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
| 01 | Prompt-attack blocks by session | invocation log | PB-01 triage (B3) |
| 02 | Session timeline (edit `SESSION_UUID`) | invocation log | PB-01 investigation (B6) |
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
| Evidence exports | Store in an S3 bucket with versioning (and Object Lock if available), plus SHA-256 hashes ([PB-01 step C1](Northstar%20Assist%20IR%20Playbook%20PB-01.md)) |
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

------------------------------------------------------------------------

## A8. Verification (performed 2026-10-03)

Everything in this document was exercised against the live Northstar deployment. The files referenced are in this folder.

| Test | Method | Result |
|---|---|---|
| Metric filter patterns (9 patterns) | `TestMetricFilter` on 27 real Northstar records, compared with the known traffic | ✅ Every pattern matched the expected records: prompt attacks 2, topic blocks 2, input blocks 6, output blocks 2, answers 4, tool calls 7, KB retrievals 7. `GuardrailMissing` matched exactly 1 record, the **real** unguarded override from the guardrail testing at 06:20:04, a true positive. Patterns are in `metric-filter-patterns.json`. |
| Saved Logs Insights queries (11) | Each query run against the last 24 h | ✅ All complete. Query 04 and query 07 both found the unguarded override session (`0e0227d4…`). Query 10 listed client sessions with request times. Query 08 listed the retrieval queries ("standard working hours", "Meridian Healthcare Systems contact email account ID", …). |
| Query 11 (indirect injection hunt) | Regex tested against compact-JSON records with a user-typed injection and with a poisoned chunk, then run on real logs | ✅ It matches instruction text **inside retrieved chunks** only. It ignores injections typed by the user, which an earlier version of the query falsely flagged, and returns 0 rows on real traffic (no poisoned documents). |
| **AL-1 end to end** | `simulate_prompt_attack.py`: one session sent 1 legitimate question and 6 injection attempts (06:58:44–06:58:51 UTC) | ✅ All 6 were blocked by PROMPT_ATTACK. The alarm `northstar-assist-prompt-attack-single-session` went to **ALARM about 30 seconds after the last attempt**, with `MaxContributorValue` **6.0 > 5**, and Contributor Insights named the session `BedrockAgentCore-60365d36…` (count 6). Details in `simulation-results.json`. |
| Other alarms, same traffic | Alarm states after the simulation | ✅ AL-2 saw 6 (≤ 10, stays OK), AL-3 OK (no bypass), AL-11 OK (2 errors from the kill-switch tests ≤ 5). There were no false alarms from the legitimate test traffic. |
| Lesson learned | A first simulation run counted only 2 of 6 | `deploy_monitoring.py` had been re-run (re-putting the rule) while that attack was arriving, and only the attempts before the redeploy were counted. A clean re-run with no redeploy counted all 6, so **re-putting a rule appears to restart its counting**. `deploy_monitoring.py` now writes the rule only when its definition changes. |

The playbook's dry run (triage, evidence, containment and kill-switch tests) is recorded in [PB-01 §B10](Northstar%20Assist%20IR%20Playbook%20PB-01.md).
