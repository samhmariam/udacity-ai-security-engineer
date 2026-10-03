# Northstar Assist: Incident Response Playbook PB-01, Suspected Prompt Injection

| Field | Value |
|---|---|
| System | Northstar Assist (harness `NorthstarAssist-yH4PMorNwm`, runtime `harness_NorthstarAssist-4tSgy4Clrq`, guardrail `bzgydako86r9` v1, gateway `northstar-assist-gateway-bkdy1kxxxm`, KB `ZCAWWBRBXU`) |
| Account / Region | `911470903119` / `us-east-1` |
| Owner | Samuel H. Mariam (system owner) |
| Last updated | 2026-10-03 |
| Companion document | [Northstar Assist Monitoring Plan](Northstar%20Assist%20Monitoring%20Plan.md). It defines the alarms this playbook responds to (**AL-1 to AL-11**, §A4), the saved Logs Insights queries it uses (**queries 01–11**, CloudWatch > Logs Insights > Saved queries > NorthstarAssist, §A4.5), the log sources (**S1–S11**, §A1), and how to correlate an invocation-log session with a client session (§A3). |
| Tested | Dry run against a simulated attack on 2026-10-03 (§B10) |

------------------------------------------------------------------------

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
  2. Run saved query `10 Client sessions active in a time window`, with the time range set to that window (±1 minute). The `sessionId` whose `first_request` and `last_request` line up with the attack timestamps is the client **`runtimeSessionId`** (see [Monitoring Plan §A3](Northstar%20Assist%20Monitoring%20Plan.md)).
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

- [ ] **C6: Emergency stop, if the attack continues and C2–C5 aren't enough.** Both options cause a **full outage** of Northstar Assist (tested, §B10).

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

## B10. Verification: Playbook Dry Run (performed 2026-10-03)

The dry run was performed with `playbook_dryrun.sh` (in this folder), which runs the steps below with this playbook's own commands against the simulated attack from `simulate_prompt_attack.py`. Its output is in `dryrun-output.txt`.

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
