"""Feature correlations page: ports the old analysis correlation tab."""

from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.pages.correlations import alerts, distributions, heatmaps, scanner
from midi_exploration.pages.correlations.engine import (
    apply_cross_category_mask,
    compute_correlation_matrices,
    detect_constant_columns,
    mask_diagonal,
    select_numeric_columns,
)


def render(
    matrix: pd.DataFrame,
    active_cols: list[str],
    taxonomy: dict[str, Any],
):
    st.header("Correlations")
    st.caption('use sidebar to filter (upper left corner ">>" button)')
    st.info("This tab analyzes active normalized features and respects the current filters.")

    selected, skipped = select_numeric_columns(matrix, active_cols, taxonomy)

    if skipped:
        with st.expander(f"Skipped {len(skipped)} unsupported columns", expanded=False):
            st.info("Only active numeric _norm columns are correlated.")
            for reason in skipped:
                st.write(f"- {reason}")

    if len(selected) < 2:
        st.warning("Select at least two numeric normalized features in the sidebar to see correlations.")
        return

    st.write(f"**Analyzing:** `{len(matrix)}` loops across `{len(selected)}` normalized features.")

    st.subheader("Analysis Thresholds")
    gc1, gc2 = st.columns(2)
    with gc1:
        cross_cat_only = st.checkbox(
            "Cross-category pairs only",
            value=False,
            help="Hide correlations between features within the same category group.",
            key="corr_cross_cat_only",
        )
    with gc2:
        sort_by_cat = st.checkbox(
            "Group by category pairs",
            value=False,
            help="Group alert pairs by their category combination.",
            key="corr_sort_by_cat",
        )

    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Pearson**")
        p_map_range = st.slider("Map Focus (|r|)", 0.0, 1.0, (0.5, 1.0), 0.05, key="corr_map_p")
        p_alert_range = st.slider("Alert Range", 0.0, 1.0, (0.8, 1.0), 0.05, key="corr_alert_p")
    with c2:
        st.markdown("**Spearman**")
        s_map_range = st.slider("Map Focus (|r|)", 0.0, 1.0, (0.5, 1.0), 0.05, key="corr_map_s")
        s_alert_range = st.slider("Alert Range", 0.0, 1.0, (0.8, 1.0), 0.05, key="corr_alert_s")
    with c3:
        st.markdown("**Diff (Spearman - Pearson)**")
        d_map_range = st.slider("Map Focus", 0.0, 1.0, (0.15, 1.0), 0.05, key="corr_map_d")
        d_alert_range = st.slider("Alert Range", 0.0, 1.0, (0.5, 1.0), 0.05, key="corr_alert_d")

    map_ranges = {"pearson": p_map_range, "spearman": s_map_range, "diff": d_map_range}
    alert_ranges = {"pearson": p_alert_range, "spearman": s_alert_range, "diff": d_alert_range}

    if st.button("Run Correlation Analysis", use_container_width=True, key="corr_run_btn"):
        constant = detect_constant_columns(matrix, selected)
        usable = [c for c in selected if c not in constant]
        analysis_df = matrix[usable].copy()

        if constant:
            st.info(f"{len(constant)} constant features skipped: {', '.join(constant)}")

        pearson, spearman, diff = compute_correlation_matrices(analysis_df)

        temp_p = mask_diagonal(pearson)
        temp_s = mask_diagonal(spearman)
        temp_d = mask_diagonal(diff)

        if cross_cat_only:
            temp_p = apply_cross_category_mask(temp_p, taxonomy)
            temp_s = apply_cross_category_mask(temp_s, taxonomy)
            temp_d = apply_cross_category_mask(temp_d, taxonomy)

        st.write(f"**Audit:** Analyzed `{len(usable)}` features across `{len(analysis_df)}` loops.")

        heatmaps.render(
            pearson,
            spearman,
            diff,
            temp_p,
            temp_s,
            temp_d,
            map_ranges,
            cross_cat_only,
            taxonomy,
        )
        alerts.render(
            pearson,
            spearman,
            diff,
            temp_p,
            temp_s,
            temp_d,
            alert_ranges,
            cross_cat_only,
            taxonomy,
            sort_by_cat,
            constant,
        )
        scanner.render(pearson, spearman, diff, taxonomy)
        distributions.render(temp_p, temp_s, temp_d)
