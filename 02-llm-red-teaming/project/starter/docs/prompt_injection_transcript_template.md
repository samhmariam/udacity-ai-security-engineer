# Prompt Injection Transcript

## Summary

- **Target:** FinanceGuard Expense RAG Chatbot
- **Techniques tested:**
- **Successful prompt injections:** ___ / ___
- **System prompt extraction:** <!-- result + retrieval level (full/partial/none) -->
- **Confidential source disclosed in retrieval sources:** ___ / ___ attempts
- **Results file:** `../attacks/results/03_prompt_injection/prompt_injection_results.json`

<!-- Note: "injection successful" and "confidential source disclosed" are
     separate signals. A response can refuse the malicious request while the
     RAG retriever still surfaces a confidential document. Track both. -->

## Attempt 1: [Name] — [SUCCESS/BLOCKED]

**Prompt:**
> [Your injection prompt]

**Response:**
> [Chatbot response]

**Sources:**
<!-- list the source filenames returned in the `sources` field -->

**Matched indicators:**
<!-- list the success_indicators that appeared in the response, or "None" -->

<!-- For the system prompt extraction attempt only: -->
**System prompt retrieval level:** <!-- full / partial / none -->

**Confidential source disclosed:** <!-- Yes (and which file) / No -->

**Analysis:**
<!-- Why did this succeed/fail? Did the model misbehave, did the retriever leak, both, or neither? -->

---

## Attempt 2: [Name] — [SUCCESS/BLOCKED]

**Prompt:**
> [Your injection prompt]

**Response:**
> [Chatbot response]

**Sources:**

**Matched indicators:**

**Confidential source disclosed:**

**Analysis:**

---

<!-- Repeat for all 5 attempts -->

## Key Findings

<!-- Summarize:
1. Which techniques worked best and why?
2. What defenses did the chatbot have?
3. What does this tell you about prompt-level security?
-->
