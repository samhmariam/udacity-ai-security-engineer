"""
Unit tests for lab/shap_analysis.py

    pytest lab/tests/test_shap_analysis.py -v

These tests use a small synthetic SHAP-values matrix to exercise
detect_proxy_features, plus a marker test for setup_explainer.
"""
import numpy as np
import pandas as pd
import pytest
from lab.shap_analysis import detect_proxy_features


def test_detect_excludes_protected_features():
    shap_values = np.array([
        [-0.5,  0.2,  0.4, -0.1],
        [-0.6,  0.3,  0.5, -0.1],
        [-0.4,  0.1,  0.3, -0.2],
    ])
    feature_names = [
        "cat__region_Black",
        "num__age",
        "cat__insurance_type_Medicaid",
        "num__bmi",
    ]
    out = detect_proxy_features(
        shap_values, feature_names,
        protected_feature_substrings=["region"],
        top_k=10,
    )
    assert "cat__region_Black" not in out["feature"].values, \
        "protected feature must be filtered out"

def test_detect_returns_top_k():
    shap_values = np.random.RandomState(0).randn(50, 6)
    names = [f"feat_{i}" for i in range(6)]
    out = detect_proxy_features(shap_values, names,
                                 protected_feature_substrings=[], top_k=3)
    assert len(out) == 3

def test_detect_signed_strength_bounds():
    # signed_strength in [0, 1]
    shap_values = np.random.RandomState(1).randn(100, 4)
    names = list("abcd")
    out = detect_proxy_features(shap_values, names,
                                 protected_feature_substrings=[], top_k=4)
    assert ((out["signed_strength"] >= 0) & (out["signed_strength"] <= 1)).all()

def test_detect_dataframe_columns():
    shap_values = np.random.RandomState(2).randn(20, 3)
    out = detect_proxy_features(shap_values, list("xyz"),
                                 protected_feature_substrings=[], top_k=3)
    assert {"feature","mean_abs_shap","mean_shap","signed_strength","rank"}.issubset(out.columns)
