"""
Unit tests for lab/audit.py

    pytest lab/tests/test_audit.py -v
"""
import math
import numpy as np
import pandas as pd
import pytest

from lab.audit import (
    compute_subgroup_metrics,
    find_most_harmed_subgroup,
    assess_proxy_pathway,
)

# Tiny synthetic test set for predictable arithmetic.
def _toy():
    y_true = np.array([1,1,1,1, 1,1,0,0, 1,1,0,0])
    y_pred = np.array([1,1,0,0, 1,0,0,0, 1,1,0,1])
    sensitive_single = pd.Series(
        ["A","A","A","A", "B","B","B","B", "C","C","C","C"],
        name="group")
    sensitive_inter = pd.DataFrame({
        "region": ["X","X","X","X", "X","X","X","X", "Y","Y","Y","Y"],
        "ins":  ["P","P","M","M", "P","P","M","M", "P","P","M","M"],
    })
    return y_true, y_pred, sensitive_single, sensitive_inter

# --- compute_subgroup_metrics -----------------------------------------------

def test_subgroup_returns_dataframe_with_expected_columns():
    y_true, y_pred, s, _ = _toy()
    df = compute_subgroup_metrics(y_true, y_pred, s)
    assert isinstance(df, pd.DataFrame)
    for col in ["n_total", "n_positives", "selection_rate", "FNR", "FPR", "accuracy"]:
        assert col in df.columns, f"missing column {col}"

def test_subgroup_has_one_row_per_group():
    y_true, y_pred, s, _ = _toy()
    df = compute_subgroup_metrics(y_true, y_pred, s)
    assert len(df) == 3

def test_subgroup_intersectional_uses_multiindex():
    y_true, y_pred, _, sf = _toy()
    df = compute_subgroup_metrics(y_true, y_pred, sf)
    # MultiIndex of (region, ins)
    assert isinstance(df.index, pd.MultiIndex)
    assert set(df.index.names) == {"region", "ins"}

def test_subgroup_metrics_arithmetic_for_one_cell():
    y_true, y_pred, s, _ = _toy()
    df = compute_subgroup_metrics(y_true, y_pred, s)
    # Group A: y_true=[1,1,1,1], y_pred=[1,1,0,0]
    # FNR = 2/4 = 0.5 ; FPR = nan ; selection_rate = 0.5 ; n_positives = 4
    a = df.loc["A"]
    assert a["n_total"] == 4
    assert a["n_positives"] == 4
    assert a["FNR"] == pytest.approx(0.5)
    assert math.isnan(a["FPR"])
    assert a["selection_rate"] == pytest.approx(0.5)

# --- find_most_harmed_subgroup ----------------------------------------------

def test_find_most_harmed_returns_none_when_filter_excludes_all():
    y_true, y_pred, s, _ = _toy()
    df = compute_subgroup_metrics(y_true, y_pred, s)
    out = find_most_harmed_subgroup(df, metric_name="FNR", min_n_positives=99)
    assert out is None

def test_find_most_harmed_returns_correct_group():
    y_true, y_pred, s, _ = _toy()
    df = compute_subgroup_metrics(y_true, y_pred, s)
    # min_n_positives=2 will keep all groups
    out = find_most_harmed_subgroup(df, metric_name="FNR", min_n_positives=2)
    # Group B: y_true=[1,1,0,0], y_pred=[1,0,0,0] → FNR=1/2=0.5
    # Group A: FNR=0.5 (same)
    # Group C: y_true=[1,1,0,0], y_pred=[1,1,0,1] → FNR=0/2=0
    # Tie between A and B at 0.5 — both are valid; the contract is "highest value", whichever idxmax picks
    assert out["metric_value"] == pytest.approx(0.5)

def test_find_most_harmed_filters_low_n():
    # Construct a df where the cell with the worst FNR has tiny n_positives
    df = pd.DataFrame({
        "n_total":     [100, 100, 5],
        "n_positives": [40, 40, 3],
        "FNR":         [0.20, 0.30, 0.90],   # the 0.90 comes from the n_pos=3 cell
        "FPR":         [0.10, 0.10, 0.10],
        "accuracy":    [0.8, 0.8, 0.8],
        "selection_rate": [0.4, 0.4, 0.4],
    }, index=["X", "Y", "Z"])
    out = find_most_harmed_subgroup(df, metric_name="FNR", min_n_positives=10)
    # Should pick Y (FNR=0.30) NOT Z (FNR=0.90 but only n_pos=3)
    assert out["subgroup"] == "Y"

# --- assess_proxy_pathway ---------------------------------------------------

def test_proxy_supported_when_within_gap_exceeds_reference():
    df = pd.DataFrame({
        "n_total": [100, 100, 100, 100],
        "n_positives": [50, 50, 50, 50],
        "FNR": [0.65, 0.30, 0.40, 0.35],
    }, index=pd.MultiIndex.from_tuples(
        [("Rural","Medicaid"), ("Rural","Private"),
         ("Urban","Medicaid"), ("Urban","Private")],
        names=["region","ins"]))
    out = assess_proxy_pathway(df, "Rural", "Medicaid", "Private", metric_name="FNR")
    assert out["verdict"] == "proxy_supported"
    assert out["within_gap_pp"] > out["reference_gap_pp"]

def test_proxy_inconclusive_when_cell_missing():
    df = pd.DataFrame({
        "n_total": [100, 100],
        "n_positives": [50, 50],
        "FNR": [0.30, 0.30],
    }, index=pd.MultiIndex.from_tuples(
        [("Urban","Medicaid"), ("Urban","Private")],
        names=["region","ins"]))
    out = assess_proxy_pathway(df, "Rural", "Medicaid", "Private", metric_name="FNR")
    assert out["verdict"] == "inconclusive"
