# HealthGuard Governance Portfolio: Future Upgrades

Design specs for four upgrades that go beyond the rubric. Each one deepens a finding the portfolio already makes, rather than adding a new topic.

| # | Upgrade | Builds on | Effort | Priority |
|---|---|---|---|---|
| U1 | Counterfactual retrain: drop proxy features, re-measure the most-harmed FNR | D4 verdict, D8 condition C1 | M (½ day) | **1st** |
| U2 | Fourth threat on the human override path, traced to a new KRI | D3, D5, D7, `lab/kri.py` | M (½–1 day) | 2nd |
| U3 | Serious-incident reporting workflow as a D8 appendix | D7 escalations, D8 conditions | S–M (2–3 h) | 3rd |
| U4 | Transfer Impact Assessment template attached to the RoPA | D2 Section B | M (3–4 h) | 4th |

**Why this order.** U1 can change the central finding. If removing the proxy features does not close the gap, the D4 narrative, D5 RR-01, the D6 limitations section and D8's C1 all need revising, so it should run before anything else is built on top. U2 adds the KRI that U3 uses as an incident trigger. U4 stands alone.

---

## Current baseline (what the upgrades are measured against)

Numbers come from `audit_notebook.ipynb` (test n = 3,000, threshold 0.26) and are recorded in the `04_D4_Technical_Audit` tab.

| Metric | Value |
|---|---|
| ROC AUC / recall / overall FNR | 0.812 / 0.744 / 25.6% |
| Most-harmed cell (n_pos ≥ 20) | Rural × Medicaid, FNR **60.6%** (n_pos 33, Wilson 95% CI 44–75%) |
| Comparator | Rural × Private, FNR 23.1% (n_pos 52, CI 14–36%) |
| Proxy-pathway verdict | `proxy_supported` (+37.5 pp within Rural vs −5.2 pp in Urban) |
| KRI-1 Subgroup FNR Drift | **Red**, 43.4 pp |
| SHAP evidence | region + insurance_type = −0.59 log-odds in Rural × Medicaid/Uninsured vs +0.15 in Urban × Private |

The current evidence for the proxy finding is **attributional** (SHAP). U1 adds **interventional** evidence.

---

## Guardrails: keep the submission valid

Every upgrade must keep these true. Check them before committing.

- [ ] `pytest lab/tests/ -v` still reports **34 passed**. Put new tests in **`lab/tests_extra/`**, so the rubric's 34-test count does not change. Run them with `pytest lab/tests_extra/ -v`.
- [ ] `audit_notebook.ipynb` runs end to end with every output visible: `jupyter nbconvert --to notebook --execute --inplace audit_notebook.ipynb`.
- [ ] The notebook's write targets stay put: D4 rows 6–55, D6 `A18`/`A22`, D7 rows 11–13. New content goes in **free** rows; never move existing blocks.
- [ ] Hand-written cells the notebook does not touch stay intact: the D4 narrative (`A58:A59`), D6 `A23`, D7 `A16:A18`.
- [ ] No `[bracketed]` placeholders anywhere. Every new figure is computed in the notebook, not typed by hand.
- [ ] D5 Risk Scores stay stored as **values**, not formulas. openpyxl drops formula results, so formula scores are invisible outside Excel.

---

## U1: Counterfactual retrain (proxy-feature ablation)

**Goal:** turn "SHAP attributes the gap to region and insurance_type" into "removing them changes the gap by X pp," with an uncertainty interval and a decision rule fixed before any results are seen. This also delivers the "ablation result" milestone in D8 condition **C1** (due at T+30 days).

### Experimental design

| Variant | Features dropped | Purpose |
|---|---|---|
| A0 | none (retrained locally) | **Reproduce the shipped artifact first.** All comparisons are against A0, not the shipped model, so retraining differences don't masquerade as effects. |
| A1 | `insurance_type` | Isolate the insurance pathway |
| A2 | `region` | Isolate the region pathway |
| A3 | `region`, `insurance_type` | Full proxy removal |

- **Same hyperparameters as the bundle:** `GradientBoostingClassifier(n_estimators=180, learning_rate=0.08, random_state=20260425)`, and the same `ColumnTransformer` minus the dropped columns.
- **Two operating points:**
  - (a) Fixed threshold **0.26**, the deployed setting.
  - (b) A threshold re-tuned so overall recall matches A0's (0.744). Tune it on a **validation split carved from `train.csv`**, never on test, to avoid leakage. Dropping features shifts calibration, so (a) alone can confuse "less biased" with "flags more people".
- **Uncertainty:** 1,000 paired bootstrap resamples of the test set, giving a 95% CI on ΔFNR for the most-harmed cell. Also run 5 retrain seeds to show model variance is negligible next to sampling variance.
- **Metrics per variant:**
  - Rural × Medicaid FNR, with its Wilson CI.
  - KRI-1 gap.
  - Overall AUC and recall.
  - Selection rate and FPR in Rural × Medicaid. Removing the proxy should raise flags there; report the extra false positives honestly.

### Decision rule (pre-registered)

Write this into the notebook **before** running the variants.

| Outcome on A3 at matched recall | Verdict | Portfolio consequence |
|---|---|---|
| Rural × Medicaid FNR falls ≥ 15 pp **and** the bootstrap CI of the fall excludes 0 | **Confirmed** | The D4 verdict stands. D8 C1 retraining without the features is validated. |
| Falls 5–15 pp, or the CI touches 0 | **Partial** | The proxy pathway exists but is not the whole story. Weight label remediation (D8 C1 label audit) more heavily than feature removal. |
| Falls < 5 pp | **Weakened** | The gap comes mainly from label bias the model reconstructs from clinical features. Revise D4, D5 RR-01, D6 §5b and D8 C1 so feature removal is no longer the main fix. |

**Interpretation caveat to state explicitly:** the test labels carry the same under-diagnosis as the training labels. Rural × Medicaid test prevalence is 11.6%, against 25–28% elsewhere. So every variant's FNR is measured against biased ground truth, and an ablation can show the gap narrowing but cannot prove it has closed.

### Implementation

- **New module `lab/counterfactual.py`:**

  ```python
  from sklearn.base import clone

  def retrain_without(pipeline, X_train, y_train, drop):
      """Refit an unfitted clone of `pipeline` with `drop` columns removed everywhere."""
      model = clone(pipeline)
      transformers = [
          (name, tr, [c for c in cols if c not in drop])
          for name, tr, cols in model.named_steps["preprocessor"].transformers
      ]
      model.set_params(preprocessor__transformers=transformers)
      return model.fit(X_train.drop(columns=list(drop)), y_train)
  ```

  Add `threshold_for_recall(model, X_val, y_val, target_recall)` and `bootstrap_fnr_delta(...)` beside it.
- **Tests in `lab/tests_extra/test_counterfactual.py`:**
  - Dropped columns are absent from `get_feature_names_out()`.
  - Hyperparameters equal the original's.
  - The A0 refit reproduces the shipped AUC within ±0.005.
  - The threshold search hits its target recall on a toy set.
- **Notebook §6c "Counterfactual ablation"**, inserted after §6b: run the variants, print the comparison table, and print the verdict from the decision rule.
- **Workbook:**
  - **D4:** a new block from row 62 ("Counterfactual ablation"), one row per variant, written by the notebook.
  - **Updates to existing text:** append the result to the D4 narrative's "what would confirm or refute it" paragraph. Update D5 RR-01's note and residual risk, D6 §5b point (2), and the evidence line of D8 condition C1.

### Acceptance criteria

- [ ] A0 reproduces the shipped model, with AUC within ±0.005; otherwise stop and investigate before comparing variants.
- [ ] The table shows A0–A3 at both operating points, with bootstrap CIs.
- [ ] The verdict is printed by code from the pre-registered rule, not judged by hand.
- [ ] Every portfolio cell that cites the proxy finding is consistent with the verdict.

---

## U2: Fourth threat on the human override path, traced to a monitoring indicator

### Scoping: why this is not a repeat of D3 #1

D3 rank 1 (`AML.T0020`) attacks the **future model**: overrides poison the retraining data. The fourth threat attacks the **current clinical decision**: an override suppresses a true high-risk flag *today*, so the referral never happens, whether or not the model is ever retrained. The two share a channel but have different harms, timing and controls.

| | D3 #1 (existing) | U2 (new) |
|---|---|---|
| Target | Training data (Component 5 — Model Registry) | Live clinical decision (Component 4 — Clinician-Facing Dashboard) |
| When harm lands | Next model release | Immediately, per patient |
| Primary ATLAS technique | `AML.T0020` Poison Training Data | `AML.T0012` Valid Accounts → impact `AML.T0048` External Harms (user-harm sub-technique) |

**Verify both IDs and names on atlas.mitre.org before writing them into the workbook.** ATLAS renamed many "ML" techniques to "AI" in 2025, and the sub-technique numbering for External Harms must be checked.

### Threat specification (D3 row 12)

- **Actor:** an attacker with a phished clinician credential, or an insider. There is also a **non-adversarial twin** with the same signature: clinicians who systematically dismiss flags for under-served patients. The control and the indicator must catch both.
- **Scenario:**
  1. The attacker uses a valid account on the dashboard.
  2. They override high-score flags (p ≥ 0.60) to "not high-risk" for a targeted cohort, e.g. one insurer's members or one site.
  3. The overrides are logged, but nothing routes them for review.
  4. Referrals silently drop for that cohort.
  5. Overall KRI-2 can stay Green, because a few hundred targeted overrides barely move a site-wide override rate.
- **Likelihood / Impact:** M / H. Clinician credentials are the most-phished in healthcare, and every suppressed referral is a potential delayed diagnosis.

### Mitigation (named mechanisms)

1. **Dual control on high-score overrides.** Overriding a flag with p ≥ 0.60 requires a structured reason code plus confirmation by a second clinician within 24 h. Until it's confirmed, the referral stays in the worklist.
2. **Structured override reasons.** A controlled vocabulary, mandatory for every override, which also feeds KRI-2's structured-share criterion.
3. **Step-up authentication** (MFA re-prompt) when one session overrides more than 5 flags in 60 minutes.
4. **Per-clinician override anomaly detection.** A z-score of each clinician's high-score override rate against peers at the same site.

### The trace (must be explicit in the workbook)

```
D3 row 12 threat ─► D5 RR-13 (risk) ─► controls 1–4 ─► D7 KRI-4 (indicator)
                                                        └─► U3 incident trigger on Red
```

### New indicator: KRI-4 High-Score Override Rate

| Field | Definition |
|---|---|
| Metric | Share of predictions with p ≥ 0.60 that a clinician overrode to "not high-risk" |
| Calculation | From the C4 override events joined to the C6 inference log; a rolling 30-day window; computed **per clinician** (min 20 high-score cases) **and per region × insurance subgroup**. The status is the **worst** qualifying unit, so a targeted cohort cannot hide in the average. |
| Thresholds (provisional) | Green ≤ 10% · Amber > 10% and ≤ 20% · Red > 20%. Baseline them in the shadow-mode pilot (D8 C4), as with KRI-2. |
| Owner | Clinical Safety Officer; SOC on any per-clinician Red |
| Connected risks | RR-13 (primary); RR-04, RR-05 |

Note the difference from KRI-2: KRI-2 asks whether the override channel *as a whole* is healthy, while KRI-4 asks whether *anyone* is suppressing the flags that matter most.

### Implementation

- **`lab/kri.py`:** add `kri_high_score_override(events: pd.DataFrame, p_threshold=0.60, min_cases=20) -> dict`, returning the same shape as the existing KRIs (`kri_id`, `status`, `rate`, `worst_unit`, `note`).
- **`lab/tests_extra/test_kri4.py`** should cover:
  - the band edges (10% and 20% inclusive);
  - the rule that a unit below `min_cases` cannot drive the status;
  - the case where one targeted clinician turns the status Red even though the pooled rate is Green.
- **Notebook §7:** generate a **clearly labelled synthetic** override log to demonstrate KRI-4, as KRI-2 and KRI-3 already do, including one injected rogue clinician, and show KRI-4 going Red.
- **Workbook (free rows only):**
  - **D3:** row 12 holds the threat row. Update Section C (`A14`) with why it ranks 4th.
  - **D5:** RR-13 needs a row, but rows 7–18 are full and the scoring guide starts at row 19. Move the scoring guide (rows 19–23) down one row by rewriting the cells, not `insert_rows`, which breaks merged ranges and conditional formatting. Then put RR-13 in row 19, and extend the Top-N highlight to `A7:L19`.
  - **D7:** the KRI-4 status goes in row 14, which is free, below the notebook's rows 11–13. Rows 6–8 are the three rubric KRIs, so the KRI-4 definition and rationale go in an "Extension KRI" block after `A18`.
  - **D6 §6:** add the fourth threat. **D8 condition C4:** add dual control on high-score overrides.

### Acceptance criteria

- [ ] The D3 row has a valid `AML.T####` ID, component, scenario, mechanism-level mitigation, and Likelihood/Impact.
- [ ] The RR-13 to KRI-4 to incident-trigger chain is readable from the workbook alone.
- [ ] The KRI-4 tests prove a single targeted clinician cannot hide in the pooled rate.
- [ ] The three rubric KRIs (rows 6–8, 11–13) are untouched.

---

## U3: Serious-incident reporting workflow (D8 appendix)

### Legal routing (the part most often wrong)

D1 classifies HealthGuard as high-risk **because it is medical-device software** (Art. 6(1) + Annex I). That changes where incidents are reported:

- **AI Act Art. 73(10):** for AI systems that are devices under MDR 2017/745, AI Act serious-incident notification is **limited to Art. 3(49)(c) incidents**, i.e. infringements of Union-law obligations that protect fundamental rights. Those go to the national competent authority.
- **Everything else that harms health goes through MDR vigilance (MDR Art. 87), not AI Act Art. 73(2)–(4).** For example, a missed diagnosis attributable to the model.

**Confirm every clock below with regulatory counsel before adoption.** They are drafting assumptions, not legal advice.

| Regime | Trigger | Clock (from awareness) | Notify |
|---|---|---|---|
| MDR Art. 87(1), (3) | Serious incident: death, serious deterioration in health, or serious public-health threat, linked to the device | ≤ 15 days | Competent authority of the Member State where it occurred |
| MDR Art. 87(4) | Serious public-health threat | ≤ 2 days | Same |
| MDR Art. 87(5) | Death or unanticipated serious deterioration | ≤ 10 days | Same |
| AI Act Art. 73(10) + 3(49)(c) | Fundamental-rights infringement, e.g. a confirmed discriminatory pattern | ≤ 15 days (Art. 73(2)) | National competent authority |
| GDPR Art. 33(2) (Klariova as processor) | Personal-data breach | Without undue delay; contract SLA ≤ 24 h | Each affected hospital (controller), which owns the Art. 33(1) 72-h notice to its supervisory authority |
| GDPR Art. 33(1) (Klariova as controller, e.g. model development) | Personal-data breach | ≤ 72 h | Lead supervisory authority, likely the Irish DPC (HQ Dublin; Art. 56) |
| HIPAA 45 CFR §164.410 (Klariova as business associate) | Breach of unsecured PHI | Without unreasonable delay, ≤ 60 days; the BAA SLA is usually shorter | The covered-entity hospital, which notifies individuals and HHS under §164.404–408 |
| FDA (if HealthGuard is a device in the US) | Device-related death or serious injury | 21 CFR Part 803 (30 days; 5 work days for events needing remedial action) | FDA. **First settle whether the CDS exemption (FD&C Act §520(o)(1)(E)) applies.** |

### Workflow

1. **Triggers (open an incident):**
   - KRI-1 or KRI-4 Red;
   - a clinician or patient complaint alleging a missed or delayed diagnosis;
   - a deployer report under AI Act Art. 26(5);
   - KRI-3 Red with suspected exfiltration;
   - an artifact signature mismatch at load;
   - any confirmed personal-data breach.
2. **Triage (≤ 24 h):** the Clinical Safety Officer acts as incident commander and classifies the incident as **health harm / fundamental rights / data breach / security**. One incident can fall in several classes. Record the **awareness timestamp**, because every regulatory clock starts there.
3. **Contain:** use the per-tenant kill-switch to fall back to standard screening (D8 C4). Preserve logs, the model version and the artifact hash for evidence.
4. **Assess causality:** a clinical and ML review to decide whether the incident is device-related.
5. **Notify:** follow the routing table. Send an initial report even if incomplete (permitted under Art. 73(5)), then follow up.
6. **Internal escalation:**
   - **CAIRO, CMO, DPO and CISO:** always.
   - **General Counsel:** any external notification.
   - **CEO and Board:** any regulator notification, or any death or serious deterioration.
7. **Corrective action:** a field safety corrective action (FSCA, MDR Art. 87(1)(b)) where needed; root cause analysis; CAPA.
8. **Close the loop:** add or re-score risks in D5, update D6 (a refresh trigger), review KRI thresholds in D7, and record lessons learned.

### Deliverable

- **D8 "Appendix: Serious-incident reporting workflow"** in free rows below the RACI (row 41 onward), using the existing four-column layout. It holds the routing table, the eight steps, and a RACI for incident roles. Reference it from D8 B.4 and from each Red escalation in D7.
- **Optional:** a swim-lane diagram (Clinician / Hospital / Klariova CSO / DPO / Regulator) exported to `results/incident_workflow.png`.

### Acceptance criteria

- [ ] Every trigger maps to at least one routing row. Every routing row has an owner and a clock.
- [ ] The MDR vs AI Act split (Art. 73(10)) is explicit.
- [ ] The awareness timestamp is defined, because it starts every clock.
- [ ] Counsel review is recorded as an open item until done.

---

## U4: Transfer Impact Assessment template (attached to the RoPA)

### Scope reminder from D2 Section B

- **US→EU inbound telemetry:** not a GDPR Chapter V transfer, so no TIA is legally required. GDPR still applies in Frankfurt under Art. 3(1).
- **EU→US return legs:** drift alerts, dashboards viewed from Boston, and remote access by US staff. These **are** transfers. The mechanism is DPF adequacy, with SCCs Module 4 as the fallback. A TIA is required whenever SCCs are relied on.

The template should therefore record **every leg**, including the ones that conclude "not a transfer". That conclusion is itself an accountability record under Art. 5(2).

### Template structure (follows the six steps in EDPB Recommendations 01/2020)

| Section | Fields | HealthGuard pre-fill |
|---|---|---|
| 0. Header | TIA ID, version, RoPA entry ID, owner (DPO), approver, review date | `TIA-HG-01`, linked to RoPA "Model-drift monitoring of US inference telemetry" |
| 1. Know the transfer | Leg ID; exporter / importer (legal entities and roles); data categories; special-category flag; data subjects; volume and frequency; format (row-level / aggregate / pseudonymised); onward transfers | Leg 1 US→EU (inbound); Leg 2 EU→US alerts; Leg 3 remote access from Boston; Leg 4 onward to US hospitals |
| 2. Transfer tool | Art. 45 adequacy (DPF certification checked, date) / Art. 46 SCCs (module, clause 14 applicability) / Art. 49 derogation | Legs 2–4: DPF, with SCCs Module 4 as fallback. Clause 14 applies under Module 4 only where EU and US data are combined. |
| 3. Third-country law and practice | Laws that could compel access (FISA §702, EO 12333), redress (EO 14086, Data Protection Review Court), whether the importer is likely in scope (e.g. electronic communications service provider status), sources consulted and dates | Pre-written US assessment; refresh on any DPF challenge |
| 4. Supplementary measures | Technical (encryption with EU-held keys, pseudonymisation, aggregation with k ≥ 20); contractual (transparency and challenge commitments); organisational (access policy, logging) | Aggregate-only telemetry; tokenised IDs with US-East-held keys |
| 5. Conclusion | Transfer may proceed / proceed with measures / suspend; residual risk; sign-off | Signed by the DPO |
| 6. Re-evaluation triggers | DPF invalidated or amended; new data category; change of importer; US legal change; annual review | Calendar entry plus D5 RR-10 review |
| Annex | Data-flow diagram for the legs; evidence log (DPF list entry, SCC execution date) | Reuse the D2 stage 8 analysis |

### Deliverable

- **`docs/tia_template.md`:** a blank template with field guidance.
- **`docs/TIA-HG-01_us_eu_telemetry.md`:** the filled-in assessment for HealthGuard.
- **Links:** reference both from D2 Section B, point 4 (`A16`), and from D5 RR-10's controls.

Keep the TIA **out** of the graded workbook (no new tab), so the eight-tab structure the rubric expects stays intact.

### Acceptance criteria

- [ ] All four legs are recorded, including the "not a transfer" conclusion for Leg 1.
- [ ] Each leg names its tool and states whether clause 14 / a TIA applies.
- [ ] Supplementary measures name mechanisms, not intentions.
- [ ] Re-evaluation triggers are concrete events.

---

## Optional enabler: portfolio consistency checker

During the rubric review, ad-hoc scripts caught three real defects:
- a stale "should be ~0.40" FNR comment in the notebook;
- an overstated "26–29% in every other cell" claim, copied into four tabs;
- formula-based D5 scores that read as blank outside Excel.

Promote those checks into **`scripts/verify_portfolio.py`** and run it after every upgrade. It should check:

- no `[bracketed]` placeholders in any input cell;
- every number cited in D6, D8 and the D4 narrative matches its source cell in D4 or the notebook output;
- every D7 risk ID exists in D5, and every D6 §6 ATLAS ID exists in D3;
- D5 scores are stored values and equal Likelihood × Impact;
- Article citations in D1 include a paragraph reference.

---

## Open questions

1. **U1:** if A0 does not reproduce the shipped AUC within ±0.005, compare against A0 or investigate the artifact first? Recommendation: investigate first. A mismatch may itself be a provenance finding for D6 §3.
2. **U2:** are the KRI-4 thresholds (10% / 20%) acceptable as provisional values until the shadow pilot, or should KRI-4 report only (no status colour) until then?
3. **U3:** who is the named incident commander out of hours? The RACI currently names the Clinical Safety Officer role only.
4. **U4:** has Klariova Health Inc. actually self-certified under the DPF? The TIA's Leg 2–4 conclusions depend on it.
