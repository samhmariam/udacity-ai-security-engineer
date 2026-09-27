# API Security Checklist — CaseAssist Bedrock Configuration

**Instructions:** Review the starter files (`app_config_review.py`, `iam_policy_overpermissive.json`, `bedrock_invocation.py`) and mark each item below as Pass, Fail, or N/A based on the current configuration. For any item you mark Fail, add a one-sentence note explaining what the problem is. For any item you mark N/A, add a one-sentence note explaining why it doesn't apply.

When you complete this checklist for your own project configuration, every item should be a Pass or a justified N/A before you submit.

---

## Credential Handling

- [ ] No hardcoded credentials in source code
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] IAM role used for authentication (not static access keys)
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] Credentials never written to logs or error output
  - Status: ___
  - Note (if Fail or N/A): ___

---

## Configuration Management

- [ ] Harness ARN stored in environment variable (not hardcoded in source)
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] Harness endpoint qualifier (if the app targets an endpoint other than DEFAULT) stored in environment variable (not hardcoded in source)
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] AWS region stored in environment variable (not hardcoded in source)
  - Status: ___
  - Note (if Fail or N/A): ___

---

## IAM Policy

- [ ] Minimum required IAM actions only (no wildcard actions such as `bedrock:*`, `s3:*`)
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] Resource ARNs are specific (no wildcards on sensitive resources)
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] No S3 access beyond what the application needs (not all S3 resources)
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] CloudWatch Logs access scoped to the minimum required actions
  - Status: ___
  - Note (if Fail or N/A): ___

---

## Input Handling

- [ ] Input length limits enforced at the application layer before invoking the harness
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] User input is not passed directly to the harness without any validation
  - Status: ___
  - Note (if Fail or N/A): ___

---

## Output and Error Handling

- [ ] Error responses do not expose stack traces or internal configuration details
  - Status: ___
  - Note (if Fail or N/A): ___

- [ ] Raw API response objects are not returned directly to the user interface
  - Status: ___
  - Note (if Fail or N/A): ___

---

## Logging and Observability

- [ ] Model invocation logging enabled in Bedrock settings
  - Status: ___
  - Note (if Fail or N/A): ___

---

## Transport Security

- [ ] HTTPS enforced for all API calls (handled automatically by the Bedrock SDK — confirm the SDK is used, not raw HTTP calls)
  - Status: ___
  - Note (if Fail or N/A): ___

---

## Summary

Total items: 16
Pass: ___
Fail: ___
N/A: ___

**Overall assessment:** ___
