"""Unified range alert list for high-correlation pairs."""

from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.pages.correlations.categories import get_column_category


def _collect_alert_pairs(
    temp_matrix: pd.DataFrame,
    alert_range: tuple[float, float],
) -> set[tuple[str, str]]:
    low, high = alert_range
    all_pairs = temp_matrix.unstack().dropna()
    filtered = all_pairs[(all_pairs.abs() >= low) & (all_pairs.abs() <= high)]
    return {tuple(sorted((f1, f2))) for f1, f2 in filtered.index}


def render(
    pearson: pd.DataFrame,
    spearman: pd.DataFrame,
    diff: pd.DataFrame,
    temp_p: pd.DataFrame,
    temp_s: pd.DataFrame,
    temp_d: pd.DataFrame,
    alert_ranges: dict[str, tuple[float, float]],
    cross_cat_only: bool,
    taxonomy: dict[str, Any],
    sort_by_cat: bool,
    constant_stats: list[str],
) -> None:
    st.divider()
    st.subheader("Unified Range Alerts")

    alert_pairs = set()
    alert_pairs |= _collect_alert_pairs(temp_p, alert_ranges["pearson"])
    alert_pairs |= _collect_alert_pairs(temp_s, alert_ranges["spearman"])
    alert_pairs |= _collect_alert_pairs(temp_d, alert_ranges["diff"])

    processed: list[tuple[str, str, str, float, float, float, float]] = []
    for f1, f2 in alert_pairs:
        cat1 = get_column_category(f1, taxonomy)
        cat2 = get_column_category(f2, taxonomy)
        if cross_cat_only and cat1 == cat2:
            continue

        cat_pair_name = " & ".join(sorted([cat1, cat2]))
        v_p = float(pearson.loc[f1, f2]) if pd.notna(pearson.loc[f1, f2]) else 0.0
        v_s = float(spearman.loc[f1, f2]) if pd.notna(spearman.loc[f1, f2]) else 0.0
        v_d = float(diff.loc[f1, f2]) if pd.notna(diff.loc[f1, f2]) else 0.0
        sort_val = max(abs(v_p), abs(v_s))
        processed.append((cat_pair_name, f1, f2, v_p, v_s, v_d, sort_val))

    if not processed:
        st.success("No pairs triggered an alert across any of the defined ranges.")
        return

    if sort_by_cat:
        valid_features = [f for f in pearson.columns if f not in constant_stats]
        cat_counts: dict[str, int] = {}
        for f in valid_features:
            cat = get_column_category(f, taxonomy)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        grouped: dict[str, list[tuple]] = {}
        for item in processed:
            grouped.setdefault(item[0], []).append(item)

        group_stats = [(k, sum(x[6] for x in v) / len(v), v) for k, v in grouped.items()]
        group_stats.sort(key=lambda x: x[1], reverse=True)

        global_counter = 1
        for cat_pair, _, items in group_stats:
            cat1, cat2 = cat_pair.split(" & ")
            expected_pairs = cat_counts.get(cat1, 0) * cat_counts.get(cat2, 0)
            is_pure = len(items) == expected_pairs and expected_pairs > 0
            clean_title = cat_pair.replace("_", " ").upper()
            if is_pure:
                accordion_title = f"All Stats: {clean_title} ({len(items)}/{expected_pairs} pairs matched)"
            else:
                accordion_title = f"{clean_title} ({len(items)}/{expected_pairs} pairs)"

            with st.expander(accordion_title):
                items.sort(key=lambda x: x[6], reverse=True)
                for _, f1, f2, v_p, v_s, v_d, _ in items:
                    st.warning(
                        f"**{global_counter}.** **{f1}** & **{f2}** "
                        f"Pearson: `{v_p:+.3f}` | "
                        f"Spearman: `{v_s:+.3f}` | "
                        f"Diff: `{v_d:.3f}`"
                    )
                    global_counter += 1
    else:
        processed.sort(key=lambda x: x[6], reverse=True)
        for i, (_, f1, f2, v_p, v_s, v_d, _) in enumerate(processed, start=1):
            st.warning(
                f"**{i}.** **{f1}** & **{f2}** Pearson: `{v_p:+.3f}` | Spearman: `{v_s:+.3f}` | Diff: `{v_d:.3f}`"
            )
