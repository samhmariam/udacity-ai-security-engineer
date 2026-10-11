"""
Unit tests for lab/kri.py

    pytest lab/tests/test_kri.py -v
"""
import numpy as np
import pandas as pd
import pytest
from lab.kri import (
    kri_subgroup_fnr_drift,
    kri_override_health,
    kri_inference_anomaly,
)

# --- kri_override_health -----------------------------------------------------

def test_override_green():
    out = kri_override_health(override_rate=0.05, structured_share=0.90)
    assert out["status"] == "Green"

def test_override_amber_via_rate_band():
    out = kri_override_health(override_rate=0.12, structured_share=0.85)
    assert out["status"] == "Amber"

def test_override_amber_via_structured_share_band():
    out = kri_override_health(override_rate=0.05, structured_share=0.75)
    assert out["status"] == "Amber"

def test_override_red_via_rate_breach():
    out = kri_override_health(override_rate=0.20, structured_share=0.85)
    assert out["status"] == "Red"

def test_override_red_via_structured_share_breach():
    out = kri_override_health(override_rate=0.05, structured_share=0.40)
    assert out["status"] == "Red"

# --- kri_inference_anomaly ---------------------------------------------------

def test_anomaly_green_below_one_per_thousand():
    # 0 anomalies in 5000 inferences → 0/1000 → Green
    out = kri_inference_anomaly(anomaly_count=0, total_inferences=5000)
    assert out["status"] == "Green"

def test_anomaly_amber_in_band():
    # 5 anomalies in 5000 → 1/1000 → Amber boundary (inclusive)
    out = kri_inference_anomaly(anomaly_count=5, total_inferences=5000)
    assert out["status"] == "Amber"

def test_anomaly_red_above_threshold():
    # 30 anomalies in 5000 → 6/1000 → Red
    out = kri_inference_anomaly(anomaly_count=30, total_inferences=5000)
    assert out["status"] == "Red"

def test_anomaly_zero_inferences_is_insufficient():
    out = kri_inference_anomaly(anomaly_count=0, total_inferences=0)
    assert out["status"] == "Insufficient"

# --- kri_subgroup_fnr_drift --------------------------------------------------

def test_fnr_drift_green_when_gap_small():
    # Construct a synthetic test where every subgroup has near-equal FNR
    rng = np.random.default_rng(42)
    n = 600
    sensitive = pd.DataFrame({
        "region": rng.choice(["A","B","C"], size=n),
        "ins":  rng.choice(["P","M"], size=n),
    })
    y_true = rng.binomial(1, 0.5, size=n)
    # Predictions exactly match → FNR=0 everywhere → gap=0 → Green
    out = kri_subgroup_fnr_drift(y_true, y_true, sensitive, min_n_positives=10)
    assert out["status"] in {"Green", "Insufficient"}

def test_fnr_drift_red_when_gap_large():
    # Build data where one cell has FNR=1.0 and another has FNR=0.0
    n_per_cell = 50
    regions = ["A"]*n_per_cell + ["A"]*n_per_cell + ["B"]*n_per_cell + ["B"]*n_per_cell
    inss  = ["P"]*n_per_cell + ["M"]*n_per_cell + ["P"]*n_per_cell + ["M"]*n_per_cell
    sensitive = pd.DataFrame({"region": regions, "ins": inss})
    # All positives in y_true; predict 1 in (A,P) and (B,P), predict 0 elsewhere
    y_true = np.ones(len(regions), dtype=int)
    y_pred = np.array([1]*n_per_cell + [0]*n_per_cell + [1]*n_per_cell + [0]*n_per_cell)
    out = kri_subgroup_fnr_drift(y_true, y_pred, sensitive, min_n_positives=10)
    assert out["status"] == "Red"
    assert out["gap_pp"] >= 99
