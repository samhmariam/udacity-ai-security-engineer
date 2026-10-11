"""
Unit tests for lab/fairness_metrics.py

Run from the starter/ directory:
    pytest lab/tests/test_fairness_metrics.py -v

These tests are designed to fail with a clear message until you have
implemented each function. The test names tell you what behavior is being
checked — read them as a checklist.
"""
import math
import numpy as np
import pytest
from lab.fairness_metrics import (
    false_negative_rate, false_positive_rate, selection_rate,
    demographic_parity_difference, equalized_odds_difference,
)

# --- false_negative_rate ----------------------------------------------------

def test_fnr_perfect_recall_is_zero():
    # All positives are predicted positive → FNR = 0
    y_true = [1, 1, 1, 0, 0]
    y_pred = [1, 1, 1, 0, 0]
    assert false_negative_rate(y_true, y_pred) == pytest.approx(0.0)

def test_fnr_no_positives_returns_nan():
    # No positives in y_true → FNR is undefined → must be nan
    y_true = [0, 0, 0, 0]
    y_pred = [0, 0, 0, 1]
    result = false_negative_rate(y_true, y_pred)
    assert math.isnan(result), "FNR must be nan when there are no positives"

def test_fnr_basic_arithmetic():
    # 4 positives, 1 detected → FNR = 3/4 = 0.75
    y_true = [1, 1, 1, 1, 0, 0]
    y_pred = [1, 0, 0, 0, 0, 0]
    assert false_negative_rate(y_true, y_pred) == pytest.approx(0.75)

# --- false_positive_rate ----------------------------------------------------

def test_fpr_no_negatives_returns_nan():
    y_true = [1, 1, 1]
    y_pred = [1, 1, 0]
    assert math.isnan(false_positive_rate(y_true, y_pred))

def test_fpr_basic_arithmetic():
    # 4 negatives, 1 false alarm → FPR = 1/4 = 0.25
    y_true = [0, 0, 0, 0, 1, 1]
    y_pred = [1, 0, 0, 0, 1, 0]
    assert false_positive_rate(y_true, y_pred) == pytest.approx(0.25)

# --- selection_rate ---------------------------------------------------------

def test_selection_rate_basic():
    assert selection_rate([1, 1, 0, 0, 0]) == pytest.approx(0.4)

# --- demographic_parity_difference ------------------------------------------

def test_dpd_finds_max_min_groups():
    y_pred = [1, 0, 1, 0, 1, 1]
    sensitive = ["A", "A", "A", "B", "B", "B"]
    # A: 2/3 ≈ 0.667; B: 2/3 ≈ 0.667 → diff = 0
    out = demographic_parity_difference(y_pred, sensitive)
    assert out["difference"] == pytest.approx(0.0)

def test_dpd_with_clear_disparity():
    y_pred = [1, 1, 1, 0, 0, 0]
    sensitive = ["A", "A", "A", "B", "B", "B"]
    out = demographic_parity_difference(y_pred, sensitive)
    assert out["difference"] == pytest.approx(1.0)
    assert out["max_group"] == "A"
    assert out["min_group"] == "B"

# --- equalized_odds_difference ----------------------------------------------

def test_eod_returns_dict_shape():
    y_true = [1, 1, 0, 0, 1, 1, 0, 0]
    y_pred = [1, 0, 0, 0, 1, 1, 1, 0]
    sensitive = ["A", "A", "A", "A", "B", "B", "B", "B"]
    out = equalized_odds_difference(y_true, y_pred, sensitive)
    assert set(["difference", "fnr_difference", "fpr_difference",
                "driver", "fnr_by_group", "fpr_by_group"]).issubset(out.keys())

def test_eod_picks_larger_of_fnr_or_fpr_diff():
    # Group A: FNR=0.5, FPR=0
    # Group B: FNR=0,   FPR=0.5
    # FNR diff = 0.5; FPR diff = 0.5 → driver could be either
    # Now skew it: Group B FPR = 1.0 → FPR diff = 1.0, larger
    y_true =   [1, 1, 0, 0,  1, 1, 0, 0]
    y_pred =   [1, 0, 0, 0,  1, 1, 1, 1]
    sensitive = ["A","A","A","A", "B","B","B","B"]
    out = equalized_odds_difference(y_true, y_pred, sensitive)
    assert out["fnr_difference"] == pytest.approx(0.5)
    assert out["fpr_difference"] == pytest.approx(1.0)
    assert out["difference"] == pytest.approx(1.0)
    assert out["driver"] == "FPR"
