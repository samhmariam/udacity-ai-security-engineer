# Note to the Reviewer: Secure AI Deployment Project

Thank you for reviewing my project. This repository holds my work for the whole nanodegree. **The project for _Secure AI Deployment_ (Operation HealthGuard: AI Model Risk & Compliance Assessment) is entirely in [`04-secure-ai-deployment/project/starter/`](04-secure-ai-deployment/project/starter/).** Everything else belongs to other courses and can be ignored.

The three submission artifacts:
- [`governance_portfolio.xlsx`](04-secure-ai-deployment/project/starter/governance_portfolio.xlsx): all 8 tabs (D1–D8) completed;
- [`audit_notebook.ipynb`](04-secure-ai-deployment/project/starter/audit_notebook.ipynb): executed end to end, with all outputs saved;
- [`lab/`](04-secure-ai-deployment/project/starter/lab/): the four implemented modules. The pytest log is in [`results/pytest_run_log.txt`](04-secure-ai-deployment/project/starter/results/pytest_run_log.txt) (**34/34 passed**).

## Where to find each rubric item

| Rubric area | Evidence (tab → cells) |
|---|---|
| **EU AI Act classification** | **D1.** A6–E9: HIGH-RISK under Art. 6(1) + Annex I, Section A, point 11 (MDR), with Annex III 5(a) as secondary basis. Rows 14–24: all 11 Art. 9–15 obligations with status, severity and evidence or remediation. A27: three launch blockers tied to the brief's risk-appetite statement. |
| **GDPR / CPRA data-flow map** | **D2.** Rows 6–13: 8 stages, each with GDPR Articles, CPRA §1798 Sections, Met/Gap and a remediation note. A16–A17: the transfer mechanism and TIA answer, in a bottom line at the top. A19: top 5 risks, each linked to its D5 row. |
| **MITRE ATLAS threat model** | **D3.** A5: attack surface of Components 1–6. Rows 9–11: AML.T0020, AML.T0010, AML.T0024, each with scenario, mechanism-level mitigation and L/I. A14: prioritisation rationale. |
| **Technical audit** | `lab/` and the notebook fill **D4** rows 6–55: metrics, region and intersectional FNR, most-harmed cell, SHAP top-K, verdict `proxy_supported`. **A58–A59:** my proxy-bias narrative. Every figure in it is computed in notebook §6b. |
| **Risk register** | **D5** rows 7–18: 12 risks from D1–D4, each with L × I, NIST function and a named control. 5 Top-N risks are flagged in column K and highlighted. |
| **Model card** | **D6.** §4 and §5 SHAP (A18, A22) are written by the notebook from D4. §1–3, §5b limitations (A23), §6 (citing the D3 ATLAS IDs) and §7 are hand-written. |
| **KRI dashboard** | **D7.** Rows 6–8: three KRIs, with thresholds that mirror `lab/kri.py`. Rows 11–13: Status written by the notebook (KRI-1 **Red**, 43.4 pp). A16–A18: rationale and escalation. |
| **Launch decision** | **D8.** B5 and A10: **Conditional Go** plus a one-page executive brief. A13–A25: evidence citing D1–D7, residual risk against appetite, and 7 conditions (rows 18–24) with threshold, owner and timeline. Rows 28–39: RACI. |

**Headline finding:** the model misses 60.6% of diabetes cases in Rural × Medicaid patients, against 23.1% for Rural × Private. These patients are clinically comparable. The cause is historical under-diagnosis in the training labels, learned through `region` and `insurance_type`.

## To verify

```bash
cd 04-secure-ai-deployment/project
uv sync                                    # or: pip install -r requirements.txt
cd starter
uv run pytest lab/tests/ -v                # 34 passed
uv run jupyter nbconvert --to notebook --execute --inplace audit_notebook.ipynb
```

`requirements.txt` sits in `project/`, not in `starter/` as the starter README suggests.

## Changes from the starter you may notice

- **Dependency pins.** The provided `healthguard_model.joblib` was saved with numpy 2.x and scikit-learn 1.7.2, so it fails to load under the original `numpy==1.26.4` pin. I updated `numpy==2.0.2` and `scikit-learn==1.7.2` in `pyproject.toml`, `requirements.txt` and `uv.lock`.
- **Notebook additions.**
  - **Gaps filled in.** It now writes D4 B40/B41 and D6 §4/§5. The tabs mark these as notebook-filled, but the starter never wrote them.
  - **Display fix.** It shows a KRI value of `0.0` instead of "—".
  - **New §6b evidence cell.** It sits behind the D4 narrative.
  - **Comment fix.** The stale `(should be ~0.40)` FNR comment is replaced; the actual FNR is 0.256.
- **`lab/` and tests.** The `lab/` functions keep their signatures; a few optional, defaulted parameters were added. The tests and the `data/` folder are untouched.
- **D5 scores are stored values, not formulas.** openpyxl drops formula results, so formula scores would read as blank outside Excel.
- **D8 layout.** I widened it to four columns, so the conditions table and RACI are real tables. The decision date (B7) is the date I did the work, and every condition timeline is relative to it.
- **KRI-2 and KRI-3** show Green on the synthetic inputs hard-coded in the starter notebook. D7 and D8 say plainly that this is not production evidence.

[`project/FUTURE_UPGRADES.md`](04-secure-ai-deployment/project/FUTURE_UPGRADES.md) is optional reading. It is a design doc for four stand-out extensions and is not part of the graded work.
