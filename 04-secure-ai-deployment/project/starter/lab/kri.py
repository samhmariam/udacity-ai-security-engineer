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


def kri_subgroup_fnr_drift(
    y_true,
    y_pred,
    sensitive_features: pd.DataFrame,
    min_n_positives: int = 20,
) -> dict:
    """
    TODO: Implement the KRI defined as KRI-1 in your D7 dashboard tab.

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
    raise NotImplementedError("Implement kri_subgroup_fnr_drift")


def kri_override_health(
    override_rate: float,
    structured_share: float,
) -> dict:
    """
    TODO: Implement the KRI defined as KRI-2 in your D7 dashboard tab.

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
    raise NotImplementedError("Implement kri_override_health")


def kri_inference_anomaly(
    anomaly_count: int,
    total_inferences: int,
) -> dict:
    """
    TODO: Implement the KRI defined as KRI-3 in your D7 dashboard tab.

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
    raise NotImplementedError("Implement kri_inference_anomaly")
