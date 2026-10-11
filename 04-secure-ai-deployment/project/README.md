# Operation HealthGuard — AI Model Risk & Compliance Assessment

You take the role of Chief AI Risk Officer at Klariova Health and produce a complete pre-launch governance, risk, and compliance review of **HealthGuard** — a diabetes-risk prediction model — covering EU AI Act compliance, fairness auditing, threat modeling, and a launch recommendation.

## Getting Started

### Dependencies

- Python 3.10+
- scikit-learn ≥ 1.7
- pandas ≥ 2.0
- numpy ≥ 1.24
- matplotlib ≥ 3.7
- shap ≥ 0.46
- fairlearn ≥ 0.10
- joblib ≥ 1.3
- openpyxl ≥ 3.1
- jupyter ≥ 1.0
- pytest ≥ 7.0
- nbformat ≥ 5.9
- nbclient ≥ 0.10

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/udacity/ai-sec-eng-c4-cd15150-project-starter.git
   cd ai-sec-eng-c4-cd15150-project-starter/starter
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the audit notebook:
   ```bash
   jupyter notebook audit_notebook.ipynb
   ```

## Project Structure

```
starter/
├── audit_notebook.ipynb        Orchestrator notebook — runs lab/ code, writes to Excel
├── governance_portfolio.xlsx   The deliverable Excel workbook (8 tabs)
├── data/                       Read-only inputs
│   ├── case_study_brief.md       Scenario description — read this first
│   ├── healthguard_model.joblib  Pre-trained scikit-learn pipeline
│   ├── train.csv / test.csv      Synthetic patient datasets
│   └── data_flow_diagram.png     Pre-drawn DFD for annotation
├── lab/                        Code modules to implement
│   ├── fairness_metrics.py       FNR, FPR, selection rate, parity metrics
│   ├── audit.py                  Subgroup, intersectional, and proxy analysis
│   ├── shap_analysis.py          SHAP explainer setup and proxy detection
│   ├── kri.py                    Key Risk Indicator functions
│   └── tests/                    34 unit tests (read-only)
└── results/                    Output directory for exported charts
```

## Testing

Run all 34 unit tests from the `starter/` directory:

```bash
pytest lab/tests/ -v
```

All tests will fail initially — they pass as you implement each module.

### Test Breakdown

| Test file | Covers | What it validates |
|---|---|---|
| `test_fairness_metrics.py` | `fairness_metrics.py` | FNR, FPR, selection rate, demographic parity diff, equalized odds diff — including edge cases |
| `test_audit.py` | `audit.py` | Subgroup metric computation, intersectional pivots, small-n filtering, proxy-pathway testing |
| `test_shap_analysis.py` | `shap_analysis.py` | SHAP explainer initialization, proxy-feature detection logic |
| `test_kri.py` | `kri.py` | Three KRI functions with Green/Amber/Red thresholds and edge cases |

## Project Instructions

### Track A — Code (~2 hours)

Implement the four modules in `lab/`. Run unit tests after each function:

```bash
pytest lab/tests/test_fairness_metrics.py -v
```

### Track B — Governance Portfolio (~3.5 hours)

Populate all 8 tabs in `governance_portfolio.xlsx`:

| Tab | Source | Content |
|---|---|---|
| D1 EU AI Act | Hand | Risk-tier classification + obligations gap analysis |
| D2 DFD Compliance | Hand | Annotated data flow diagram + obligation table |
| D3 ATLAS | Hand | 3 analyzed MITRE ATLAS TTPs |
| D4 Technical Audit | Code | Performance, subgroup tables, proxy hypothesis |
| D5 Risk Register | Hand + Code | ≥10 risks across ≥4 source outputs |
| D6 Model Card | Hand + Code | Performance, subgroup analysis, explainability |
| D7 KRI Dashboard | Code | Three KRIs with status from `kri.py` |
| D8 Launch Decision | Hand | Executive brief + detailed justification + RACI |

### Submission

- [ ] `pytest lab/tests/ -v` — 34 tests pass
- [ ] `audit_notebook.ipynb` runs end-to-end without error
- [ ] All 8 tabs in `governance_portfolio.xlsx` populated
- [ ] `lab/` folder contains your implementations

## License

[License](LICENSE.txt)
