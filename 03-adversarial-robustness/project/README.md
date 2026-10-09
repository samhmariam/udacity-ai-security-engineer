# Northstar Research Agent
### Red Team and Harden a RAG-Enabled AI Agent

---

## Your Mission

You are an AI Security Engineer at **Northstar Technologies**. Leadership is about to launch the **Northstar Research Agent** — an internal AI assistant that can search internal documents, create support tickets, and save research notes.

Before it goes live, your job is to **find the vulnerabilities, prove they work, and fix them**.

---

## How This Project Works

| Phase | What You Do | Time |
|-------|------------|------|
| 1 — Review & Assess | Read the code, map risks using OWASP LLM Top 10 | ~1 hr |
| 2 — Attack | Run direct injection, RAG poisoning, and task hijacking attacks | ~1.5 hrs |
| 3 — Defend | Harden the prompt, secure the RAG pipeline, restrict tool access | ~1.5 hrs |
| 4 — Report | Validate your defenses and write the launch readiness report | ~1 hr |

---

## Getting Started

```bash
# 1. Confirm the agent is running
sudo python3 northstar_agent.py --demo

# 2. Load the knowledge base
sudo python3 load_knowledge_base.py

# 3. Read the full project guide
cat PROJECT_GUIDE.md
```

---

## What You Will Submit

| Deliverable | File |
|-------------|------|
| OWASP risk assessment | `student_work/reports/owasp_assessment.md` |
| Security findings report | `student_work/reports/security_findings.md` |
| Hardened agent code | `student_work/defenses/northstar_agent_hardened.py` |
| Hardened system prompt | `student_work/defenses/system_prompt_hardened.txt` |
| Incident response playbook | `student_work/reports/ir_playbook.md` |
| Launch readiness report | `student_work/reports/launch_readiness_report.md` |

---

## Tools

- **Ollama + Mistral 7B** — local LLM, no API key needed
- **ChromaDB** — vector store for RAG
- **Python 3** — all code is plain Python
- **OWASP LLM Top 10** — your assessment framework

---

## A Note on Ethics

All attacks in this project target only the local application on your machine. Do not use these techniques against real AI systems without authorization.
