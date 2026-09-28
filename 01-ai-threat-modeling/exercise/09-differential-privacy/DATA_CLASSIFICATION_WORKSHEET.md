# Data Classification Worksheet — Westfield Health Knowledge Base Review

**Your Name:** ___________________________________
**Date:** ___________________________________

The six documents to review are in `starter/documents_to_classify_myhealth/`.

---

## Task 1: Document Classification Table

For each document, specify the classification level, whether to include it in the KB, and your reasoning. Classify each document for the MyHealth Assistant audience: authenticated patients.

| Document | Classification | Include in KB? | Fields/Columns to Remove | Reason |
|---|---|---|---|---|
| `appointment_scheduling_guide.txt` | | | | |
| `discharge_and_medications_guide.txt` | | | | |
| `patient_access_center_procedures.txt` | | | | |
| `payer_contract_rates.txt` | | | | |
| `staff_directory.csv` | | | | |
| `discharge_followup_call_log.csv` | | | | |

**Classification levels:** Public / Internal / Confidential / Restricted

**Include in KB?:** Yes / No / Modified

---

## Task 2: Staff Directory Column Removal

The full staff directory, `staff_directory.csv`, has these 8 columns:

```
employee_id, full_name, email, phone_extension, department, manager_name, office_location, salary_band
```

**2a. Which columns should be removed before uploading to a patient-facing KB? For each, explain the specific privacy or safety risk in a patient-facing context.**

List each column you would remove, with its risk. Add as many entries as you need.

Column:

> _Your answer_

Column:

> _Your answer_

**2b. Write the minimized CSV header (only the columns that remain):**

```
(your answer)
```

---

_Continue to `GUARDRAIL_PII_CONFIG.md` for Tasks 3 and 4._
