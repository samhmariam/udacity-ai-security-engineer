# Demo: Building an ML-BOM for a Production AI System

**Estimated Time:** 10 minutes

---

> **Note:** This demo uses **Aria**, the internal employee assistant of **Vantage Technologies**, the same system shown in the video. The goal is to show the concept working on a real deployment before you apply it to the exercise scenario. Everything you see here carries over to the scenario in `EXERCISE.md`.

> **Platform note for the video:** The video leaves the Claude version open ("4.5, 4.6 to 4.7 depending on what's available"). Aria runs **Claude Sonnet 4.5** on an Amazon Bedrock AgentCore harness, saved as `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. Amazon Bedrock no longer has a model access step, so read the model ID from the harness instead. Step 10 adds the harness components the video doesn't show. The template in the video also has different sections (Model Inventory, Embedding model, Data inventory, External services, IAM roles, Known risks). Use `starter/ML_BOM_TEMPLATE.md`, whose sections are listed in Step 1.

## Overview

In this demo, we build a partial Machine Learning Bill of Materials (ML-BOM) for a simple, single-model deployment — Claude Sonnet 4.5 accessed through Amazon Bedrock — to show exactly what the format captures and why it matters for security.

The goal is not to fill in every field perfectly. The goal is to surface the questions that the BOM forces you to ask, and to show how those questions connect directly to threat modeling. By the end, you will see why a traditional software SBOM is not enough for AI systems.

---

## Scenario

Vantage Technologies is early in its AI rollout. Before the knowledge base is connected, the security team has approved a simple use case: employees can query Aria, an internal chatbot powered by Claude Sonnet 4.5 through Amazon Bedrock.

The CISO pulls you into a meeting and asks:

> "What AI components are running in our environment right now, and what are their dependencies? If something goes wrong — a model update, a policy change, a jailbreak — how do I know what we're running and what it's capable of?"

Your answer is an ML-BOM. We are going to build one, live, for this single-model deployment.

---

## Tools Used

- The `ML_BOM_TEMPLATE.md` from `starter/` (we'll walk through its structure)
- The Aria harness configuration — the **Configs** panel in the Harness playground or the `GetHarness` API — to confirm the saved model ID and inference profile
- Anthropic model card documentation (linked in the template)

---

## Key Insights We'll Uncover

### 1. Why software SBOMs don't capture AI-specific risks

A traditional SBOM tells you what software packages are present and their versions. It does not tell you anything about training data, model lineage, embedding pipelines, or what a model is actually capable of generating. Two builds of the same application with identical SBOMs could behave completely differently if the underlying model changed. The ML-BOM exists to fill that gap.

### 2. What "model provenance" means and why it matters for security

Model provenance describes where a model came from — who created it, what it was trained on, whether it is a fine-tune of another model, and under what methodology it was aligned. For security purposes, provenance is the chain of custody for your AI component. If you cannot answer "where did this model come from and what was done to it," you cannot reason about its risk surface.

### 3. The managed service opacity problem

When you access Claude through Amazon Bedrock, you do not download a model — you call an API. Anthropic controls the model weights, the training data, the update schedule, and the alignment approach. AWS controls the infrastructure, the endpoints, and the access controls. You, as the customer, control almost nothing about the model itself.

This is the "managed service opacity" problem: the model can be updated or changed without your direct knowledge, and you have no visibility into training data or internal architecture details. The same applies to other managed parts of the system. Aria's Managed Knowledge Base, for example, uses a vector store you can't inspect directly. Your ML-BOM must document this opacity explicitly — it is a security condition, not just a documentation gap.

### 4. Why "intended use" and "out-of-scope use" are security controls

When we write down that Claude Sonnet 4.5's intended use is "natural language understanding and generation for internal employee Q&A," we are implicitly drawing a boundary. Anything outside that boundary — clinical advice, legal conclusions, real-time voice synthesis — is out of scope. Those boundaries become inputs to your threat model: what happens when a user tries to push the model across those lines? How do you detect it? How do you prevent it?

Intended use and out-of-scope use documentation is not corporate boilerplate. It is the starting point for your misuse section.

### 5. How misuse documentation maps to threat modeling

The misuse section of an ML-BOM lists the ways an attacker or a misguided user could abuse the model. For Claude Sonnet 4.5, the primary misuse vectors are prompt injection (crafting inputs to override system instructions) and jailbreaking (inputs designed to bypass safety guardrails). Documenting these here means they appear on your threat model. If they are not in the BOM, they are easy to forget.

---

## Step-by-Step Walkthrough

### Step 1 — Open the template and orient

Open `starter/ML_BOM_TEMPLATE.md`. Point out the major sections: Model Information, Training Datasets, Architecture Details, Model Lineage, Input/Output specs, Intended Use, Out of Scope Use, and Misuse.

Note that the template has two model sections (Model 1, Model 2) for systems with multiple models. We will only fill in Model 1 for this demo, then list the platform components in Step 10.

---

### Step 2 — Model Information

Fill in the following:

| Field | Value |
|---|---|
| Model Name | Claude Sonnet 4.5 |
| Version | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (US cross-Region inference profile, as saved on the harness) |
| Model Type | Text generation (decoder-only LLM) |
| Author/Organization | Anthropic |
| License | Commercial API — Anthropic usage policy |
| Source URL | https://docs.anthropic.com/en/docs/about-claude/models |

Point out: the "Source URL" here links to documentation, not downloadable weights. This is a managed service — there is nothing to download. That distinction matters.

Also point out: the saved ID depends on the inference option chosen when the harness was created. The model picker offers **US Anthropic Claude Sonnet 4.5** and **Global Claude Sonnet 4.5**, and the choice changes the `us.` or `global.` prefix. Record the exact string you read from the harness, not the one you expect.

---

### Step 3 — Training Datasets

| Field | Value |
|---|---|
| Dataset Name | Proprietary — not publicly disclosed |
| Source URL | N/A |
| License | N/A |
| Usage Notes | Trained on a large corpus of internet text, books, and code with RLHF and Constitutional AI alignment. Specific dataset composition is not disclosed by Anthropic. |

This is the opacity problem in action. We know the methodology (RLHF, Constitutional AI), but we cannot enumerate the training data. Document what you know; explicitly note what you cannot know.

---

### Step 4 — Architecture Details

| Field | Value |
|---|---|
| Architecture Type | Decoder-only transformer |
| Model Family | Claude Sonnet 4.5 (Anthropic Claude 4.5 generation) |

Note the alignment methodology: Constitutional AI (CAI) — a technique where the model is trained to critique and revise its own outputs against a set of principles. This is security-relevant because it affects how the model responds to adversarial prompts and why jailbreaking techniques that work on other models may behave differently here.

---

### Step 5 — Input/Output Specs

| Field | Value |
|---|---|
| Input Type | Text (system prompt + user messages) |
| Input Format | JSON via the Bedrock Converse streaming API (the harness saves `apiFormat` `converse_stream`) |
| Max Input Tokens | 200,000 (200K context window) |
| Output Type | Text |
| Output Format | JSON (message content blocks) |
| Max Output Tokens | Up to 64,000 |

The 200K context window is a security-relevant spec. An attacker who can stuff a large context can attempt to dilute system prompt instructions or exploit attention patterns. Document it.

---

### Step 6 — Intended Use

> Claude Sonnet 4.5 is intended for natural language understanding and text generation tasks in the context of internal employee Q&A. The model receives a system prompt establishing its role, a retrieved context window (in future RAG deployments), and a user question, then returns a grounded natural-language response.

---

### Step 7 — Out-of-Scope Use

- Clinical or medical decision-making
- Legal advice or conclusions
- Financial advice in regulated contexts
- Real-time voice synthesis or audio generation
- Autonomous decision-making without human review
- Use by or for customers outside the employee-facing internal tool

---

### Step 8 — Misuse / Malicious Use

- **Prompt injection:** Crafting user inputs that override or contradict the system prompt to change model behavior
- **Jailbreaking:** Inputs designed to bypass Constitutional AI safety training and elicit prohibited content
- **Training data extraction:** Prompts designed to get the model to reproduce memorized training data verbatim
- **Social engineering amplification:** Using the model to generate convincing phishing content or internal impersonation

---

### Step 9 — Connect to the threat model

Show how the misuse section maps directly to STRIDE threats from Skill Pair 1:

- Prompt injection → Elevation of Privilege, because the attacker's text takes over what the model does. Tampering applies when someone changes the input before it reaches the model, such as an application joining user input onto its system instructions before the API call.
- Jailbreaking → Tampering, Information Disclosure
- Training data extraction → Information Disclosure

This is not coincidental. A well-structured ML-BOM is designed to feed directly into threat modeling. The security artifacts are meant to talk to each other.

---

### Step 10 — Extend the BOM to Aria's platform components

Once Aria is connected to its knowledge base, the model is one row among many. On the AgentCore harness, record these components too:

| Component | Aria value | Why it belongs in the BOM |
|---|---|---|
| Harness | `VantageAria`. Model `us.anthropic.claude-sonnet-4-5-20250929-v1:0`, memory off, one tool (the gateway), system prompt, `maxIterations` 75, `timeoutSeconds` 3600, `sliding_window` truncation at 150 messages. A new version is created automatically with each update | The system prompt and limits define behavior and cost ceilings. The version number tells you what changed and gives you a rollback point |
| Inference profile | US cross-Region (`us.` prefix) | Requests may be processed in other US Regions. A lab invocation record from a us-east-1 harness showed `inferenceRegion: us-east-2`. This is a data residency fact |
| AgentCore Gateway | `vantage-aria-gateway`, target `aria-kb` (type Knowledge Base), exposed to the model as the tool `aria-kb___Retrieve` | It is the path retrieved content takes into the model's context |
| Managed Knowledge Base | `vantage-aria-kb`, S3 data source, managed vector store, managed parser, default chunking, on-demand sync | You can't inspect the vector store directly, so this is managed-service opacity again. Record what you can't see |
| Embedding model | Amazon Titan Text Embeddings V2, `amazon.titan-embed-text-v2:0` | It is the second model in the system (Model 2 in the template) |
| Source documents | S3 bucket `vantage-aria-kb-<suffix>`, versioning on | The documents decide what Aria says. Versioning lets you roll back a poisoned document |
| IAM roles | Harness default role `AmazonBedrockAgentCoreHarnessDefaultServiceRole-<suffix>`; gateway default role `AmazonBedrockAgentCoreGatewayDefaultServiceRole<timestamp>`; knowledge base service role (`AmazonBedrockExecutionRoleForKnowledgeBase_…`) | Each role is a separate blast radius. The harness default role can invoke all foundation models and doesn't include `bedrock:ApplyGuardrail` until you add it |
| Guardrail | `aria-production-guardrails`. At this point in the course it's version 1 and isn't attached. Lesson 11 creates version 2 and attaches it through the harness `guardrailConfig` additional parameter | Record the version and whether it's attached, because a new guardrail version changes behavior without changing the harness |
| Log groups | `/aws/bedrock/vantage-aria/invocations` (model invocation logs), `/aws/bedrock-agentcore/runtimes/harness_VantageAria-<id>-DEFAULT` (harness runtime), `/aws/vendedlogs/bedrock/knowledge-base/APPLICATION_LOGS/<kb-id>` (ingestion) | Invocation records contain the full system prompt and retrieved chunk text, so treat the log group as a sensitive data store |

Where to read each value: the harness **Configs** panel in the Harness playground or `GetHarness` for the model, prompt, and limits; the gateway detail page for the target; the knowledge base data source page for parsing, chunking, and sync; IAM for the roles.

---

## Key Takeaway

An ML-BOM is your AI system's security baseline. Without it, you cannot reason about what changed between deployments, what is in scope for security testing, or what the model is actually capable of. A traditional SBOM tells you what code is running. An ML-BOM tells you what your AI system knows, how it was trained, and how it is expected to behave — which is everything a security team needs to model threats against it.

When Aria expands to a full RAG system with two models, the BOM expands with it. That is exactly what you will build in the exercise.
