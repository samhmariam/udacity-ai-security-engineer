"""
kri.py — Translate the three KRI definitions from D7 into runnable code.

Why this lab matters. A Key Risk Indicator defined only in prose is a wish,
not a control. A KRI defined in code is reproducible, testable, and
auditable. The difference is what makes "post-launch monitoring" credible
to a regulator.

Each function returns the same shape: a status of Green, Amber, or Red,
the metric value, and any context fields the dashboard would need.

Run the unit tests:
    cd starter/
    pytest lab/tests/test_kri.py -v
"""
from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd

from .audit import compute_subgroup_metrics

# Threshold comparisons round first so float noise (e.g. 15.000000000001 pp)
# cannot push a value across a band boundary.
_PRECISION = 9


def _cell_label(label) -> str:
    return " × ".join(map(str, label)) if isinstance(label, tuple) else str(label)


def kri_subgroup_fnr_drift(
    y_true,
    y_pred,
    sensitive_features: pd.DataFrame,
    min_n_positives: int = 20,
) -> dict:
    """
    Implement the KRI defined as KRI-1 in your D7 dashboard tab.

    Conceptual definition (from D7).
        Look across the intersectional cells of the audit population — for
        example, region paired with insurance type. Among cells that have
        enough actual positives to read reliably, find the worst false-
        negative rate and the best false-negative rate, and compute the
        gap between them in percentage points.

        Apply a Green / Amber / Red ladder to that gap:
            Green when the gap is up to eight percentage points.
            Amber when the gap is between eight and fifteen percentage
                points (inclusive of the upper bound).
            Red when the gap is greater than fifteen percentage points.

    Steps you will need.
        - Build the intersectional subgroup metrics by calling your
          existing subgroup-metrics function on the sensitive features.
        - Drop cells that fall below the minimum-positive-count threshold.
        - From the remaining cells, find the highest false-negative rate
          and the lowest false-negative rate.
        - Convert the difference into percentage points.
        - Apply the threshold ladder to determine the status.

    Edge case. If fewer than two cells survive the minimum-positive-count
    filter, the KRI is undefined for the audit window. Return a status of
    "Insufficient" with a note explaining how many cells qualified.

    Returns:
        A dictionary that names the KRI identifier, the status, the gap
        in percentage points, the cell label with the worst false-negative
        rate, the cell label with the best false-negative rate, the count
        of qualifying cells, and a short note string.
    """
    cells = compute_subgroup_metrics(y_true, y_pred, sensitive_features)
    qualifying = cells[(cells["n_positives"] >= min_n_positives) & cells["FNR"].notna()]
    result = {
        "kri_id": "KRI-1",
        "kri_name": "Subgroup FNR Drift",
        "status": "Insufficient",
        "gap_pp": None,
        "worst_cell": None,
        "worst_fnr": None,
        "best_cell": None,
        "best_fnr": None,
        "n_qualifying_cells": int(len(qualifying)),
        "n_total_cells": int(len(cells)),
        "min_n_positives": min_n_positives,
    }
    if len(qualifying) < 2:
        result["note"] = (f"Only {len(qualifying)} of {len(cells)} cells have >= "
                          f"{min_n_positives} positives; need 2 to measure a gap.")
        return result

    worst, best = qualifying["FNR"].idxmax(), qualifying["FNR"].idxmin()
    worst_fnr, best_fnr = float(qualifying.loc[worst, "FNR"]), float(qualifying.loc[best, "FNR"])
    gap_pp = round((worst_fnr - best_fnr) * 100, _PRECISION)
    if gap_pp <= 8:
        status = "Green"
    elif gap_pp <= 15:
        status = "Amber"
    else:
        status = "Red"

    result.update({
        "status": status,
        "gap_pp": round(gap_pp, 1),
        "worst_cell": _cell_label(worst),
        "worst_fnr": round(worst_fnr, 3),
        "best_cell": _cell_label(best),
        "best_fnr": round(best_fnr, 3),
        "note": (f"FNR gap {gap_pp:.1f} pp: worst {_cell_label(worst)} {worst_fnr:.1%} vs best "
                 f"{_cell_label(best)} {best_fnr:.1%} across {len(qualifying)} cells with >= "
                 f"{min_n_positives} positives (Green <= 8, Amber <= 15, Red > 15)."),
    })
    return result


def kri_override_health(
    override_rate: float,
    structured_share: float,
) -> dict:
    """
    Implement the KRI defined as KRI-2 in your D7 dashboard tab.

    Conceptual definition. This is a dual-criterion KRI. Two inputs:
        - the share of inferences where a clinician recorded an override,
          as a fraction between zero and one;
        - the share of overrides that carried a structured reason (drawn
          from a controlled vocabulary) rather than free text, also as a
          fraction between zero and one.

    Threshold ladder (both criteria evaluated together).
        Green: override rate is at most ten percent AND structured share
            is at least eighty percent.
        Amber: override rate is between ten and fifteen percent (inclusive
            of fifteen), OR structured share is between sixty and eighty
            percent (inclusive of sixty).
        Red:   override rate is greater than fifteen percent, OR structured
            share is below sixty percent.

    Why this matters. A KRI with two conditions joined by AND / OR is a
    common governance pattern. Implementing it correctly requires careful
    boolean logic — and is something you cannot defer to a spreadsheet
    conditional-formatting rule. It needs to live in code, where it can be
    unit-tested.

    Returns:
        A dictionary with the KRI identifier, the resolved status, the two
        inputs echoed back, and a short reason string explaining which
        condition triggered the status (so the dashboard can show why the
        KRI changed color).
    """
    for name, value in (("override_rate", override_rate), ("structured_share", structured_share)):
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be a fraction in [0, 1], got {value}")
    rate = round(float(override_rate), _PRECISION)
    share = round(float(structured_share), _PRECISION)

    # Red takes precedence over Amber: one breached criterion is enough.
    red = [msg for cond, msg in (
        (rate > 0.15, f"override rate {rate:.1%} > 15%"),
        (share < 0.60, f"structured share {share:.1%} < 60%"),
    ) if cond]
    amber = [msg for cond, msg in (
        (0.10 < rate <= 0.15, f"override rate {rate:.1%} in (10%, 15%]"),
        (0.60 <= share < 0.80, f"structured share {share:.1%} in [60%, 80%)"),
    ) if cond]

    if red:
        status, reason = "Red", "; ".join(red)
    elif amber:
        status, reason = "Amber", "; ".join(amber)
    else:
        status = "Green"
        reason = f"override rate {rate:.1%} <= 10% and structured share {share:.1%} >= 80%"

    return {
        "kri_id": "KRI-2",
        "kri_name": "Override Channel Health",
        "status": status,
        "override_rate": float(override_rate),
        "structured_share": float(structured_share),
        "reason": reason,
    }


def kri_inference_anomaly(
    anomaly_count: int,
    total_inferences: int,
) -> dict:
    """
    Implement the KRI defined as KRI-3 in your D7 dashboard tab.

    Conceptual definition. Convert the count of anomalous inferences into
    an anomaly rate per one thousand inferences, and apply a Green / Amber
    / Red ladder:
        Green: rate is below one anomaly per thousand inferences.
        Amber: rate is between one and five per thousand (inclusive of
            both bounds).
        Red:   rate is greater than five per thousand.

    Edge case. If the total inference count is zero, the rate is undefined
    — return a status of "Insufficient" with an explanatory note.

    Returns:
        A dictionary with the KRI identifier, the status, the anomaly rate
        per one thousand inferences, the raw counts echoed back, and a
        short note describing the rate in plain language.
    """
    if anomaly_count < 0 or total_inferences < 0:
        raise ValueError("counts must be non-negative")
    result = {
        "kri_id": "KRI-3",
        "kri_name": "Inference Anomaly Rate",
        "anomaly_count": int(anomaly_count),
        "total_inferences": int(total_inferences),
    }
    if total_inferences == 0:
        result.update(status="Insufficient", per_1000=None,
                      note="No inferences in the window; anomaly rate is undefined.")
        return result
    if anomaly_count > total_inferences:
        raise ValueError("anomaly_count cannot exceed total_inferences")

    per_1000 = round(anomaly_count / total_inferences * 1000, _PRECISION)
    if per_1000 < 1:
        status = "Green"
    elif per_1000 <= 5:
        status = "Amber"
    else:
        status = "Red"
    result.update(
        status=status,
        per_1000=per_1000,
        note=(f"{anomaly_count} anomalous of {total_inferences:,} inferences = "
              f"{per_1000:.2f} per 1,000 (Green < 1, Amber 1-5, Red > 5)."),
    )
    return result
