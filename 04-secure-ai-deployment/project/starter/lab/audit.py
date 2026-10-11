"""
audit.py — Subgroup, intersectional, and proxy-pathway analysis.

These functions assemble the metrics from fairness_metrics.py into the kind
of analysis a real AI Risk Officer would run.

Run the unit tests to check your work:
    cd starter/
    pytest lab/tests/test_audit.py -v
"""
from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd

# You will import your implementations from the same package
from .fairness_metrics import (
    false_negative_rate, false_positive_rate, selection_rate,
)


def compute_subgroup_metrics(
    y_true,
    y_pred,
    sensitive_features,
) -> pd.DataFrame:
    """
    TODO: Compute per-subgroup metrics and return them as a table.

    What the input looks like. The sensitive_features argument can be either
    a single column of group labels (single-axis analysis — e.g., region by
    itself) OR a multi-column structure of group labels (intersectional
    analysis — e.g., region together with insurance type). Your function
    must handle both shapes.

    For each unique value or combination of values in the sensitive
    features, compute against the rows belonging to that subgroup:
        - the total number of rows in the subgroup,
        - the count of actual positives in the subgroup,
        - the selection rate,
        - the false-negative rate,
        - the false-positive rate,
        - the within-subgroup accuracy.

    Why n_positives matters. The false-negative rate of a cell with five
    positives is far less stable than the false-negative rate of a cell
    with fifty. Always carry the positive count alongside the metric so
    downstream code can apply a statistical-power filter.

    Returns:
        A table with one row per subgroup, indexed by the subgroup label
        (single-axis) or the combination of labels (intersectional).
    """
    raise NotImplementedError("Implement compute_subgroup_metrics")


def find_most_harmed_subgroup(
    subgroup_df: pd.DataFrame,
    metric_name: str = "FNR",
    min_n_positives: int = 20,
    higher_is_worse: bool = True,
) -> Optional[dict]:
    """
    TODO: Return the subgroup row with the worst value of `metric_name`,
    AMONG subgroups that meet a minimum-positive-count threshold.

    Why this matters — the small-n trap. A cell with five positives can
    show a very high false-negative rate just by random sampling — three
    more or fewer false negatives swing it twenty percentage points. Calling
    that cell "most harmed" without statistical power is a finding you
    cannot defend in a launch-decision meeting.

    The minimum-positive-count filter is a deliberate choice. Document the
    choice in your D8 limitations, and surface it as a residual risk in D5:
    the smallest subgroup cells are not statistically powered, so disparities
    in those cells cannot be quantified.

    Args:
        subgroup_df: the table produced by compute_subgroup_metrics.
        metric_name: which column to maximize (or minimize, depending on
            higher_is_worse).
        min_n_positives: minimum positive count required for a row to be
            considered.
        higher_is_worse: True for false-negative rate and false-positive
            rate; False for accuracy or selection rate, when applicable.

    Returns:
        A dictionary describing the most-harmed subgroup — the subgroup
        label, which metric was used, the metric value, the positive count,
        and the total count. Return nothing (None) if no subgroup meets
        the minimum-positive-count threshold.
    """
    raise NotImplementedError("Implement find_most_harmed_subgroup")


def assess_proxy_pathway(
    intersectional_df: pd.DataFrame,
    primary_axis_value,
    secondary_axis_low,
    secondary_axis_high,
    metric_name: str = "FNR",
) -> dict:
    """
    TODO: Compare the within-primary-axis disparity to the across-primary-
    axis baseline, and return a verdict on whether a proxy pathway is
    consistent with the data.

    Why this matters — this IS the proxy-bias test, in code.

    The reasoning. Suppose the model has false-negative-rate disparities
    across the primary axis (say, region). Two explanations are possible:
        (a) the primary axis is the operative variable, OR
        (b) a second variable that is correlated with the primary axis
            is the operative variable — i.e., a proxy for the primary axis.

    If you slice within a single value of the primary axis and find that
    the metric varies just as much across the secondary variable, then the
    secondary variable is a candidate proxy. If the metric does not vary
    within the primary axis, the primary axis is likely doing the work
    directly.

    What to compute. Look up the metric value at two specific cells of the
    intersectional table:
        - the cell where the primary axis equals primary_axis_value AND the
          secondary axis equals secondary_axis_low,
        - the cell where the primary axis equals primary_axis_value AND the
          secondary axis equals secondary_axis_high.
    The within-axis gap is the difference between these two values.

    Then compute the same gap for a reference primary value (a value other
    than primary_axis_value — pick the one with the largest sample size so
    your reference is stable). The reference gap tells you what the
    secondary-axis effect looks like in a population where you do NOT
    expect the proxy mechanism to be operating.

    Decision rule.
        - If the within-axis gap is meaningfully larger than the reference
          gap (and both are positive), call the proxy pathway supported.
        - If the within-axis gap is comparable to the reference gap, call
          it inconsistent with the proxy hypothesis.
        - If a required cell is missing or the gap is not directional,
          call it inconclusive and explain what is missing.

    Returns:
        A dictionary with the within-axis gap (in percentage points), the
        reference gap (in percentage points), the verdict, the reference
        primary value used, and a short rationale string.
    """
    raise NotImplementedError("Implement assess_proxy_pathway")
