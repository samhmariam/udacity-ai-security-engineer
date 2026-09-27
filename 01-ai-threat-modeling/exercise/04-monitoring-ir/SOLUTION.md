# SOLUTION — Exercise 04: Monitoring Plan and IR Playbook for OpsGuide

This document is the answer key for skill-pair-04. Open it after you've completed every task.

---

## Task 1 — Completed Monitoring Plan

**Author:** NovaTech Security Team
**Date:** 2026-03-14
**System:** OpsGuide (RAG assistant on an AgentCore harness)

| # | Log / Metric Source | What to Log | Alert Condition |
|---|---|---|---|
| 1 | **Bedrock Model Invocation Logs** | `ConverseStream` records from the harness: `input.inputBodyJson.messages` (user text, the `toolUse` retrieval query, and the `toolResult` with full chunk text and S3 location), `input.inputBodyJson.system`, `output.outputBodyJson.output.message.content`, `output.outputBodyJson.stopReason`, `input.inputTokenCount` / `output.outputTokenCount`, `modelId`, `inferenceRegion`, `identity.arn` (harness role + session ID; no user identity), and `output.outputBodyJson.trace.guardrail` (which policy intervened, and `modelOutput` for blocked answers). Restrict access and set retention: the log holds retrieved PII and withheld answers. | **Threshold-based:** Any record with a blocking guardrail intervention in `trace.guardrail` — page immediately (potential injection attempt). Don't alert on `stopReason: guardrail_intervened` alone; anonymize actions report it too. **Threshold-based:** Any harness `ConverseStream` record with no `appliedGuardrailDetails` (guardrail bypassed through a model override). **Rate-based:** `input.inputTokenCount` > 10,000 on a turn with no `toolResult` (context stuffing). **Pattern-based:** Same harness session ID with > 20 model turns within 5 minutes (Logs Insights per-session query; one question is at least 2 turns). **Pattern-based:** An `end_turn` record with no `toolResult` and `output.outputTokenCount` more than 3 times the session average (an ungrounded answer). |
| 2 | **Bedrock Guardrails Metrics** | Namespace `AWS/Bedrock/Guardrails`: `Invocations`, `InvocationsIntervened`, `InvocationLatency`, `TextUnitCount`. Break `InvocationsIntervened` out by `GuardrailPolicyType` (`ContentPolicy`, `SensitiveInformationPolicy`, `TopicPolicy`, `WordPolicy`) and `GuardrailContentSource` (`Input`/`Output`); harness traffic reports under `Operation=ApplyGuardrail`. Per-invocation detail (including grounding results) is in `trace.guardrail` in the invocation log, not in a metric. | **Rate-based:** `InvocationsIntervened` exceeds 5% of `Invocations` in any 15-minute window (baseline is ~0.5% for legitimate users; 5% indicates active probing). **Threshold-based:** Input-side `ContentPolicy` interventions > 5 in 10 minutes (prompt attacks). **Threshold-based:** Any output-side `SensitiveInformationPolicy` intervention outside normal anonymization volume. |
| 3 | **S3 Access Logs (Knowledge Base source bucket)** | All `PutObject`, `DeleteObject`, and `GetObject` events on `novatech-opsguide-kb` with prefix `knowledge-base-docs/`. Record: requester ARN, source IP, timestamp, object key, HTTP status code, bytes transferred. Enable CloudTrail data events on this bucket specifically. | **Threshold-based:** Any `PutObject` or `DeleteObject` by a principal other than the designated content-owner IAM role — page immediately (unauthorized KB modification). **Rate-based:** More than 50 `GetObject` calls to this bucket within 5 minutes from a single identity (bulk exfiltration attempt). |
| 4 | **CloudWatch Cost and Usage Alarms** | Bedrock token usage metrics: `InputTokenCount` and `OutputTokenCount` from namespace `AWS/Bedrock`. Estimated cost derived from token counts. Also monitor Bedrock invocation count (`Invocations` metric, dimension `ModelId`). | **Threshold-based (billing):** Estimated Bedrock spend exceeds $50 in any single day — SNS notification to security-engineering and finance. **Rate-based (invocations):** `Invocations` exceeds 500 in any 60-minute period — page immediately (well above expected maximum of ~25 concurrent operators × 2 queries/hour). |

### Additional Sources (Not Required)

The template asks for the four sources above. These rows go further.

| # | Log / Metric Source | What to Log | Alert Condition |
|---|---|---|---|
| 5 | **IAM Authentication Events (CloudTrail)** (denied in the Udacity lab) | `AssumeRole` events for the OpsGuide roles (harness execution role, gateway role, KB service role, Streamlit app role). Record: who assumed the role, from what source IP, at what time, and from what originating identity. Also log `CreateAccessKey`, `DeleteAccessKey`, `AttachRolePolicy`, `DetachRolePolicy` events on these roles. | **Threshold-based:** Any `AssumeRole` event for an OpsGuide role from an IP address outside OpsGuide's expected network ranges — page immediately. **Threshold-based:** Any `AttachRolePolicy` event on an OpsGuide role that adds permissions beyond the least-privilege baseline — page immediately. |
| 6 | **Harness and Gateway Operational Logs** | Harness runtime log group `/aws/bedrock-agentcore/runtimes/harness_<name>-<id>-DEFAULT` (runtime errors; mostly container noise), and the harness Observability panel (sessions, invocations, gateway/tool invocations, tokens, error and throttle rates). The Managed Knowledge Base vector store is AWS-managed, so there is no vector index access log to collect. Gateway traces require CloudWatch Transaction Search. | **Rate-based:** Runtime error rate or throttle rate above 5% in any 15-minute window. Don't use the Observability panel for real-time alerts: its data can be delayed up to 60 minutes. |
| 7 | **Streamlit Application Logs** | Application-layer log for each request: operator user ID, terminal ID, the `runtimeSessionId` the app sent, timestamp, request character count, response status (success/error/rate-limited), rate limiter decision (allowed/denied), and any application-level exceptions. Do NOT log the full query text here (it is captured in Bedrock invocation logs with appropriate access controls). | **Rate-based:** More than 10 requests from a single user ID within any 60-minute window (rate limit enforcement check). **Rate-based:** More than 20% of requests in a 5-minute window returning application errors (Bedrock API degradation or misconfiguration). **Threshold-based:** Any rate limiter DENY event followed by the same user immediately creating a new session — potential rate limit evasion. |
| 8 | **Bedrock Knowledge Base Sync Events** | All KB sync job start/complete/fail events (`StartIngestionJob.StatusChanged` events in the knowledge base application log group `/aws/vendedlogs/bedrock/knowledge-base/APPLICATION_LOGS/<kb-id>`, and CloudTrail `StartIngestionJob`). Record: job ID, start time, end time, documents processed count, documents failed count, error messages if any. | **Threshold-based:** Any sync job that completes with 0 documents processed when documents are expected (possible KB wipe). **Threshold-based:** Any sync job started outside the scheduled nightly window (02:00–03:00 UTC) — page security team (unauthorized or early sync that may be ingesting poisoned documents). **Threshold-based:** Any sync job failure with an error indicating access denied on S3 — investigate for IAM misconfiguration. |

### Prioritization

**Must-have before go-live (top 3):**

1. **Bedrock Model Invocation Logs (#1)** — Without this, you have no forensic record of what was asked, what was retrieved, and what the model said. Every other incident type is uninvestigable without this log. It is the single most important gap to close before production.

2. **S3 Access Logs (#3)** — The KB source bucket is the primary attack surface for tampering and poisoning. Without access logs, a document replacement could go undetected for days or until an operator reports unexpected system behavior.

3. **Bedrock Guardrails Metrics (#2)** — This is the real-time signal for active injection attempts. A spike in BLOCK rate is often the first indicator that an attacker is probing the system. Without this signal, injection attempts are invisible until after damage is done.

**Log source most unique to AI systems:**

Bedrock Model Invocation Logs (#1) — specifically the inclusion of retrieved document chunks in the invocation log. Traditional application logs record request/response but have no concept of "what documents was the model shown." This is a RAG-specific artifact: the log must capture the retrieval context to be useful for forensics, because the same user query can produce different model responses depending on which chunks were retrieved.

**Gap in this monitoring plan:**

None of the sources in this plan directly catch a slow membership inference attack — an employee systematically probing the system with slightly varied queries to enumerate the contents of the employee directory, one record at a time. The queries look individually legitimate; it is only the pattern across hundreds of queries that reveals the attack. Detecting this requires cross-session behavioral analytics (user queried 50 "who works in..." variations over 3 days), which would require aggregating Streamlit logs and invocation logs at the user level and applying anomaly detection — not covered by any single source in this plan.

---

## Task 2 — Mock Incident Log Analysis (Event A)

The exercise asks three questions about Event A. Events B and C follow as further study.

### Event A

**1. What is happening?**

One harness session sent 47 requests in 8 minutes from terminal `PLANT2-LINE4-T07` between 03:02 and 03:10 UTC. That's outside the terminal's normal pattern of short bursts at shift start and shift end.

The session starts with two ordinary maintenance questions. It then escalates: four prompt injection attempts (admin mode, system prompt extraction, context window extraction, and a no-restrictions persona) and a competitor question, all blocked. The session has 12 prompt attack interventions and 3 topic policy interventions in total.

The last shown request is the one that matters. The operator rephrased the goal as an ordinary operational question about clearing a jam with the interlock engaged. It passed the guardrail and returned a 312-token answer, 4.1 times the session average, with 0 retrieved chunks. No approved procedure covers that task, so the model answered from its own knowledge. For a plant operator, an ungrounded answer about working around a safety interlock can cause equipment damage or injury.

Classify this as a suspected prompt injection attack with a probable evasion success. The contextual grounding check didn't catch the ungrounded answer: the guardrail recorded no grounding assessment for the turn, which matches testing on harness traffic.

**2. Which detection signals from the monitoring plan would catch it?**

- **Guardrails metrics (row 2):** input-side `ContentPolicy` interventions > 5 in 10 minutes. The 12 prompt attack interventions in 8 minutes trip it.
- **Model invocation logs (row 1):** the per-session query for more than 20 model turns in 5 minutes flags the session.
- **Model invocation logs (row 1):** an `end_turn` record with no `toolResult` and an output token count far above the session average flags the 03:08:30 answer. This is the signal that shows the attacker may have succeeded.
- **Cost alarms (row 4)** don't catch it. 47 requests is too few.
- The unusual hour isn't a CloudWatch metric. Seeing it takes the Streamlit application log, which records the terminal and time.

**3. What information is missing?**

- The full text of the 312-token answer (`output.outputBodyJson.output.message.content` in the invocation record)
- The 39 requests not shown, and the guardrail trace for each
- Whether the operator used other terminals or sessions that night. The invocation log can't answer this, because it doesn't record the operator or the app's `runtimeSessionId`.
- Who was physically at the terminal at 03:00, and whether anyone acted on the answer at HP-12
- This operator's and this terminal's activity over the previous days

**First-hour actions (for the playbook):**

1. Export the invocation records for 02:55–03:15 UTC first. In CloudWatch > Logs Insights, select `/aws/bedrock/novatech-opsguide/invocations`, filter on `sess_7f3a92bc`, and export the results.
2. Read the 03:08:30 record's response text and guardrail trace.
3. Tell plant operations for Line 4 that the HP-12 answer given at 03:08 isn't an approved procedure.
4. Run the per-session query over the last 24 hours to find other sessions with prompt attack interventions.

The course doesn't show a way to block a single operator on a harness. Record that gap at the playbook's decision point.

---

### Event B (further study)

**Incident type:** Knowledge base tampering. An unknown IAM user uploaded a new version of the HP-12 maintenance manual from an unknown IP address and started a manual sync at 23:46, outside the nightly 02:00 schedule. The changed manual has been answering operators' questions since 23:47.

**First-hour actions:**
1. Compare the current and previous versions of `hp12_maintenance_manual_v3.pdf` (S3 > `novatech-opsguide-kb` > the object > **Versions**).
2. If the new version is suspicious, restore the previous version and sync the knowledge base again. The changed chunks stay in the index until the sync completes.
3. Deactivate the access keys for `kb-sync-svc-unknown` (IAM > Users > the user > **Security credentials**).
4. Search the invocation log for records whose `toolResult` includes the document since 23:47 (Logs Insights: `filter @message like /hp12_maintenance_manual_v3.pdf/`).

**Additional information you'd want:** what changed between the two versions, who created `kb-sync-svc-unknown`, and what else that user did.

### Event C (further study)

**Incident type:** Possible sensitive data exposure from a tampered document. The answer drew on the manual ingested in Event B, and the guardrail blocked a phone number in the output. The previous version of the manual has no phone numbers in its emergency contact section, so the number was probably added in the Event B upload. OpsGuide streams responses, so the operator may have seen the number before the block.

**First-hour actions:**
1. Read the blocked answer in `trace.guardrail.modelOutput` for the 03:52:07 record.
2. Ask `m.okonkwo@novatech.com` what they saw and whether they called the number.
3. Handle the source document as in Event B.

### Cross-Event Analysis

- **Connection:** Events B and C are the same incident, because C retrieved the document B uploaded. Event A is probably separate, because its final answer used no retrieved chunks, but it happened the same night.
- **Escalate first:** Event B. The tampered manual keeps answering every operator's HP-12 questions until it's restored and the knowledge base is synced again.
- **Earliest warning:** an alert on S3 `PutObject` in the knowledge base prefix by any principal other than the content-owner role (row 3), or on a sync started outside the 02:00 window (additional row 8). Either would have fired at 23:44–23:46.

---

## Task 3 — IR Playbook: Suspected Prompt Injection Attack

**Detection signals:**

| Signal | Where to find it | Threshold |
|---|---|---|
| Input-side prompt attack interventions | CloudWatch > Metrics > `AWS/Bedrock/Guardrails` > `InvocationsIntervened` with `GuardrailContentSource=Input`, `GuardrailPolicyType=ContentPolicy`, `Operation=ApplyGuardrail` | > 5 in 10 minutes |
| Many model turns in one harness session | CloudWatch > Logs Insights on the invocation log group, per-session query (`parse identity.arn "/BedrockAgentCore-*" as session_id`) | > 20 model turns in 5 minutes |
| An ungrounded long answer after blocked attempts | Invocation log: an `end_turn` record with no `toolResult` and `output.outputTokenCount` far above the session average | Any, in a session that also has prompt attack interventions |
| Harness records with no guardrail trace | Invocation log: `ConverseStream` records with no `appliedGuardrailDetails` | Any (model override bypass) |

**Confirmation:** A single blocked prompt attack is a probe, not necessarily an active attack. Treat it as an active incident if: (1) the same session or terminal has more than 3 prompt attack interventions in 24 hours, (2) blocked attempts are followed by rephrased questions that pass, or (3) any record shows an answer outside the approved documents, such as an answer with no retrieved chunks.

**Containment (first 15 minutes):**
1. Export the evidence first. In CloudWatch > Logs Insights, run the per-session query over the attack window on the invocation log group, and export the results before any change that could affect the records.
2. If any record in the window has no guardrail trace, the attacker bypassed the guardrail with a model override. Add the harness-role Deny that requires the guardrail (IAM > Roles > the harness execution role > **Add permissions** > **Create inline policy**), as shown in Lesson 11.
3. If an ungrounded answer about equipment or safety reached an operator, tell plant operations for that line that the answer isn't an approved procedure.
4. Blocking one operator: the course doesn't show a way to block a single user on a harness. Decide ahead of time whether a temporary outage is acceptable if the attack continues, and who approves it (the template's decision point).

**Investigation (first hour):**
1. Find the operator and terminal in the Streamlit application log for the attack window. The invocation log has no user ID, and its session ID doesn't match the `runtimeSessionId` the app logs, so review all invocation records in the same window (CloudWatch > Logs Insights on the invocation log group).
2. Identify the pattern: probing for the system prompt, trying to reach restricted content, or testing guardrail bypass variants.
3. Check for success: records in the window that ended in `end_turn` with no intervention, answers with no retrieved chunks, and records with no guardrail trace. Read `output.outputBodyJson.output.message.content` for each.
4. Check the scope: run the per-session query over the last 24 hours for other sessions with prompt attack interventions.

**Resolution:** Resolved when the investigation confirms what, if anything, the attacker got; every operator who received an ungrounded safety answer has been told it isn't approved; the activity has stopped; and any bypass is closed with the IAM Deny. Document the findings, and add new bypass patterns to the guardrail configuration.

---

## Beyond the Exercise (Not Required): Two More Playbooks

The exercise asks for one playbook. These two show the same approach for other incident types.

### (b) Possible Sensitive Data Exposure in AI Response

**Detection signal:** Guardrail action = BLOCKED with filter = SENSITIVE_INFORMATION (Guardrail caught it), OR an operator reports that the system returned their colleague's personal information, OR invocation log review reveals a response containing PII patterns (SSN, salary figure, individual performance review content).

**Initial question:** Is this a Guardrail failure or a data problem?
- **Guardrail failure:** The data was legitimately in the KB, the guardrail was supposed to catch it, and didn't. The system is working as designed but the Guardrail is misconfigured.
- **Data problem:** The data should not have been in the KB in the first place (e.g., the full employee directory with salary data was uploaded). The root cause is a data governance failure at the ingestion step.

**Containment:**
1. If the response has already been delivered to the user: document what was exposed and who received it — this may trigger a privacy notification obligation. On a streaming harness, assume an output-side block arrived after the text was already shown.
2. Identify the source document that produced the sensitive chunk. Find the S3 URI in the `toolResult` retrieval results (`location.s3Location.uri`) in the invocation record.
3. If the source document should not be in the KB: delete the S3 object and run a manual KB sync (this re-indexes the KB without the deleted document, removing the sensitive chunk from the vector index).
4. If the source document should be in the KB but should have been minimized (columns removed): create a minimized version, replace the S3 object, re-sync the KB.

**Resolution:** Confirmed when: (1) the sensitive data source has been removed from the KB and the sync has completed, (2) a test query that previously triggered the exposure now returns no sensitive content, (3) Guardrail PII settings have been reviewed and tightened if a filter gap was found, and (4) the privacy team has been notified of the exposure for potential notification obligations.

---

### (c) Knowledge Base Document Tampering

**Detection signal:** S3 access log shows a `PutObject` or `DeleteObject` event on the KB prefix by an unexpected principal, OR the KB sync job fails or produces an anomalous document count, OR an operator reports that the system is giving incorrect policy information.

**Key characteristic:** This incident is silent by design. The system continues operating normally — it is just operating on poisoned data. The window between the tampered document being ingested and the tampering being discovered is the blast radius window.

**Immediate steps:**
1. **Stop the next KB sync:** If the tampered document has not yet been synced, block the sync from running (disable the sync schedule in the Bedrock console) until the document is validated.
2. If already synced: the vector index now contains the poisoned content. Determine when the sync ran (from `StartIngestionJob.StatusChanged` events in the KB application log group) to establish the blast radius window (which queries were answered using poisoned chunks?).
3. Revoke or suspend the credentials of the uploader if they are not a designated content owner.

**Investigation:**
1. Download the tampered document from S3 and compare to the previous version (use S3 Object Versioning if enabled; if not, compare to a backup).
2. Search invocation logs for records whose `toolResult` contains the tampered document's S3 URI in the post-sync window (Logs Insights: `filter @message like /<document-name>/`).
3. Review the tampered content: was it a factual modification (changed policy terms), a social engineering payload (fake instructions to operators), or an embedded prompt injection (instructions to the model)?

**Restoration:**
1. Restore the previous document version (S3 ObjectVersions) to the S3 bucket.
2. Run a manual KB sync to re-index the KB with the restored document.
3. Verify: submit a test query that would have retrieved the tampered chunk; confirm the response now reflects the correct document content.

**Resolution:** Confirmed when: (1) the KB has been re-indexed with the clean document, (2) test queries return correct content, (3) the credential that performed the upload has been investigated and handled, (4) affected operators have been notified if they received information from the tampered document during the blast radius window.

---

## Beyond the Exercise (Not Required): Most Important Thing to Log

The single most important thing to log in a Bedrock RAG system is the full model invocation record: the exact input to the model (system prompt + retrieved chunks + user query) AND the exact response. Traditional application logs capture request/response but have no concept of the retrieved context — they cannot tell you which documents the model was shown when it produced a given response. In a RAG system, the same query can produce wildly different responses depending on what was retrieved (especially after a KB poisoning event). Without the retrieved chunks in the log, you cannot determine: (1) whether an injected document influenced a response, (2) which users were affected during a tampered-KB window, or (3) why the model said something it shouldn't have. This log is the forensic foundation for every other incident type in this playbook.

---

## Console Walkthrough: Setting Up Monitoring in the AWS Console

### 1. Enable Bedrock model invocation logging

Create the log group before you turn on logging. The role that Bedrock creates for logging can write to an existing log group, but it can't create one.

1. In **CloudWatch**, choose **Logs > Log groups > Create log group**, and enter `/aws/bedrock/novatech-opsguide/invocations`
2. Go to **Amazon Bedrock > Settings** and turn on **Model invocation logging**
3. Keep **Text** selected, choose **CloudWatch Logs only**, and enter the log group name
4. Choose **Create default role** and enter a role name
5. Choose **Save settings**. If saving fails with **Failed to validate permissions for log group**, the log group doesn't exist yet
6. Test: send a prompt to the harness (Harness playground or `invoke_harness`) and check for `ConverseStream` records under the harness execution role

### 2. Create a CloudWatch alarm on Bedrock invocation count

1. Navigate to **Services > CloudWatch**
2. In the left sidebar, click **Alarms > All alarms > Create alarm**
3. Click **Select metric**
4. Navigate to **AWS/Bedrock > ModelId**
5. Find the metric `Invocations` for your model ID (e.g., `us.anthropic.claude-sonnet-4-5-20250929-v1:0`)
6. Click **Select metric**
7. Set:
   - **Period:** 1 hour
   - **Statistic:** Sum
   - **Threshold:** Greater than **500**
8. Click **Next**
9. Under **Notification**, click **Add notification**, choose **In alarm**, select or create an SNS topic (e.g., `novatech-security-alerts`)
10. Click through to **Create alarm**

### 3. View CloudTrail logs for Bedrock API calls

> CloudTrail is denied in the Udacity Cloud Lab. Run these steps in your own account.

1. Navigate to **Services > CloudTrail**
2. In the left sidebar, click **Event history**
3. Use the filter dropdown to filter by:
   - **Event source:** `bedrock.amazonaws.com`
   - **Time range:** last 24 hours
4. Click any event to expand and see the full API call details (who called it, from what IP, what parameters)
5. For S3 data events on the KB bucket: go to **Trails > your trail > Edit > Data events**, ensure the S3 bucket is listed for Read and Write events

### 4. Create an SNS topic for alert notifications

1. Navigate to **Services > Amazon SNS**
2. Click **Topics > Create topic**
3. Choose **Standard**, name it `novatech-security-alerts`
4. Click **Create topic**
5. Click **Create subscription**, choose **Protocol: Email**, enter the security team email address
6. Click **Create subscription** — the team receives a confirmation email; click the confirmation link
7. Use this topic ARN in all CloudWatch alarm notification actions
