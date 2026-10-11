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
    Compute per-subgroup metrics and return them as a table.

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
    y_true = np.asarray(y_true).astype(int).ravel()
    y_pred = np.asarray(y_pred).astype(int).ravel()

    if isinstance(sensitive_features, pd.DataFrame):
        groups = sensitive_features.reset_index(drop=True)
    else:
        s = pd.Series(np.asarray(sensitive_features).ravel(),
                      name=getattr(sensitive_features, "name", None))
        groups = s.to_frame(name=s.name if s.name is not None else "subgroup")
    if len(groups) != len(y_true) or len(y_pred) != len(y_true):
        raise ValueError("y_true, y_pred and sensitive_features must have the same length")

    group_cols = list(groups.columns)
    # A single column groups by scalar labels; several columns by tuples.
    by = group_cols[0] if len(group_cols) == 1 else group_cols

    labels, rows = [], []
    for label, idx in groups.groupby(by, sort=True, dropna=False).indices.items():
        t, p = y_true[idx], y_pred[idx]
        labels.append(label)
        rows.append({
            "n_total": int(len(idx)),
            "n_positives": int((t == 1).sum()),
            "selection_rate": selection_rate(p),
            "FNR": false_negative_rate(t, p),
            "FPR": false_positive_rate(t, p),
            "accuracy": float((t == p).mean()),
        })

    if len(group_cols) == 1:
        index = pd.Index(labels, name=group_cols[0])
    else:
        index = pd.MultiIndex.from_tuples(labels, names=group_cols)
    return pd.DataFrame(rows, index=index).sort_index()


def find_most_harmed_subgroup(
    subgroup_df: pd.DataFrame,
    metric_name: str = "FNR",
    min_n_positives: int = 20,
    higher_is_worse: bool = True,
) -> Optional[dict]:
    """
    Return the subgroup row with the worst value of `metric_name`,
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
    if metric_name not in subgroup_df.columns:
        raise KeyError(f"metric {metric_name!r} not in subgroup table")

    eligible = subgroup_df[
        (subgroup_df["n_positives"] >= min_n_positives)
        & subgroup_df[metric_name].notna()
    ]
    if eligible.empty:
        return None

    metric = eligible[metric_name]
    label = metric.idxmax() if higher_is_worse else metric.idxmin()
    row = eligible.loc[label]
    return {
        "subgroup": label,
        "metric": metric_name,
        "metric_value": float(row[metric_name]),
        "n_positives": int(row["n_positives"]),
        "n_total": int(row["n_total"]),
        "min_n_positives": min_n_positives,
        "n_eligible_subgroups": int(len(eligible)),
        "n_excluded_subgroups": int(len(subgroup_df) - len(eligible)),
    }


def assess_proxy_pathway(
    intersectional_df: pd.DataFrame,
    primary_axis_value,
    secondary_axis_low,
    secondary_axis_high,
    metric_name: str = "FNR",
    min_margin_pp: float = 5.0,
    min_n_positives: int = 20,
) -> dict:
    """
    Compare the within-primary-axis disparity to the across-primary-
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

    Implementation notes. The primary axis is index level 0 and the
    secondary axis is level 1. "Meaningfully larger" means the within-axis
    gap exceeds the reference gap by at least `min_margin_pp` percentage
    points. Verdicts are "proxy_supported", "inconsistent_with_proxy", or
    "inconclusive". The rationale flags any comparison cell below
    `min_n_positives` positives, because its rate is unstable.
    """
    result = {
        "metric": metric_name,
        "primary_axis_value": primary_axis_value,
        "secondary_axis_low": secondary_axis_low,
        "secondary_axis_high": secondary_axis_high,
        "within_gap_pp": float("nan"),
        "reference_gap_pp": float("nan"),
        "reference_primary_value": None,
        "verdict": "inconclusive",
        "rationale": "",
    }

    if not isinstance(intersectional_df.index, pd.MultiIndex) or intersectional_df.index.nlevels < 2:
        result["rationale"] = ("Needs an intersectional table indexed by "
                               "(primary axis, secondary axis).")
        return result

    def cell(primary):
        """Metric value and positive count for (primary, low) and (primary, high)."""
        out = []
        for secondary in (secondary_axis_low, secondary_axis_high):
            key = (primary, secondary)
            if key not in intersectional_df.index:
                return None
            row = intersectional_df.loc[key]
            value = float(row[metric_name])
            if np.isnan(value):
                return None
            out.append((value, int(row.get("n_positives", 0)), int(row.get("n_total", 0))))
        return out

    target = cell(primary_axis_value)
    if target is None:
        result["rationale"] = (
            f"Missing or undefined {metric_name} for {primary_axis_value} x "
            f"{secondary_axis_low} or {primary_axis_value} x {secondary_axis_high}.")
        return result
    (low_v, low_npos, _), (high_v, high_npos, _) = target
    within_gap = (low_v - high_v) * 100
    result["within_gap_pp"] = within_gap
    result["n_positives_low_cell"] = low_npos
    result["n_positives_high_cell"] = high_npos

    # Reference: the other primary value with the largest sample whose two
    # comparison cells both exist, so the baseline gap is as stable as possible.
    candidates = []
    for primary in intersectional_df.index.get_level_values(0).unique():
        if primary == primary_axis_value:
            continue
        ref = cell(primary)
        if ref is not None:
            candidates.append((ref[0][2] + ref[1][2], primary, ref))
    if not candidates:
        result["rationale"] = (f"No other {intersectional_df.index.names[0]} value has both "
                               f"comparison cells; no reference baseline.")
        return result
    _, ref_primary, ((ref_low, _, _), (ref_high, _, _)) = max(candidates, key=lambda c: c[0])
    reference_gap = (ref_low - ref_high) * 100
    result["reference_gap_pp"] = reference_gap
    result["reference_primary_value"] = ref_primary

    small_n = min(low_npos, high_npos) < min_n_positives
    power_note = (f" Caution: a comparison cell has fewer than {min_n_positives} positives."
                  if small_n else "")
    excess = within_gap - reference_gap

    if within_gap <= 0:
        result["rationale"] = (
            f"Within-{primary_axis_value} gap is {within_gap:+.1f} pp: "
            f"{secondary_axis_low} is not worse than {secondary_axis_high}, "
            f"so there is no directional effect to attribute.{power_note}")
    elif excess >= min_margin_pp:
        result["verdict"] = "proxy_supported"
        result["rationale"] = (
            f"Within {primary_axis_value}, {secondary_axis_low} vs {secondary_axis_high} "
            f"{metric_name} gap is {within_gap:+.1f} pp against {reference_gap:+.1f} pp in "
            f"{ref_primary} ({excess:+.1f} pp excess, margin {min_margin_pp:.0f} pp): the "
            f"secondary axis carries disparity inside {primary_axis_value}.{power_note}")
    else:
        result["verdict"] = "inconsistent_with_proxy"
        result["rationale"] = (
            f"Within-{primary_axis_value} gap {within_gap:+.1f} pp is comparable to the "
            f"{ref_primary} reference {reference_gap:+.1f} pp (excess {excess:+.1f} pp < "
            f"{min_margin_pp:.0f} pp margin).{power_note}")
    return result
