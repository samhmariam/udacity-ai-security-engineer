# Lab Setup Guide

Everything you need runs locally — no API keys required.

**Estimated setup time: 15–20 minutes**

---

## Local Python 3.12 Environment with uv

For a local checkout, run these commands in PowerShell from this project folder:

```powershell
uv venv --python 3.12 --no-project .venv
uv sync --python 3.12 --locked
uv run python load_knowledge_base.py
uv run python northstar_agent.py --demo
```

Install Ollama and pull `mistral:7b-instruct-v0.2-q4_0` before running the agent.
The repository root excludes this folder from its uv workspace, so this project
uses its own `.venv` and `uv.lock`. The root `.gitignore` already ignores `.venv`.

To activate the environment for direct Python commands:

```powershell
.\.venv\Scripts\Activate.ps1
```

If recreating `pyproject.toml`, use `uv init --bare --python 3.12 --no-workspace`
followed by `uv add -r requirements.txt` to keep the project independent.

The steps below describe the provided Linux container setup.

---

## Step 1 — Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv curl git
```

---

## Step 2 — Install Python Packages

```bash
sudo pip3 install pysqlite3-binary chromadb requests Pillow sentence-transformers
```

---

## Step 3 — Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sudo sh
```

Start it:

```bash
sudo ollama serve &
```

Wait a few seconds, then confirm it is running:

```bash
curl http://localhost:11434/api/tags
```

---

## Step 4 — Pull the Model

```bash
sudo ollama pull mistral:7b-instruct-v0.2-q4_0
```

This is about 4 GB and may take a few minutes. Confirm it downloaded:

```bash
sudo ollama list
```

---

## Step 5 — Load the Knowledge Base

```bash
cd /project
sudo mkdir -p student_work/attacks student_work/defenses student_work/reports
sudo python3 load_knowledge_base.py
```

The `student_work/` folders are where every deliverable you submit will live. Run
all project commands from `/project` — the agent resolves `chroma_data/` and
`knowledge_base/` relative to your current directory.

Expected output:
```
Loading Northstar knowledge base...
  Added: northstar-ai-policy
  Added: security-incident-proc
  Added: acceptable-use-guidelines
Knowledge base ready. 3 documents loaded.
```

---

## Step 6 — Verify the Agent

```bash
sudo python3 northstar_agent.py --demo
```

If you see a response with no unauthorized commands executed, you are ready to begin.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ollama not responding | `sudo pkill -f 'ollama serve'` then restart |
| ChromaDB sqlite3 error | `sudo pip3 install pysqlite3-binary` |
| Model not found | `sudo ollama pull mistral:7b-instruct-v0.2-q4_0` |
| Permission errors | `sudo chmod -R 777 /project/student_work/` |
