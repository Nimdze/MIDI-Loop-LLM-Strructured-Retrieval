"""Sidebar controls for filter/focus and presets."""

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.components.sidebar_filters.apply import _apply_filters
from midi_exploration.components.sidebar_filters.filters_ui import (
    _render_feature_filters,
    _render_quick_filters,
)
from midi_exploration.components.sidebar_filters.helpers import (
    _all_concepts,
    _build_concept_categories,
    _build_drum_categories,
    _stat_cols,
)
from midi_exploration.components.sidebar_filters.presets import _render_presets
from midi_exploration.components.sidebar_filters.state import (
    _capture_state,
    _clear_filter_keys,
    _initialize_state,
    _sanitize_state,
)


def render_filter_sidebar(
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
    db_path: str | Path,
) -> tuple[pd.DataFrame, list[str]]:
    """Render the filter/focus sidebar and return a filtered matrix plus active columns."""
    if st.session_state.get("_last_db_path") != str(db_path):
        _clear_filter_keys()

    categories = _build_concept_categories(taxonomy)
    stat_cols = _stat_cols(matrix)

    _initialize_state(categories, matrix, taxonomy)
    _sanitize_state(matrix, stat_cols)
    st.session_state["_last_db_path"] = str(db_path)

    _render_presets(categories, matrix, taxonomy, db_path)
    _render_quick_filters(matrix, stat_cols)

    # Keep the original, unfiltered matrix for range min/max checks
    _orig_matrix = matrix

    # Filter concepts by selected family: hide drum_ concepts for pitched,
    # hide non-drum_ concepts for drums, show all for All.
    selected_family = st.session_state.get("filter_family", "pitched")
    if selected_family == "pitched":
        categories = {
            section: [c for c in concepts if not c.startswith("drum_")]
            for section, concepts in categories.items()
        }
        matrix = matrix.loc[:, ~matrix.columns.str.startswith("drum_")]
    elif selected_family == "drums":
        categories = _build_drum_categories(taxonomy)
        base_cols = [c for c in matrix.columns if not any(c.endswith(s) for s in ("_raw", "_tag", "_norm"))]
        drum_cols = [c for c in matrix.columns if c.startswith("drum_")]
        matrix = matrix.loc[:, base_cols + drum_cols]

    # Rebuild stat_cols after matrix column filtering
    stat_cols = _stat_cols(matrix)

    # Clear stale session state for concepts that are no longer visible
    visible = set(_all_concepts(categories))
    for key in list(st.session_state.keys()):
        if key.startswith("focus_") and key.removeprefix("focus_") not in visible:
            del st.session_state[key]

    st.sidebar.markdown("---")
    active_concepts = _render_feature_filters(categories, matrix, taxonomy)

    state = _capture_state(categories, taxonomy)
    filtered_matrix = _apply_filters(matrix, taxonomy, state, stat_cols, original_matrix=_orig_matrix)

    active_columns = [
        f"{concept}_{suffix}"
        for concept in sorted(active_concepts)
        for suffix in ("raw", "tag", "norm")
        if f"{concept}_{suffix}" in matrix.columns
    ]

    total = len(matrix)
    matches = len(filtered_matrix)
    st.sidebar.markdown("---")

    st.sidebar.checkbox(
        "Show tag & norm columns",
        value=False,
        key="show_tag_norm",
        help="When unchecked, only _raw columns are visible in Overview and Visualizer.",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Active features: {len(active_concepts)} | Matches: {matches}/{total}")

    return filtered_matrix, active_columns


__all__ = ["render_filter_sidebar"]
