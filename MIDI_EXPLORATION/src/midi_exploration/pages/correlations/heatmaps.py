"""Heatmap panel for Pearson, Spearman and Diff matrices."""

from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from midi_exploration.pages.correlations.utils import clamp


def _draw_heatmap(
    corr_matrix: pd.DataFrame,
    temp_matrix: pd.DataFrame,
    map_range: tuple[float, float],
    title: str,
    taxonomy: dict[str, Any],
    cross_cat_only: bool,
    is_diff: bool = False,
) -> None:
    low_f, high_f = map_range
    abs_max_corrs = temp_matrix.abs().max(axis=1)
    cols_to_keep = corr_matrix.columns[(abs_max_corrs >= low_f) & (abs_max_corrs <= high_f)]
    shrunk = corr_matrix.loc[cols_to_keep, cols_to_keep].copy()

    if shrunk.empty:
        st.info("No features in focus range.")
        return

    if cross_cat_only:
        shrunk = temp_matrix.loc[cols_to_keep, cols_to_keep].copy()

    display_mask = (shrunk.abs() >= low_f) & (shrunk.abs() <= high_f)
    if not cross_cat_only:
        eye = pd.DataFrame(
            np.eye(len(shrunk), dtype=bool),
            index=shrunk.index,
            columns=shrunk.columns,
        )
        display_mask = display_mask | eye

    shrunk = shrunk.where(display_mask)
    if shrunk.dropna(how="all").empty:
        st.info("No features in focus range.")
        return

    color_scale = "Reds" if is_diff else "RdBu_r"
    color_range = [0, 1] if is_diff else [-1, 1]

    text_auto = ".2f" if len(cols_to_keep) < 20 else False
    fig = px.imshow(
        shrunk,
        text_auto=text_auto,
        aspect="auto",
        color_continuous_scale=color_scale,
        range_color=color_range,
        title=f"{title}: {low_f} to {high_f}",
    )
    plot_height = clamp(len(cols_to_keep) * 40, 300, 800)
    fig.update_layout(
        height=plot_height,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_tickangle=-45,
        title_font=dict(size=16),
    )
    st.plotly_chart(fig, width="stretch")


def render(
    pearson: pd.DataFrame,
    spearman: pd.DataFrame,
    diff: pd.DataFrame,
    temp_p: pd.DataFrame,
    temp_s: pd.DataFrame,
    temp_d: pd.DataFrame,
    map_ranges: dict[str, tuple[float, float]],
    cross_cat_only: bool,
    taxonomy: dict[str, Any],
) -> None:
    st.subheader("Relationship Maps")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        _draw_heatmap(pearson, temp_p, map_ranges["pearson"], "Pearson", taxonomy, cross_cat_only)
    with hc2:
        _draw_heatmap(spearman, temp_s, map_ranges["spearman"], "Spearman", taxonomy, cross_cat_only)
    with hc3:
        _draw_heatmap(
            diff,
            temp_d,
            map_ranges["diff"],
            "Diff",
            taxonomy,
            cross_cat_only,
            is_diff=True,
        )
