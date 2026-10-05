# Note to the Reviewer: LLM Red Teaming Project

Thank you for reviewing my project. This repository holds my work for the whole nanodegree. **The project for _LLM Red Teaming_ (AI System Compromise & Resilience Assessment, Finance Edition) is entirely in [`02-llm-red-teaming/project/`](02-llm-red-teaming/project/).** Everything else in the repository belongs to other courses and can be ignored.

Inside the project:
- the written deliverables are in [`starter/doc_delivery/`](02-llm-red-teaming/project/starter/doc_delivery/),
- the five attack scripts are in [`starter/attacks/`](02-llm-red-teaming/project/starter/attacks/),
- their raw outputs (JSON and PNG) are in [`starter/attacks/results/`](02-llm-red-teaming/project/starter/attacks/results/).

You don't need to run anything to review the work. Every number in the documents traces back to a file in `results/`.

## Where to find each rubric item

| Rubric area | Evidence |
|---|---|
| **Red Team Planning** | [Charter](02-llm-red-teaming/project/starter/doc_delivery/charter_delivered.md): engagement details, 5 objectives, in-scope and out-of-scope systems, 9 rules of engagement, a numeric success criterion for each attack |
| **FGSM evasion** | [`01_fgsm_evasion.py`](02-llm-red-teaming/project/starter/attacks/01_fgsm_evasion.py) · [results](02-llm-red-teaming/project/starter/doc_delivery/fgsm_results_delivered.md): 6 ε values, accuracy 94.4% → 27.2%, side-by-side images · `results/01_fgsm/fgsm_results.json` |
| **Label-flip poisoning** | [`02_label_flip_poisoning.py`](02-llm-red-teaming/project/starter/attacks/02_label_flip_poisoning.py) · [results](02-llm-red-teaming/project/starter/doc_delivery/poisoning_results_delivered.md): 10% flip rate, training split only, clean vs. poisoned on all 4 metrics · `results/02_label_flip/*/metrics.json` |
| **Prompt injection** | [`03_prompt_injection.py`](02-llm-red-teaming/project/starter/attacks/03_prompt_injection.py) · [transcript](02-llm-red-teaming/project/starter/doc_delivery/prompt_injection_transcript_delivered.md): 5 techniques, with injection success (0/5) and confidential source disclosed (2/5) counted separately · `results/03_prompt_injection/` |
| **Data exfiltration** | [`04_data_exfiltration.py`](02-llm-red-teaming/project/starter/attacks/04_data_exfiltration.py) · [evidence](02-llm-red-teaming/project/starter/doc_delivery/data_exfiltration_evidence_delivered.md): 6 strategies, **6/6 exfiltrated**, root cause analysis at the architecture level · `results/04_exfiltration/` |
| **Supply chain** | [`05_supply_chain_analysis.py`](02-llm-red-teaming/project/starter/attacks/05_supply_chain_analysis.py) · [analysis](02-llm-red-teaming/project/starter/doc_delivery/supply_chain_analysis_delivered.md): 804 findings (0 critical, 34 high), 6 Dockerfile issues each with a fix, prioritized plan · `results/05_supply_chain/supply_chain_report.json` |
| **Reporting** | [Vulnerability Log](02-llm-red-teaming/project/starter/doc_delivery/vulnerability_log_delivered.md) (VUL-001 to VUL-005, with severity justifications) · [Executive Summary](02-llm-red-teaming/project/starter/doc_delivery/executive_summary_delivered.md) · [Reproduction Steps](02-llm-red-teaming/project/starter/doc_delivery/reproduction_steps_delivered.md) |
| **Best practices** | All 5 scripts run with their default arguments and exit with code 0 (re-checked on 2026-10-05). The commands and expected output are in the Reproduction Steps |

## Things that may help when reading

- **Poisoning reached a 3.3-point accuracy drop, not the rubric's 5.** At the maximum allowed 10% flip rate, accuracy fell 3.33 points compared with a clean model I retrained on the same hardware, and 2.82 points compared with the provided checkpoint. Recall fell 7.7 points, and rejected genuine receipts nearly doubled (17 → 32). I also tried 5%, and two one-way variants that spend the whole 10% on a single class; none reached 5 points. All runs are documented, with the reasons, in the poisoning results. I report the shortfall rather than tuning seeds until a run happened to clear it.
- **Why there is a second clean baseline.** The provided checkpoint was trained on Apple MPS, and my poisoned models were trained on CPU. On its own, the poisoned model scored *higher* than the provided checkpoint. So I retrained a clean model with the same script and hardware and used that as the fair baseline. Both baselines are reported.
- **FGSM accuracy rises again at ε = 0.15.** It falls steadily from ε = 0 to 0.10 (94% → 27%), then climbs back to 45% at ε = 0.15. This is the known overshoot of a single-step attack: the noise becomes so heavy that images read as "non-receipt" again. The FGSM results document breaks this down by class.
- **Prompt injection: the model held, but the system leaked.** No injection got past the model, and that held across 3 runs. Two attempts still pulled the confidential document into the model's context and listed it in `sources`. I treat that as the more important finding, and it leads into the 6/6 exfiltration result.
- **Analysis beyond the scripts.** Two sets of figures come from extra checks rather than the attack scripts:
  - The supply-chain analysis adds a `pip-audit` of `requirements.txt`. Trivy didn't cover the app's own libraries, and the audit found torch CVE-2025-32434 and the Pillow advisories.
  - The per-class and image-distortion (PSNR) breakdown in the FGSM results came from a one-off diagnostic script that isn't in the repository.

  The headline numbers come from the submitted scripts, and both documents say which figures come from these extra checks.
- **What is and isn't committed.**
  - **Committed:** the result JSON files. The project `.gitignore` excludes `*.json`, so I added them explicitly.
  - **Not committed (git-ignored):** retrained checkpoints (`*.pt`), the poisoned dataset copy, the FAISS index and `rag_chatbot/.env`. The Reproduction Steps regenerate everything.
  - **No credentials** are in the repository.
- **Data.** The "confidential" executive compensation document is the fictional course data, but the reports treat it as real restricted data.
