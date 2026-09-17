"""Filter UI for the sidebar filter/focus component."""

from functools import partial
from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.components.sidebar_filters.helpers import (
    DRUM_PIECE_ORDER,
    SECTION_ORDER,
    _all_concepts,
    _build_feature_descriptions,
    _level_names_present,
)

_FOCUS_TRACKING_KEY = "overview_focused_concept"


def _set_all_concepts(categories: dict[str, list[str]], value: bool) -> None:
    for concept in _all_concepts(categories):
        st.session_state[f"focus_{concept}"] = value


def _on_active_change(concept: str) -> None:
    """Remember the last concept toggled active/inactive."""
    if st.session_state.get(f"focus_{concept}", False):
        st.session_state[_FOCUS_TRACKING_KEY] = concept


def _on_category_change(category: str, concepts: list[str]) -> None:
    """Toggle every concept in a category based on the category checkbox."""
    value = st.session_state.get(f"focus_category_{category}", False)
    for concept in concepts:
        st.session_state[f"focus_{concept}"] = value
    if value and concepts:
        st.session_state[_FOCUS_TRACKING_KEY] = concepts[0]


def _render_quick_filters(matrix: pd.DataFrame, stat_cols: list[str]) -> None:
    family_options = ["All"] + sorted(matrix["family"].dropna().unique().tolist())
    selected_family = st.session_state.get("filter_family", "pitched")
    if selected_family not in family_options:
        selected_family = "All"
    st.sidebar.selectbox(
        "Family",
        family_options,
        index=family_options.index(selected_family),
        key="filter_family",
    )


def _render_concept_filter(
    concept: str,
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> bool:
    """Render the active checkbox and per-concept filters for one concept."""
    entry = taxonomy.get(concept, {})
    llm = entry.get("llm", {})
    desc = llm.get("description", "")
    if not desc and entry.get("base_concept"):
        desc = (
            taxonomy.get(entry["base_concept"], {})
            .get("llm", {})
            .get("description", "")
        )
    active = st.checkbox(
        concept,
        key=f"focus_{concept}",
        on_change=partial(_on_active_change, concept),
        help=desc,
    )

    if not active:
        return False

    show_tag_norm = st.session_state.get("show_tag_norm", False)

    tag_col = f"{concept}_tag"
    norm_col = f"{concept}_norm"
    raw_col = f"{concept}_raw"

    if show_tag_norm and tag_col in matrix.columns:
        level_names = _level_names_present(concept, matrix, taxonomy)
        if level_names:
            st.multiselect(
                "Include levels",
                level_names,
                key=f"filter_include_{concept}",
            )
            st.multiselect(
                "Exclude levels",
                level_names,
                key=f"filter_exclude_{concept}",
            )

    if show_tag_norm and norm_col in matrix.columns:
        vals = matrix[norm_col].dropna()
        if not vals.empty:
            lo = float(vals.min())
            hi = float(vals.max())
            if lo < hi:
                c1, c2 = st.columns(2)
                with c1:
                    st.number_input(
                        "Norm from",
                        value=st.session_state.get(f"filter_norm_{concept}", (lo, hi))[0],
                        min_value=lo,
                        max_value=hi,
                        key=f"filter_norm_{concept}_lo",
                    )
                with c2:
                    st.number_input(
                        "Norm to",
                        value=st.session_state.get(f"filter_norm_{concept}", (lo, hi))[1],
                        min_value=lo,
                        max_value=hi,
                        key=f"filter_norm_{concept}_hi",
                    )
                st.session_state[f"filter_norm_{concept}"] = (
                    st.session_state[f"filter_norm_{concept}_lo"],
                    st.session_state[f"filter_norm_{concept}_hi"],
                )
            else:
                st.caption(f"Constant value: {lo:.3f}")

    if raw_col in matrix.columns and pd.api.types.is_numeric_dtype(matrix[raw_col]):
        vals = matrix[raw_col].dropna()
        if not vals.empty:
            lo = float(vals.min())
            hi = float(vals.max())
            if lo < hi:
                c1, c2 = st.columns(2)
                with c1:
                    st.number_input(
                        "Raw from",
                        value=st.session_state.get(f"filter_raw_{concept}", (lo, hi))[0],
                        min_value=lo,
                        max_value=hi,
                        key=f"filter_raw_{concept}_lo",
                    )
                with c2:
                    st.number_input(
                        "Raw to",
                        value=st.session_state.get(f"filter_raw_{concept}", (lo, hi))[1],
                        min_value=lo,
                        max_value=hi,
                        key=f"filter_raw_{concept}_hi",
                    )
                st.session_state[f"filter_raw_{concept}"] = (
                    st.session_state[f"filter_raw_{concept}_lo"],
                    st.session_state[f"filter_raw_{concept}_hi"],
                )
            else:
                st.caption(f"Constant value: {lo:.3f}")

    return True


def _render_feature_filters(
    categories: dict[str, list[str]],
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> set[str]:
    st.sidebar.subheader("Feature Filters")

    all_concepts = _all_concepts(categories)
    if not all_concepts:
        st.sidebar.info("No concepts available.")
        return set()

    c1, c2 = st.sidebar.columns(2)
    if c1.button("Activate all", key="filters_activate_all", width="stretch"):
        _set_all_concepts(categories, True)
    if c2.button("Deactivate all", key="filters_deactivate_all", width="stretch"):
        _set_all_concepts(categories, False)

    selected_family = st.session_state.get("filter_family", "pitched")

    if selected_family == "drums":
        active_concepts = _render_drum_feature_filters(categories, matrix, taxonomy)
    else:
        active_concepts = _render_pitched_feature_filters(categories, matrix, taxonomy)

    focused = st.session_state.get(_FOCUS_TRACKING_KEY)
    if focused not in active_concepts and active_concepts:
        st.session_state[_FOCUS_TRACKING_KEY] = next(iter(sorted(active_concepts)))

    return active_concepts


def _render_drum_feature_filters(
    categories: dict[str, dict[str, list[str]]],
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> set[str]:
    feat_descs = _build_feature_descriptions(taxonomy)
    active_concepts: set[str] = set()
    for piece_name in DRUM_PIECE_ORDER:
        subcategories = categories.get(piece_name, {})
        if not subcategories:
            continue

        piece_concepts = [c for sub_list in subcategories.values() for c in sub_list]
        all_active = all(st.session_state.get(f"focus_{c}", False) for c in piece_concepts)
        st.session_state[f"focus_category_{piece_name}"] = all_active

        with st.sidebar.expander(piece_name, expanded=False):
            st.checkbox(
                "Activate all in this kit piece",
                key=f"focus_category_{piece_name}",
                on_change=partial(_on_category_change, piece_name, piece_concepts),
            )
            st.divider()
            for subcat_name, concepts in sorted(subcategories.items()):
                cat_key = f"{piece_name}_{subcat_name}"
                sub_all_active = all(
                    st.session_state.get(f"focus_{c}", False) for c in concepts
                )
                st.session_state[f"focus_category_{cat_key}"] = sub_all_active

                sub_desc = feat_descs.get(subcat_name, "")
                with st.expander(subcat_name, expanded=False):
                    st.checkbox(
                        f"{subcat_name} — all",
                        key=f"focus_category_{cat_key}",
                        on_change=partial(_on_category_change, cat_key, concepts),
                        help=sub_desc,
                    )
                    for concept in sorted(concepts):
                        if _render_concept_filter(concept, matrix, taxonomy):
                            active_concepts.add(concept)
    return active_concepts


def _render_pitched_feature_filters(
    categories: dict[str, list[str]],
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> set[str]:
    feat_descs = _build_feature_descriptions(taxonomy)
    active_concepts: set[str] = set()
    for section in SECTION_ORDER + ["other"]:
        concepts = categories.get(section, [])
        if not concepts:
            continue

        all_active = all(st.session_state.get(f"focus_{c}", False) for c in concepts)
        st.session_state[f"focus_category_{section}"] = all_active

        section_desc = feat_descs.get(section, "")
        with st.sidebar.expander(section, expanded=False):
            st.checkbox(
                "Activate all in this category",
                key=f"focus_category_{section}",
                on_change=partial(_on_category_change, section, concepts),
                help=section_desc,
            )
            st.divider()
            for concept in sorted(concepts):
                if _render_concept_filter(concept, matrix, taxonomy):
                    active_concepts.add(concept)
    return active_concepts
