# SOLUTION — Exercise 07: Audit the KnowledgeHub Knowledge Base for Poisoning Risk

This document is the answer key for skill-pair-07.

---

## Task 1 — Document Classification

| Document | Classification | Reason |
|---|---|---|
| remote_work_policy_v3.txt | **SAFE** | People Operations remote work and flexible scheduling policy. Content matches the filename, no suspicious patterns |
| incident_response_runbook_v5.txt | **SAFE** | IT Operations runbook for access provisioning failures. Content matches the filename and the expected owner |
| compensation_review_policy_2026.txt | **REJECT** | A compensation review policy with an embedded "SYSTEM OVERRIDE" instruction mid-paragraph, written in plausible HR language but addressed to the model. It's also the file the access log shows being overwritten at 03:14 UTC by a read-only service account (Task 2). Do not ingest under any circumstances. |
| vpn_setup_guide_v2.txt | **REVIEW** | The VPN instructions themselves are ordinary, but one paragraph is repeated dozens of times, making the file roughly ten times longer than any other document. Padding like this can crowd legitimate content out of retrieval and dilute detection. Get a clean copy from IT Operations before ingesting. |
| all_hands_q1_2026_update.txt | **REJECT** | A CEO all-hands update carrying jailbreak text ("BEGIN SYSTEM", "developer mode", and a request to respond without content filtering) aimed at the model when the chunk is retrieved |
| denver_office_opening.txt | **SAFE** | Workplace announcement about the Denver hub. Content matches the filename, no suspicious patterns |
| cloud_infrastructure_guide.txt | **SAFE** (with a note) | Architecture reference that matches its filename. It lists internal roles, prefixes, and controls, so confirm it contains no credentials and that every KnowledgeHub user should see this level of detail. It's also useful in Task 2: it claims controls that the access log shows aren't working. |
| employee_expense_policy.txt | **REVIEW** | Named as an expense policy, but it's a confidential competitive pricing analysis for business development leadership. Either the wrong file was uploaded or a confidential document was mislabeled. Hold it for review. If it really is the pricing analysis, it doesn't belong in a company-wide knowledge base at all. |

**Check your filename reasoning.** Only one file has a name that doesn't describe its content (`employee_expense_policy.txt`). The two rejections look like the documents their names promise, which is exactly why a filename check alone doesn't catch them.

---

## Task 2 — S3 Access Log Analysis

### The two suspicious entries

**Suspicious Entry 1 — Write by a read-only service account, off hours, from an external IP**

```
[2026-03-12T03:14:22Z] ... 198.51.100.42 iam-user/svc-reporting-readonly ... REST.PUT.OBJECT
hr-docs/compensation_review_policy_2026.txt ... 200 - 22861 22861 489 "python-requests/2.31.0" versionId=Hp8Qv9WrXz0Ra3Tu
```

**What's anomalous:** `svc-reporting-readonly` is a read-only reporting service account, so it should never issue a PUT at all. The write happened at 03:14 UTC, outside business hours, from `198.51.100.42`, which is outside the internal `10.0.x.x` range every legitimate upload uses. The user agent is `python-requests`, not the `internal-upload-tool` the content owners use. It overwrote `hr-docs/compensation_review_policy_2026.txt`, an HR document, and the object size differs from the owner's upload (22,861 bytes vs 22,105 bytes). The entry also appears out of time order in the log, so read by timestamp, not by position. Two more details make this the most serious entry: `cloud_infrastructure_guide.txt` says the bucket policy "Allows PUT only from approved IAM roles", yet this write returned `200`, and the overwritten file is the one Task 1 rejects for its embedded "SYSTEM OVERRIDE" instruction.

**Next step:** Hold the sync. Rotate or disable the `svc-reporting-readonly` credentials, then check why a read-only account can write to the bucket at all. Use S3 versioning to download both versions of `compensation_review_policy_2026.txt` and diff them. Review what else that identity and that source IP touched.

---

**Suspicious Entry 2 — Contractor account writing outside its prefix**

```
[2026-03-12T16:09:17Z] ... 10.0.2.14 iam-user/contractor-vendordocs-acme ... REST.PUT.OBJECT
hr-docs/employee_handbook.pdf ... 200 - 874523 874523 1243 "boto3/1.34.0 Python/3.11.0" versionId=Jr0Sx1YtZb2Tc5Vw
```

**What's anomalous:** `contractor-vendordocs-acme` is a contractor account whose other upload in the log goes to `vendor-docs/`. Here it writes into `hr-docs/`, a prefix it has no business reason to touch. The file is an 874,523-byte PDF, far larger than any other upload in the log, and it arrives through a boto3 script rather than the internal upload tool. `cloud_infrastructure_guide.txt` says contractor access outside `vendor-docs/` "is denied by explicit Deny statement in the policy", but the write returned `200`, so that control either doesn't exist or doesn't apply to this user.

**Next step:** Hold the sync and quarantine `employee_handbook.pdf`. Confirm with HR whether they asked the contractor to upload it (they almost certainly didn't). Scope the contractor's IAM policy to `vendor-docs/*` so the write can't happen again, and review the document before it's ingested.

---

### Going further (not required): S3 configuration changes to catch these anomalies automatically

1. **Enable S3 Server Access Logging** for `vertex-kb-staging` — this captures all access events to a log bucket, but does not provide real-time alerts, and delivery is best effort (often within a few hours).
2. **Enable CloudTrail Data Events** on `vertex-kb-staging` specifically (both Read and Write events) — this captures every GetObject and PutObject as a CloudTrail event, enabling CloudWatch alerts on specific patterns. (This is a production design answer. CloudTrail is denied in the Udacity Cloud Lab.)
3. **Create a CloudWatch metric filter + alarm** on the CloudTrail log group for PutObject events where `requestParameters.key` starts with `hr-docs/` (or any knowledge base prefix) and the `userIdentity.arn` does not match the authorized content-owner identities.
4. **Enable S3 Object Versioning** on `vertex-kb-staging` — prevents overwritten documents from being lost; every PutObject creates a new version, and the previous version is always recoverable.
5. **Create an S3 Event Notification** that triggers a Lambda function on PutObject events — the Lambda can run validation checks on the uploaded document and alert the security team if the uploader identity is not on the approved list.

---

## Task 3 — Analyze `validate_documents.py`

Read the file at `starter/validate_documents.py` and find the 3 bugs. The bugs are:

### Bug 1: File size unit conversion is inconsistent

**Location:** `file_size_kb = os.path.getsize(filepath) / 1000`

**Problem:** `os.path.getsize()` returns bytes. Dividing by 1000 converts to decimal kilobytes, but the constant `MAX_FILE_SIZE_KB = 500` is meant as binary kilobytes (1 KB = 1024 bytes). The size the script computes and the limit it compares against aren't in the same unit. The error is small (about 2.4 percent) and it runs toward flagging: a 500,000-byte file computes to 500.0 KB with 1000 but 488.3 KB with 1024, and a 512,000-byte file (exactly 500 binary KB, at the limit) computes to 512.0 KB and is flagged as too large. The fix is to divide by 1024 so the value and the limit use the same unit.

**Note:** None of the sample documents are large enough to trigger this check either way — it is a latent bug that would only manifest on documents approaching the 500 KB boundary.

---

### Bug 2: Pattern matching is case-sensitive

**Location:** `if re.search(pattern, content):`

**Problem:** `re.search` without `re.IGNORECASE` is case-sensitive. The patterns in `SUSPICIOUS_PATTERNS` are mostly lowercase (e.g., `r'system.*override'`), so a poisoned document using uppercase variants — like "SYSTEM OVERRIDE" in `compensation_review_policy_2026.txt` — is not detected. The fix is to pass `re.IGNORECASE` as the flags argument.

---

### Bug 3: `validate_document` always returns `True`

**Location:** `return True, issues`

**Problem:** The function signature says it returns `(is_valid, issues)`, but the return statement hardcodes `True` for `is_valid` regardless of whether any issues were found. A caller can receive `is_valid=True` alongside a non-empty `issues` list — a contradiction. Because `scan_directory` uses `is_valid` to set the `valid` key, every document is reported as `[PASS]` even when suspicious patterns are detected. The fix is to return `len(issues) == 0` instead of `True`.

---

### Running the script

```bash
python3 starter/validate_documents.py starter/sample_docs/
```

**Current (buggy) output** — every document shows `[PASS]` because of Bug 3, even though suspicious patterns are reported, and Bug 2 hides the uppercase payload entirely:

```
[PASS] all_hands_q1_2026_update.txt
       - Suspicious pattern detected: 'BEGIN SYSTEM'
       - Suspicious pattern detected: 'developer mode'
       - Suspicious pattern detected: 'without.*content.*filter'

[PASS] cloud_infrastructure_guide.txt
[PASS] compensation_review_policy_2026.txt
[PASS] denver_office_opening.txt
[PASS] employee_expense_policy.txt
[PASS] incident_response_runbook_v5.txt
[PASS] remote_work_policy_v3.txt
[PASS] vpn_setup_guide_v2.txt

Total: 8 files | Pass: 8 | Fail: 0
All documents passed validation.
```

**Expected output with all bugs fixed:**

```
[FAIL] all_hands_q1_2026_update.txt
       - Suspicious pattern detected: 'ignore.*previous.*instructions'
       - Suspicious pattern detected: 'you are now'
       - Suspicious pattern detected: 'BEGIN SYSTEM'
       - Suspicious pattern detected: 'developer mode'
       - Suspicious pattern detected: 'without.*content.*filter'

[PASS] cloud_infrastructure_guide.txt

[FAIL] compensation_review_policy_2026.txt
       - Suspicious pattern detected: 'system.*override'

[PASS] denver_office_opening.txt
[PASS] employee_expense_policy.txt
[PASS] incident_response_runbook_v5.txt
[PASS] remote_work_policy_v3.txt
[PASS] vpn_setup_guide_v2.txt

Total: 8 files | Pass: 6 | Fail: 2
ACTION REQUIRED: Do not ingest flagged documents until issues are resolved.
```

With case-insensitive matching, two more patterns match in `all_hands_q1_2026_update.txt` ("Ignore previous instructions" and "You are now" are capitalized in the document).

**Do these results match the manual classification?** Yes — `compensation_review_policy_2026.txt` and `all_hands_q1_2026_update.txt` are correctly flagged for injection content. `vpn_setup_guide_v2.txt` passes the automated check (it is about ten times longer than the other documents but far under the 500 KB size threshold) — the manual review in Task 1 identifies the padding that the automated size check does not catch. `employee_expense_policy.txt` passes automated checks but the manual review catches the content-metadata mismatch. This illustrates the key limitation of automated validation: it catches injection keyword patterns and size extremes, but cannot detect content-to-filename mismatches or subtle poisoning that avoids known keyword patterns.

---

## Task 4 — Incident Response

### `compensation_review_policy_2026.txt` was already synced 48 hours ago

**Step 1 — Contain:** Stop any further ingestion while you investigate. Don't start a new sync, and if the data source is synced on a schedule or by a pipeline, pause that. Freeze writes to the knowledge base prefix for everyone except the investigators.

**Step 2 — Remove the poisoned document, then re-sync:** Delete `compensation_review_policy_2026.txt` from the bucket (or, if it overwrote a legitimate version, copy the known-good version back with S3 versioning). Then sync the knowledge base. Removing or restoring the file is not enough on its own: the index keeps serving the poisoned chunks until the sync runs. After the sync completes, ask the questions that retrieved the poisoned chunk and confirm the answers are clean.

**Step 3 — Assess the blast radius:** Pull the model invocation logs for the 48-hour window between the sync and the discovery. On an agent that retrieves through a tool, the retrieved chunks appear as `toolResult` content inside the next model request, including the source document's S3 URI, so search for records that mention `compensation_review_policy_2026.txt`. Because the access log shows a 03:14 UTC overwrite by `svc-reporting-readonly`, also restore the version the HR content owner uploaded on March 11 at 10:31 UTC (the overwrite was on March 12) rather than simply deleting the file. For each one, review the answer to see whether the poisoned content shaped it. Notify affected consultants if they were given incorrect or manipulated guidance, and correct anything that was acted on.

---

### Going further (not required): guardrail at query time vs. validation at ingestion time

**Catching at ingestion time** means the poisoned document never enters the KB. No employee query can ever retrieve it. The attack is stopped at the source, and there is no blast radius window. This is the preferred control because it is proactive — the KB always reflects a validated, clean set of documents.

**Relying on a guardrail at query time** means the poisoned document IS in the KB and is being retrieved. The guardrail's limits matter here:
1. On an Amazon Bedrock AgentCore harness, the guardrail doesn't screen retrieved chunks (tool results) on input. The poisoned text reaches the model unscreened.
2. A factually poisoned document (a plausible but wrong policy) has no attack pattern for an output check to match. In lab testing, a weakened security policy was repeated as official policy with no guardrail action.
3. When an output check does fire on a streaming assistant, the user may already have seen the answer. In the same test, one poisoned answer was blocked only after it had fully streamed.
4. Even when a response is blocked, the KB is still poisoned, and every future query on that topic hits the same problem.

**Which is preferable:** Ingestion-time validation is unambiguously preferable. It eliminates the threat before it enters the system. Query-time guardrails are defense-in-depth — they catch some of what ingestion validation misses, but they are not a substitute for it.

---

## Console Walkthrough: S3 Validation and KB Sync in the AWS Console

### 1. View S3 access logs

1. Navigate to **Services > S3**
2. Click **vertex-kb-staging**
3. Click the **Properties** tab
4. Under **Server access logging**, confirm logging is enabled and note the target bucket
5. Navigate to the target log bucket, then the log prefix (for this scenario, `vertex-access-logs` with prefix `kb-staging/`)
6. Click any log file to download and view — each line is an S3 access event

### 2. Enable CloudTrail data events on the KB bucket

> **Production accounts only.** CloudTrail is denied in the Udacity Cloud Lab, so these steps won't work there. Use the S3 server access log from step 1 instead.

1. Navigate to **Services > CloudTrail**
2. Click **Trails > your trail name**
3. Under **Data events**, click **Edit**
4. Click **Add data event type**, choose **S3**
5. Select **Individual bucket ARN**, enter `arn:aws:s3:::vertex-kb-staging`
6. Enable both **Read** and **Write** events
7. Click **Save changes**
8. Data events now appear in CloudTrail Event history for this bucket

### 3. View Knowledge Base sync status and history

These steps follow the Managed Knowledge Base you built in `skill-pair-00-bedrock-setup/WALKTHROUGH.md`.

1. Search for **Amazon Bedrock AgentCore** and open it
2. In the left navigation under **Built-in tools**, choose **Knowledge Bases (KB)**
3. Choose your knowledge base (for the lab build, `vantage-aria-kb`)
4. Choose your S3 data source (for the lab build, `vantage-documents`)
5. The **Sync history** lists each sync job with its status and document counts. A document that was overwritten shows up as **modified**. **View CloudWatch logs** opens the knowledge base application logs, which record when each sync started and finished

### 4. Trigger a manual KB sync

1. On the knowledge base page, select the data source
2. Choose **Sync**
3. Watch the **Sync history**: the new job appears as in progress
4. Refresh until the job completes
5. Review the counts: scanned, added, modified, deleted, and failed documents. After you restore or delete a poisoned document, this sync is what removes it from answers
