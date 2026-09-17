"""Cross-category threshold scanner for high-correlation groups."""

from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.pages.correlations.categories import get_column_category

_THRESHOLD_LOW = 0.30
_THRESHOLD_MODERATE = 0.70


def _status_label(max_overall: float) -> str:
    if max_overall <= _THRESHOLD_LOW:
        return "Low correlation"
    if max_overall <= _THRESHOLD_MODERATE:
        return "Moderate correlation"
    return "High correlation"


def _status_prefix(max_overall: float) -> str:
    if max_overall <= _THRESHOLD_LOW:
        return "[LOW]"
    if max_overall <= _THRESHOLD_MODERATE:
        return "[MODERATE]"
    return "[HIGH]"


def render(
    pearson: pd.DataFrame,
    spearman: pd.DataFrame,
    diff: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Category Pair Thresholds")
    st.write(
        "Maximum cross-category correlation for each pair of groups. "
        "Groups with a maximum below 0.30 are largely independent."
    )

    valid_features = [c for c in pearson.columns]
    cat_to_features: dict[str, list[str]] = {}
    for f in valid_features:
        cat = get_column_category(f, taxonomy)
        cat_to_features.setdefault(cat, []).append(f)

    categories = list(cat_to_features.keys())
    summaries: list[dict[str, Any]] = []

    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            cat1, cat2 = categories[i], categories[j]
            f1_list = cat_to_features[cat1]
            f2_list = cat_to_features[cat2]

            sub_p = pearson.loc[f1_list, f2_list]
            sub_s = spearman.loc[f1_list, f2_list]
            sub_d = diff.loc[f1_list, f2_list]

            max_overall = max(sub_p.abs().max().max(), sub_s.abs().max().max())
            if pd.isna(max_overall):
                continue

            pairs_data = []
            for f1 in f1_list:
                for f2 in f2_list:
                    v_p = sub_p.loc[f1, f2]
                    v_s = sub_s.loc[f1, f2]
                    v_d = sub_d.loc[f1, f2]
                    if pd.notna(v_p) and pd.notna(v_s):
                        pairs_data.append((f1, f2, v_p, v_s, v_d, max(abs(v_p), abs(v_s))))

            pairs_data.sort(key=lambda x: x[5], reverse=True)
            summaries.append(
                {
                    "name": f"{cat1.replace('_', ' ')} & {cat2.replace('_', ' ')}".upper(),
                    "max_overall": max_overall,
                    "pairs": pairs_data,
                }
            )

    summaries.sort(key=lambda x: x["max_overall"])

    if not summaries:
        st.info("Check stats from at least two different categories to run the scanner.")
        return

    for summary in summaries:
        max_val = summary["max_overall"]
        prefix = _status_prefix(max_val)
        status = _status_label(max_val)
        with st.expander(f"{prefix} {status} | {summary['name']} (max < {max_val:.2f})"):
            st.caption(f"Showing {len(summary['pairs'])} total cross-pairs, sorted by strongest correlation.")
            for idx, (f1, f2, v_p, v_s, v_d, _) in enumerate(summary["pairs"], start=1):
                st.write(
                    f"**{idx}.** `{f1}` & `{f2}` Pearson: `{v_p:+.3f}` | Spearman: `{v_s:+.3f}` | Diff: `{v_d:.3f}`"
                )

    st.caption("Thresholds: [LOW] <= 0.30, [MODERATE] <= 0.70, [HIGH] > 0.70")
