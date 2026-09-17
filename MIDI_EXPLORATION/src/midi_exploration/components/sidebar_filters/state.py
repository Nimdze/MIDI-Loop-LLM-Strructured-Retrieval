"""Session state management for the sidebar filter/focus component."""

from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.components.sidebar_filters.helpers import _all_concepts


def _clear_filter_keys() -> None:
    """Remove all state keys managed by this component (used on DB change)."""
    for key in list(st.session_state.keys()):
        if (
            key.startswith(("focus_", "filter_", "preset_"))
            or key == "active_cluster_filter"
            or key == "overview_focused_concept"
        ):
            del st.session_state[key]
    st.session_state.pop("_filter_col_hash", None)


def _initialize_state(
    categories: dict[str, list[str]],
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
    concept_filters: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Set sensible defaults for any filter state keys that are missing.

    If concept_filters is provided, override the default numeric/tag ranges with
    the preset values for those concepts. This guarantees that applying a preset
    does not lose filters for concepts that were not yet initialized.
    """
    concept_filters = concept_filters or {}
    all_concepts = _all_concepts(categories)

    norm_cols = [
        f"{c}_norm" for c in all_concepts if f"{c}_norm" in matrix.columns
    ]
    raw_cols = [
        f"{c}_raw"
        for c in all_concepts
        if f"{c}_raw" in matrix.columns and pd.api.types.is_numeric_dtype(matrix[f"{c}_raw"])
    ]

    col_hash = hash(tuple(sorted(matrix.columns)))
    if st.session_state.get("_filter_col_hash") != col_hash:
        norm_stats = matrix[norm_cols].agg(["min", "max"]) if norm_cols else None
        raw_stats = matrix[raw_cols].agg(["min", "max"]) if raw_cols else None
        st.session_state["_filter_col_hash"] = col_hash
    else:
        norm_stats = None
        raw_stats = None

    for concept in all_concepts:
        st.session_state.setdefault(f"focus_{concept}", False)

        tag_col = f"{concept}_tag"
        if tag_col in matrix.columns:
            st.session_state.setdefault(f"filter_include_{concept}", [])
            st.session_state.setdefault(f"filter_exclude_{concept}", [])

        filters = concept_filters.get(concept, {})
        preset_norm = filters.get("norm_range")
        preset_raw = filters.get("raw_range")
        preset_include = filters.get("tag_include")
        preset_exclude = filters.get("tag_exclude")

        norm_col = f"{concept}_norm"
        norm_key = f"filter_norm_{concept}"
        if norm_col in matrix.columns:
            if preset_norm is not None:
                st.session_state[norm_key] = tuple(preset_norm)
            elif norm_key not in st.session_state:
                if norm_stats is not None and norm_col in norm_stats:
                    lo = float(norm_stats[norm_col]["min"])
                    hi = float(norm_stats[norm_col]["max"])
                    st.session_state[norm_key] = (lo, hi)

        raw_col = f"{concept}_raw"
        raw_key = f"filter_raw_{concept}"
        if raw_col in matrix.columns and pd.api.types.is_numeric_dtype(matrix[raw_col]):
            if preset_raw is not None:
                st.session_state[raw_key] = tuple(preset_raw)
            elif raw_key not in st.session_state:
                if raw_stats is not None and raw_col in raw_stats:
                    lo = float(raw_stats[raw_col]["min"])
                    hi = float(raw_stats[raw_col]["max"])
                    st.session_state[raw_key] = (lo, hi)

        include_key = f"filter_include_{concept}"
        if preset_include is not None and tag_col in matrix.columns:
            st.session_state[include_key] = list(preset_include)

        exclude_key = f"filter_exclude_{concept}"
        if preset_exclude is not None and tag_col in matrix.columns:
            st.session_state[exclude_key] = list(preset_exclude)

    st.session_state.setdefault("filter_family", "pitched")


def _sanitize_state(matrix: pd.DataFrame, stat_cols: list[str]) -> None:
    """Make sure loaded preset values are still valid for the current matrix."""
    family_options = ["All"] + sorted(matrix["family"].dropna().unique().tolist())
    selected_family = st.session_state.get("filter_family", "pitched")
    if selected_family not in family_options:
        st.session_state["filter_family"] = "All"


def _capture_state(
    categories: dict[str, list[str]],
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    state = {
        "family": st.session_state.get("filter_family", "pitched"),
        "active_concepts": [],
        "concept_filters": {},
    }
    for concept in _all_concepts(categories):
        if st.session_state.get(f"focus_{concept}", False):
            state["active_concepts"].append(concept)

    for concept in state["active_concepts"]:
        filters: dict[str, Any] = {}
        include = st.session_state.get(f"filter_include_{concept}", [])
        exclude = st.session_state.get(f"filter_exclude_{concept}", [])
        if include:
            filters["tag_include"] = list(include)
        if exclude:
            filters["tag_exclude"] = list(exclude)

        norm_key = f"filter_norm_{concept}"
        if norm_key in st.session_state:
            filters["norm_range"] = list(st.session_state[norm_key])

        raw_key = f"filter_raw_{concept}"
        if raw_key in st.session_state:
            filters["raw_range"] = list(st.session_state[raw_key])

        if filters:
            state["concept_filters"][concept] = filters

    return state


def _apply_state(
    state: dict[str, Any],
    categories: dict[str, list[str]],
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> None:
    """Apply a saved preset to the current session state."""
    st.session_state["filter_family"] = state.get("family", "pitched")

    active_set = set(state.get("active_concepts", []))
    for concept in _all_concepts(categories):
        st.session_state[f"focus_{concept}"] = concept in active_set

    concept_filters = state.get("concept_filters", {})

    _initialize_state(categories, matrix, taxonomy, concept_filters=concept_filters)
    _sanitize_state(matrix, [c for c in matrix.columns if c.endswith(("_raw", "_tag", "_norm"))])
    st.rerun()
