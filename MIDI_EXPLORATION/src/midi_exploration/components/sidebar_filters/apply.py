"""Apply captured filters to a DataFrame."""

from typing import Any

import pandas as pd

from midi_exploration.components.sidebar_filters.helpers import (
    _apply_numeric_filter,
    _apply_tag_filter,
    _range_is_active,
)


def _apply_filters(
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
    state: dict[str, Any],
    stat_cols: list[str],
    original_matrix: pd.DataFrame | None = None,
) -> pd.DataFrame:
    result = matrix

    family = state.get("family", "All")
    if family != "All":
        result = result[result["family"] == family]

    # Use the original unfiltered matrix for range min/max determination so that
    # column filtering (e.g. pitched/drums) does not skew what constitutes an
    # "active" range.
    range_matrix = original_matrix if original_matrix is not None else matrix

    active_concepts = set(state.get("active_concepts", []))
    concept_filters = state.get("concept_filters", {})

    for concept in active_concepts:
        filters = concept_filters.get(concept, {})

        tag_col = f"{concept}_tag"
        if tag_col in result.columns:
            include = filters.get("tag_include", [])
            exclude = filters.get("tag_exclude", [])
            result = _apply_tag_filter(result, concept, include, exclude, taxonomy)

        norm_col = f"{concept}_norm"
        if norm_col in result.columns:
            norm_range = filters.get("norm_range")
            if _range_is_active(norm_range, range_matrix, norm_col):
                result = _apply_numeric_filter(result, norm_col, norm_range)

        raw_col = f"{concept}_raw"
        if raw_col in result.columns:
            raw_range = filters.get("raw_range")
            if _range_is_active(raw_range, range_matrix, raw_col):
                result = _apply_numeric_filter(result, raw_col, raw_range)

    return result
