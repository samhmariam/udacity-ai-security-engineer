# AI System Compromise & Resilience Assessment (Finance Edition)

Capstone project for the Udacity AI Security nanodegree. You take the role of a **Junior AI Red Team Operator** at FinanceGuard Inc. and execute 5 adversarial attacks against a financial AI system (a receipt classifier and an expense-policy RAG chatbot).

> Full step-by-step instructions and the grading rubric live in the Udacity classroom. This repo contains only the scaffolded code and templates you'll work in.

## Repository Layout

```
.
├── starter/             # Scaffolded project files — work here
│   ├── classifier/      # Receipt CNN (given: model, train, evaluate, pretrained ckpt)
│   ├── attacks/         # 5 attack scripts — YOU IMPLEMENT
│   ├── rag_chatbot/     # Expense chatbot (given: app, rag, index, policies)
│   ├── docs/            # Documentation templates — YOU FILL IN
│   ├── .env.example     # API key configuration template
│   ├── 06_trivy_report.json
│   ├── requirements.txt # Pinned Python dependencies
│   └── Dockerfile
├── LICENSE.txt
└── CODEOWNERS
```

## The 5 Attacks

| # | Attack | Target | Objective |
|---|--------|--------|-----------|
| 1 | FGSM Evasion | Receipt Classifier | Craft adversarial images that fool the classifier |
| 2 | Label-Flip Poisoning | Training Pipeline | Corrupt training data to degrade model accuracy |
| 3 | Prompt Injection | RAG Chatbot | Override system instructions to manipulate behavior |
| 4 | Data Exfiltration | RAG Vector Store | Extract confidential documents through the chatbot |
| 5 | Supply Chain Analysis | Docker / Dependencies | Identify vulnerabilities via Trivy report and Dockerfile review |

## Getting Started

### Udacity Workspace

The starter files are pre-loaded and dependencies are pre-installed. Skip ahead to the verification steps in the classroom instructions.

### Local Setup

Targets **Python 3.12.13**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

Configure your classroom API key:

```bash
cp starter/.env.example starter/rag_chatbot/.env
# edit starter/rag_chatbot/.env to set OPENAI_API_KEY and OPENAI_BASE_URL
```

Verify the provided model and chatbot work end-to-end:

```bash
cd starter/classifier
python evaluate.py --model-path checkpoints/receipt_cnn_clean.pt --test-dir balanced_data/test
# Expected: ~94% accuracy

cd ../rag_chatbot
python build_index.py
python app.py &
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the meal expense limit?"}'
```

## What You Implement vs. What's Given

**You implement** — the 5 attack scripts in `starter/attacks/`.

**Given to you** — do not modify the classifier, RAG chatbot, policy documents, Trivy report, or Dockerfile. They are the system under test.

**You write** — the documentation in `starter/docs/` (Red Team Charter, Vulnerability Log, per-attack results, Executive Risk Summary, Reproduction Steps) using the provided templates.

## Deliverables

1. 5 completed attack scripts in `starter/attacks/`
2. Filled-in documentation files in `starter/docs/`
3. Attack output files (JSON results from running your scripts)

Grading criteria are in the classroom rubric.

## License

[License](LICENSE.txt)