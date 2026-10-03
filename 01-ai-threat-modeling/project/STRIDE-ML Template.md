# STRIDE-ML Threat Model Template

## Overview

STRIDE-ML extends the traditional STRIDE threat modeling framework to address threats specific to Machine Learning systems. This template helps identify security risks across both traditional application components and ML-specific attack vectors.

------------------------------------------------------------------------

## 1. System Overview

**System Name:** *\[Name of the system being modeled\]*

**Purpose:** *\[Brief description of what the system does and its business value\]*

**Architecture:** *\[High-level description of system components, data flow, and key technologies\]*

**Key Components:**

- *\[Component 1 and its role\]*
- *\[Component 2 and its role\]*
- *\[Component 3 and its role\]*

**Trust Boundaries:**

- *\[Boundary 1: e.g., User to Application\]*
- *\[Boundary 2: e.g., Application to Backend Services\]*
- *\[Boundary 3: e.g., Internal to External APIs\]*

------------------------------------------------------------------------

## 2. Data Assets

*\[Describe the sensitive data processed by the system, including data classifications and why each asset is valuable to an attacker. Include training data, inference data, model outputs, and any PII or confidential business information.\]*

------------------------------------------------------------------------

## 3. STRIDE-ML Threat Analysis

### 3.1 Spoofing

*\[Identify threats where an attacker could impersonate a legitimate user, service, or component. Consider both traditional identity spoofing and ML-specific threats like spoofed training data provenance.\]*

**\[Threat ID\]: \[Threat Name\]**

*\[Describe the threat scenario, how an attacker would exploit it, what components are affected, and the likelihood and impact. Then describe the mitigation.\]*

*Mitigation:* *\[Describe how this threat is addressed\]*

------------------------------------------------------------------------

### 3.2 Tampering

*\[Identify threats where an attacker could modify data, code, or model behavior. Consider data poisoning, adversarial examples, and manipulation of training pipelines.\]*

**\[Threat ID\]: \[Threat Name\]**

*\[Describe the threat scenario and its risk assessment\]*

*Mitigation:* *\[Describe how this threat is addressed\]*

------------------------------------------------------------------------

### 3.3 Repudiation

*\[Identify threats related to accountability and audit trails. Consider inability to attribute model decisions, lack of logging for training data changes, and unclear provenance of model outputs.\]*

**\[Threat ID\]: \[Threat Name\]**

*\[Describe the threat scenario and its risk assessment\]*

*Mitigation:* *\[Describe how this threat is addressed\]*

------------------------------------------------------------------------

### 3.4 Information Disclosure

*\[Identify threats where sensitive information could be exposed. Consider training data extraction, membership inference, model inversion, prompt leakage, and excessive data exposure through model outputs.\]*

**\[Threat ID\]: \[Threat Name\]**

*\[Describe the threat scenario and its risk assessment\]*

*Mitigation:* *\[Describe how this threat is addressed\]*

------------------------------------------------------------------------

### 3.5 Denial of Service

*\[Identify threats that could disrupt system availability. Consider resource exhaustion through expensive queries, adversarial inputs designed to slow processing, and rate limit exhaustion.\]*

**\[Threat ID\]: \[Threat Name\]**

*\[Describe the threat scenario and its risk assessment\]*

*Mitigation:* *\[Describe how this threat is addressed\]*

------------------------------------------------------------------------

### 3.6 Elevation of Privilege

*\[Identify threats where an attacker could gain unauthorized access or capabilities. Consider prompt injection, jailbreaking, and manipulation of model behavior to bypass access controls.\]*

**\[Threat ID\]: \[Threat Name\]**

*\[Describe the threat scenario and its risk assessment\]*

*Mitigation:* *\[Describe how this threat is addressed\]*

------------------------------------------------------------------------

## 4. Residual Risks

*\[Describe risks that remain even after mitigations are applied. These are risks that must be accepted, monitored, or addressed through compensating controls.\]*

**\[Risk Name\]:** *\[Description of the residual risk and why it cannot be fully eliminated\]*

------------------------------------------------------------------------

## 5. Recommendations

*\[Provide actionable recommendations for ongoing security posture, including monitoring, periodic reviews, and user education.\]*

------------------------------------------------------------------------

## 6. Sign-off

| Role          | Name | Date |
|---------------|------|------|
| Security Lead |      |      |
| ML Engineer   |      |      |
| System Owner  |      |      |

------------------------------------------------------------------------

## Appendix: Common ML Threat Categories

**Adversarial Attacks:** Inputs crafted to cause model misclassification or unexpected behavior.

**Data Poisoning:** Corrupting training or reference data to influence model behavior.

**Model Inversion:** Reconstructing sensitive training data from model outputs.

**Membership Inference:** Determining whether specific data was used to train a model.

**Prompt Injection:** Manipulating LLM inputs to override system instructions or extract information.

**Jailbreaking:** Bypassing model safety controls to generate prohibited content.

**Model Extraction:** Stealing model functionality through repeated queries.

------------------------------------------------------------------------

## References

- OWASP ML Security Top 10
- MITRE ATLAS (Adversarial Threat Landscape for AI Systems)
- NIST AI Risk Management Framework
