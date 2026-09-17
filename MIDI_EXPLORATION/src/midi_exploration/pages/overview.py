from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.components.charts import render_histogram
from midi_exploration.components.filters import maybe_show_cluster_filter

_FOCUS_TRACKING_KEY = "overview_focused_concept"


def _format_column_name(col: str) -> str:
    return col.rsplit("_", 1)[0].replace("_", " ").title()


def _count_stats(row: pd.Series, stat_cols: list[str]) -> int:
    return row[stat_cols].notna().sum()


def _numeric_columns(matrix: pd.DataFrame, active_cols: list[str]) -> list[str]:
    return [col for col in matrix.columns if col in active_cols and pd.api.types.is_numeric_dtype(matrix[col])]


def _resolve_focus_column(
    matrix: pd.DataFrame,
    active_cols: list[str],
    focused_concept: str | None,
) -> str | None:
    """Pick the best numeric column for the focused concept from active columns."""
    if not focused_concept:
        return None
    for suffix in ("_raw", "_norm", "_tag"):
        candidate = f"{focused_concept}{suffix}"
        if candidate in active_cols and candidate in matrix.columns:
            if pd.api.types.is_numeric_dtype(matrix[candidate]):
                return candidate
    return None


def _visible_columns(active_cols: list[str]) -> list[str]:
    if st.session_state.get("show_tag_norm", False):
        return active_cols
    return [c for c in active_cols if c.endswith("_raw")]


def _visible_matrix(matrix: pd.DataFrame, visible_cols: list[str]) -> pd.DataFrame:
    base = [c for c in matrix.columns if not c.endswith(("_raw", "_tag", "_norm"))]
    show = base + [c for c in visible_cols if c in matrix.columns]
    return matrix[[c for c in show if c in matrix.columns]]


def render(
    matrix: pd.DataFrame,
    tags_df: pd.DataFrame,
    taxonomy: dict[str, Any] | None,
    active_cols: list[str],
):
    st.header("Overview")
    st.caption('use sidebar to filter (upper left corner ">>" button)')

    if matrix.empty:
        st.warning("No files in the database.")
        return

    matrix = maybe_show_cluster_filter(matrix).copy()
    if matrix.empty:
        st.warning("No files match the selected filter.")
        return

    visible_cols = _visible_columns(active_cols)

    stat_cols = [c for c in matrix.columns if c.endswith(("_raw", "_tag", "_norm"))]
    matrix["stat_count"] = matrix.apply(lambda row: _count_stats(row, stat_cols), axis=1)

    total_files = len(matrix)
    filtered_tags = tags_df[tags_df["file_id"].isin(matrix["file_id"])] if not tags_df.empty else tags_df

    focused_concept = st.session_state.get(_FOCUS_TRACKING_KEY)
    numeric_cols = _numeric_columns(matrix, visible_cols)
    focus_column = _resolve_focus_column(matrix, visible_cols, focused_concept)

    c1, c2 = st.columns(2)
    with c1:
        histogram_options = ["Focus"] + numeric_cols + ["None"]
        selected_hist = st.selectbox(
            "Histogram",
            options=histogram_options,
            key="overview_histogram",
        )
    with c2:
        st.metric("Files shown", total_files)

    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Total files", total_files)
    with summary_cols[1]:
        st.metric("Tag assignments", len(filtered_tags))
    with summary_cols[2]:
        st.metric("Concepts", len(taxonomy or {}))
    with summary_cols[3]:
        st.metric("Active features", len(active_cols))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Files by family")
        st.bar_chart(matrix["family"].value_counts())
    with col2:
        st.subheader("Tags by concept")
        if not filtered_tags.empty:
            st.bar_chart(filtered_tags["concept_name"].value_counts())
        else:
            st.write("No tags stored.")

    if selected_hist == "Focus":
        selected_hist = focus_column or (numeric_cols[0] if numeric_cols else None)

    if selected_hist and selected_hist != "None":
        st.subheader(f"Distribution of {_format_column_name(selected_hist)}")
        render_histogram(matrix, selected_hist)

    st.subheader("Matching files")
    st.dataframe(_visible_matrix(matrix, visible_cols), width="stretch")
