# SOLUTION — Exercise 09: Apply Privacy-Preserving Design to the MyHealth Assistant Knowledge Base

This document is the answer key for skill-pair-09. Open it after you've completed every task.

Every decision follows from one fact: MyHealth Assistant is reachable by any authenticated patient. Staff are not the audience. The documents are in `starter/documents_to_classify_myhealth/`.

---

## Task 1 — Document Classification

| # | File | Classification | Include in KB? | Fields/Columns to Remove | Reason |
|---|---|---|---|---|---|
| 1 | appointment_scheduling_guide.txt | **Public** | **Yes** | None | Written for patients. It explains how to book, change, and prepare for appointments, and it contains no information about any individual. |
| 2 | discharge_and_medications_guide.txt | **Public** | **Yes** | None | General discharge guidance and medication coverage rules written for patients. It contains no information about any individual patient. |
| 3 | patient_access_center_procedures.txt | **Internal** | **No** | Exclude entire document | Staff procedures for verifying callers, holding slots, and overriding full schedules. Patients have no need for them, and the verification steps tell an attacker exactly which details to gather to pass as another patient on the phone. |
| 4 | payer_contract_rates.txt | **Confidential** | **No** | Exclude entire document | Negotiated insurer payment rates and renewal negotiations. Exposure would break the confidentiality terms of each payer agreement and gives patients no information they can act on. |
| 5 | staff_directory.csv | **Restricted** (for this audience) | **Modified** | `employee_id`, `full_name`, `email`, `phone_extension`, `manager_name`, `salary_band` (see Task 2) | For staff, this is ordinary internal information. When any patient can query it, it lets a patient find a named staff member, reach that person directly, and see who they report to and how they are paid. Only the department and its location help a patient reach a service. |
| 6 | discharge_followup_call_log.csv | **Restricted** (PHI) | **No** | Exclude entire document | Holds protected health information: patient names, medical record numbers, dates of birth, phone numbers, procedures, and nurse notes. Any authenticated patient could retrieve another patient's records. |

**Key point:** the staff directory file is unchanged between a staff-facing and a patient-facing assistant. Its classification rises because the audience changed.

---

## Task 2 — Staff Directory Column Removal Analysis

A patient needs to know that a department exists, that it handles a service, and where it is. A patient does not need a named staff member, a direct line to that person, or information about that person's standing in the organization.

### 2a. Columns to remove and why

Remove six columns: `employee_id`, `full_name`, `email`, `phone_extension`, `manager_name`, and `salary_band`. The three below match the three risks on the solution page: a named person, a direct line, and standing in the organization. The other three are listed under **Also remove**. A complete answer names all six columns and explains each risk in a patient-facing context.

**1. `full_name`**
A name lets a patient pick out one staff member. A patient who is angry about a bill, a denied refill, or a care decision can ask the assistant for that person by name and then look for that person at work. This is a safety risk for staff. A name also gives a caller a credible detail for social engineering ("Morgan in Cardiology told me to call about my records"). Patients don't need a staff name to reach a department.

**2. `phone_extension`**
A direct extension lets a patient skip Central Scheduling and the nurse line and call an individual staff member. That staff member may not be trained or authorized to verify the caller, which makes the extension a route for social engineering against the health system's own processes. The patient guides already give the department phone numbers patients should use.

**3. `manager_name`**
The manager column shows reporting lines. A patient can use it to escalate a complaint to a named manager outside the normal process, to pressure a staff member by naming their manager, or to map who has authority over schedule overrides. It describes a staff member's standing in the organization, which has no use for a patient.

**Also remove:**
- `email`: a direct contact route to a named person, with the same risks as `phone_extension`. It also reveals the email address format, which lets someone guess other staff addresses.
- `salary_band`: compensation data about individuals. It has no patient use and is a privacy risk for staff.
- `employee_id`: an internal identifier that links a person across HR, payroll, and access systems. Once names are removed it no longer serves any purpose, and keeping it lets someone match rows to other leaked data.

### 2b. Minimized CSV header

```
department,office_location
```

After the six columns are removed, the ten staff rows collapse to six department rows. Keep one row per department. With `full_name` removed, `office_location` shows where a department's service is. It no longer shows where a specific person can be found.

### 2c. Residual risk after minimization

The minimized directory can't confirm whether a named staff member works at Westfield Health, because it holds no names. Inference from other data is still possible. In the demo, the model guessed a likely email address from an email format rule in a different document, even after the directory was minimized. Review every included document for the same kind of detail, such as an email format, a staff name in a signature line, or a direct extension in a footer.

---

## Task 3 — PII Guardrail Configuration

| PII Type | Action | Justification |
|---|---|---|
| Social Security number (SSN) | **BLOCK** | No legitimate use in this system. None of the included documents contain SSNs. On input, a patient who types an SSN gets the blocked message, which is better than the model repeating it back. On output, an SSN would mean a document with PII was uploaded by mistake. Block it and investigate the source document. |
| Credit/debit card number | **BLOCK** | Patients may type a card number when asking about a bill. The assistant can't take payments, so there is no reason to process the number. On output, a card number would mean a data ingestion error. |
| Bank account number | **BLOCK** | Same reasoning as card numbers. No legitimate use in a patient question or a response. |
| AWS access key | **BLOCK** | A key in a response would mean a key was embedded in a knowledge base document. Block the response. Treat the key as compromised and rotate it. |
| AWS secret key | **BLOCK** | Same as the access key. Block, rotate the key, and remove it from the source document. |
| Password | **BLOCK** | Patients may type a portal password when asking for login help. The assistant should never process or repeat it. Actual passwords have no place in any knowledge base document. |
| Email | **ANONYMIZE** | Anonymizing replaces the address with `{EMAIL}`, so the answer still arrives without the specific address. Once `email` is removed from the directory, this filter is a defense-in-depth backstop. It also covers a patient typing their own email address, which the model might repeat. Streamed anonymization can leak fragments next to the placeholder, so don't treat it as the primary control. |
| Phone | **ANONYMIZE** | Same reasoning as email. Tradeoff: this also masks the public department numbers in the patient guides, such as Central Scheduling. A student who chooses ALLOW for Phone, explains that tradeoff, and relies on removing `phone_extension` has a defensible answer. |
| Name | **ALLOW** | Patients often use their own name in a question, and the assistant needs to answer them. On an assistant that calls tools, anonymizing names can stop the request before the tool runs, so the patient gets no answer. The protection for staff and patient names is data minimization: `full_name` is removed from the directory and the call log is excluded. |
| Address | **ALLOW** | The patient guides include clinic addresses, which patients need to find their appointment. BLOCK or ANONYMIZE would break those answers. Home addresses are kept out of the knowledge base by excluding the call log. A student who chooses ANONYMIZE because patients may type a home address, and who accepts that clinic addresses get masked, has a defensible answer. |

**ANONYMIZE is also defensible** for SSNs, card numbers, and bank account numbers. With ANONYMIZE, a patient who types their own number gets an answer with the number masked, instead of the blocked message. A student who chooses ANONYMIZE and explains that tradeoff has a defensible answer. BLOCK is the stricter choice. On a streaming assistant, anonymization can leak fragments next to the placeholder, so use BLOCK when a value must never reach the patient.

**Not on the PII type list:** health information and salary data. Classification decisions protect them here: the call log is excluded, and `salary_band` is removed from the directory.

---

## Task 4 — Why Output Filtering Is Not the Primary Control

Output filtering acts after the sensitive data has already been retrieved from the knowledge base and placed in the model's context. The filter only changes what the patient sees at the end. A misconfigured or bypassed filter lets the data reach the patient with no other control in the way, and the model invocation logs keep the retrieved text even when the filter works. Filtering is also imperfect when it works: in the demo, streamed anonymization leaked a fragment of a phone number next to the `{PHONE}` placeholder. Every patient question is another chance for the filter to miss, and with thousands of patients querying every day, rare misses add up. Anonymizing a value also doesn't stop someone from narrowing it down with a series of yes-or-no questions, because the underlying record is still retrievable. Data minimization removes the data from the knowledge base, so no filter setting and no sequence of questions can bring it back. Filtering remains worth configuring as a second layer, especially for data patients type into their own questions.

---

## Console Walkthrough: PII Detection and Data Protection in the AWS Console

### 1. Configure PII detection in Bedrock Guardrails

1. Navigate to **AWS Console > Services > Amazon Bedrock**
2. In the left sidebar, under **Build**, click **Guardrails**
3. Click your guardrail name (`myhealth-assistant-guardrail`), then choose **Working draft**. It opens a summary with an **Edit** button for each section. The guardrail-level **Edit** button changes only the name, description, and messages.
4. In **Sensitive information filters**, choose **Edit**
5. Under the **PII types** tab, you will see a table of PII categories
6. For each PII type, choose **Add new PII**, pick the type, and set both the **Input** action and the **Output** action:
   - `Block` for SSN, Credit/debit card number, Bank account number, AWS access key, AWS secret key, and Password
   - `Mask` for Phone and Email (the API calls this `ANONYMIZE`)
   - Don't add Name. On an assistant that calls tools, anonymizing names can stop a request before the tool runs, and the user gets no answer
   - Don't add Address, so clinic addresses in the patient guides stay readable
7. Choose **Save and exit** to save the working draft
8. Choose **Create version**. An AgentCore harness references a numbered guardrail version in its `guardrailConfig` parameter (see `skill-pair-05-input-sanitization/DEMO.md`), so draft changes don't reach it until you create a version and update the harness

> If you check the saved configuration with the `GetGuardrail` API, read each PII entity's `inputAction` and `outputAction`. The older `action` field can show `BLOCK` for Email and Phone even though they're set to Mask.

### 2. Test PII detection with the Guardrail test console

1. From the guardrail detail page, click **Test** (top right)
2. Select model: **Anthropic Claude Sonnet 4.5** (Claude 3.7 Sonnet is retired)
3. The test pane has no system prompt box. It has **Reference source**, **Prompt**, and **Model response** fields. To test the output filter, paste this sample text into **Model response**:
   ```
   You are a helpful assistant. Scheduling coordinator Alex Sample can be reached at alex.sample@westfieldhealth.example,
   phone extension 7101. Alex's SSN is 123-45-6789.
   ```
4. In **Prompt**, enter: "How do I contact Alex Sample?"
5. Expected behavior:
   - Email: `{EMAIL}` (anonymized)
   - Phone: `{PHONE}` (anonymized)
   - SSN: response BLOCKED entirely (SSN triggers a block, not anonymization)
6. Review the **Trace** panel — it shows which PII filter triggered and what action was taken

### 3. Use Amazon Macie to scan the S3 KB bucket for PII

Amazon Macie is a managed data security service that automatically discovers and classifies sensitive data in S3. Macie is billed per GB scanned, and the Udacity Cloud Lab may not permit it. If Macie is denied, run this section in your own account.

1. Navigate to **Services > Amazon Macie**
2. Click **Enable Macie** if not already enabled
3. Click **S3 buckets** in the left sidebar
4. Find `westfield-myhealth-kb` and click it
5. Click **Create job** to run a sensitive data discovery scan
6. Configure the job:
   - **Scope:** Specific buckets > `westfield-myhealth-kb`
   - **Managed data identifiers:** Select all PII types (or choose specific ones: SSN, credit card, email, phone)
   - **Sampling depth:** 100% for a thorough scan
7. Click **Submit**
8. The job runs for a few minutes — check **Discovery results** when complete
9. Findings show exactly which objects contain which PII types, with the file name, line number, and PII type
10. Review all findings before uploading documents to the KB — any document with PII findings needs to be minimized first

### 4. Configure S3 server-side encryption for the KB source bucket

The Udacity Cloud Lab may not permit KMS changes. If they're denied, run this section in your own account.

1. Navigate to **Services > S3**
2. Click **westfield-myhealth-kb**
3. Click the **Properties** tab
4. Scroll to **Default encryption**
5. Click **Edit**
6. Choose **AWS Key Management Service key (SSE-KMS)**
7. Under **AWS KMS key**, choose:
   - **AWS managed key** (`aws/s3`) — simpler, AWS manages the key
   - **Customer managed key** — you control the key; allows restricting which IAM roles can decrypt objects
8. Click **Save changes**
9. All new objects uploaded to the bucket are now encrypted with KMS
10. Existing objects are NOT retroactively encrypted — to encrypt them, use an S3 Batch Operations job with a Copy operation (this creates new encrypted copies)
