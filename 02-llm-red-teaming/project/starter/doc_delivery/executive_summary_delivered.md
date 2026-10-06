# Executive Risk Summary

**To:** CISO and Executive Leadership, FinanceGuard Inc.
**From:** AI Red Team (Samuel H. Mariam)
**Date:** 2026-10-05
**Classification:** Internal: Restricted (contains references to confidential HR data)

## Overview

We tested FinanceGuard's two expense AI systems, the **receipt checker** that decides whether an uploaded image is a valid receipt and the **policy chatbot** that answers employee expense questions, together with the **software package used to deploy them**. We ran five realistic attacks in an isolated test environment with no production impact. **Overall risk: HIGH, with one CRITICAL finding that needs action this week.** Any employee can obtain the company's confidential executive pay data from the policy chatbot simply by asking for it, and we did so in 6 of 6 attempts. The receipt checker can be fooled by image changes a reviewer would not notice, and quietly corrupting a small part of its training data teaches it to approve non-receipts. The deployment package exposes a live service password and runs with more privileges than it needs. The chatbot resisted every attempt to override its instructions, which is good news, but that resistance did not stop the data leak.

## Risk Dashboard

| System | Risk Level | Key Finding |
|--------|-----------|-------------|
| RAG Chatbot (policy assistant) | **CRITICAL** | Confidential executive compensation data (salary bands, bonus formulas, stock option terms) disclosed to anyone who asks; 6 / 6 attempts succeeded |
| Receipt Classifier | **HIGH** | Images altered in ways invisible to a reviewer cause genuine receipts to be rejected and some non-receipts to be accepted (accuracy 94% → 51%). Separately, corrupting under 10% of its training data made it approve about 1 in 6 non-receipts |
| Deployment Infrastructure | **HIGH** | The deployment package would contain the live AI-service password, runs with full administrator rights, and uses software with a known takeover flaw |

## Findings Summary

### 1. Confidential pay data exposed through the chatbot — CRITICAL

**What we found:** The chatbot was given the restricted *Executive Compensation & Bonus Structure* document alongside the public expense policies, with nothing to control who may see it. Ordinary questions such as *"How does FinanceGuard structure incentive pay for senior leadership?"* returned salary ranges for every executive level (VP through CEO), bonus percentages and formulas, the stock option price and vesting terms, and the clawback policy. In one answer the bot even stated the document was "restricted to the Compensation Committee and CHRO only" and then summarised it anyway.

**Business Impact:**
- **Confidential HR data has been exposed.** Executive pay data could reach any employee, contractor or attacker with access to the chatbot. That creates pay-equity and morale problems, gives recruiting competitors an advantage, and may create legal or regulatory exposure, since equity terms can be market-sensitive.
- **The leak looks like normal use.** No special skill is needed, and nothing currently detects it, so we cannot rule out that it has already happened.
- **The problem is how the system was built, not one bug.** Restricted and public information share one knowledge store with no access rules. Adding warnings to the AI's instructions will not fix it.

### 2. Receipt checker can be fooled by invisible image changes — HIGH

**What we found:** Making small, deliberate changes to an image's pixels, invisible on casual inspection, dropped the checker's accuracy from 94% to roughly a coin toss (51%). With slightly stronger changes, still easy to pass off as a grainy phone photo, almost every genuine receipt was rejected and up to 45% of non-receipt images were accepted as receipts.

**Business Impact:**
- **Fraud risk.** If receipt approval is automated or reviewers trust the checker's verdict, employees could get unsupported or doctored receipts approved.
- **Disruption risk.** A malicious actor could cause genuine receipts to be rejected, creating reimbursement delays, manual-review backlogs and employee frustration.
- **Human review is not a reliable safety net.** The damaging changes fall below what a reviewer would notice, so reviewers must check what the image actually shows, not just the system's verdict.

### 3. Insecure deployment package — HIGH

**What we found:** The way the system is packaged for deployment would bundle the **live password for the external AI service** inside the package. The service runs with **full administrator rights**. It relies on an outdated version of a core AI library with a known flaw that lets a tampered model file take control of the system. The automated security scan flagged 804 issues, but most come from unnecessary build tools that can simply be removed. The more important problems are the ones the scan under-weighted or missed.

**Business Impact:**
- **Stolen credentials.** Anyone who obtains a copy of the package could use FinanceGuard's AI-service account, running up costs and gaining access to whatever is sent to the provider.
- **Full takeover from a single weakness.** One exploitable flaw would hand an attacker full control: they could steal data, silently replace the AI models, or change the policies the chatbot gives employees.
- **Low cost to fix.** The fixes are standard practice and inexpensive.

### 4. Training data can be quietly corrupted to approve non-receipts — HIGH

**What we found:** Someone with access to the receipt checker's training data mislabelled fewer than 10% of the examples. They chose them carefully, using the checker itself to pick the clearest examples. The images themselves were unchanged. The retrained checker went from accepting about 1 in 65 non-receipt images as receipts to **about 1 in 6**, and its overall accuracy fell from 95% to 88%. Mislabelling the same number of examples at random did only about half the damage.

**Business Impact:**
- **A lasting fraud path.** Once the checker is retrained on the corrupted data, ordinary non-receipt images get approved as receipts, with no further effort by the attacker.
- **Hard to notice.** The corrupted examples look exactly like genuine ones, and the checker actually rejects *fewer* real receipts, so it appears to be working better.
- **An insider or supply-chain risk.** It requires someone who can change the training data, so access control and change tracking on that data are the key defences.
- **Targeted attacks are the realistic threat.** A careful attacker achieves much more with the same small effort, so the size of a data change is not a good guide to its risk.

### 5. Chatbot relies on the AI alone to resist manipulation — MEDIUM

**What we found:** We tried five standard techniques to make the chatbot ignore its rules, reveal its instructions, adopt a new persona or repeat false policy. It refused every time across repeated tests. However, some of these attempts still caused the confidential document to be pulled into the AI's working memory and its file name to be shown to the user. Feeding the bot a fake "policy update" also stopped it giving the correct answer.

**Business Impact:**
- **Protection we don't control.** Today's protection depends entirely on the behaviour of a third-party AI model, which can change without notice when the provider updates it.
- **No backstop.** There is no independent safeguard if the model's behaviour changes.
- **Accurate answers can be blocked.** Contradictory claims can stop employees getting correct policy guidance.

## Prioritized Remediation

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 1 | **Remove the confidential compensation document from the chatbot now** and stop showing document names in answers. Notify the CHRO and Compensation Committee, and review usage logs for past exposure | **Low** (hours) | **Critical:** closes the active data leak immediately |
| 2 | **Secure the deployment package:** remove the bundled password and rotate it, run without administrator rights, update the vulnerable AI and image libraries | **Low–Medium** (days) | **High:** prevents credential theft and full system takeover |
| 3 | **Add user sign-in and access rules to the chatbot,** so each person retrieves only documents they are entitled to see; add an automatic filter that blocks restricted figures in answers | **Medium** (2–4 weeks) | **High:** permanent fix for the data leak; allows restricted content to be served safely to authorised staff later |
| 4 | **Stop fully automated receipt decisions:** send borderline and low-confidence cases to human review, and add independent checks (reading the amount, merchant and date; duplicate detection) | **Medium** (weeks) | **High:** removes the fraud path while the model is hardened |
| 5 | **Harden the receipt checker** against manipulated images (robustness training, image clean-up before analysis) | **Medium–High** (1–2 months) | **Medium–High:** reduces fraud and rejection-attack success |
| 6 | **Protect the AI supply chain:** lock down and track who can change training data and models, digitally verify model files before use, and add checks that compare each new model's per-category accuracy with the previous one | **Medium** (1–2 months) | **High:** closes the training-data fraud path and prevents silent model tampering |
| 7 | **Make AI security testing routine:** re-run these five attacks automatically whenever models, documents or software change | **Low** (once the above is in place) | **Medium:** catches regressions before they reach employees |

## Conclusion

FinanceGuard's expense AI works well under normal conditions. It was not built with an attacker in mind, and in one case the harm is already within reach of any user. **Our top recommendation is to remove the executive compensation document from the policy chatbot today** and treat its contents as potentially exposed. That single low-effort step closes the only CRITICAL finding. It should be followed within days by securing the deployment package and rotating the exposed service password.

More broadly, the AI model itself was often the *strongest* part of the system, refusing every manipulation attempt. The failures came from **missing traditional controls around it**: access rules, least-privilege deployment, change control over data and models, and human oversight of automated decisions. Funding those controls, rather than relying on the AI to protect itself, will give the greatest risk reduction for the investment. We recommend a follow-up assessment once priorities 1–4 are complete.

*Supporting detail: [Vulnerability Log](vulnerability_log_delivered.md) · [Reproduction Steps](reproduction_steps_delivered.md) · per-attack reports in `doc_delivery/`.*
