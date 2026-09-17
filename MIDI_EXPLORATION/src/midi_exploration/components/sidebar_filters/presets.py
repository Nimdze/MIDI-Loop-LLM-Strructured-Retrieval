"""Preset UI for the sidebar filter/focus component."""

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.components.sidebar_filters.state import (
    _apply_state,
    _capture_state,
)
from midi_exploration.presets import delete_preset, load_presets, save_preset


def _render_presets(
    categories: dict[str, list[str]],
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
    db_path: str | Path,
) -> None:
    st.sidebar.subheader("Presets")
    presets = load_presets(db_path)
    preset_names = ["None"] + sorted(presets.keys())

    selected = st.sidebar.selectbox("Load preset", preset_names, key="preset_selector")
    if selected and selected != "None":
        if st.sidebar.button("Apply", key="preset_apply"):
            _apply_state(presets[selected], categories, matrix, taxonomy)
        if st.sidebar.button("Delete", key="preset_delete"):
            delete_preset(db_path, selected)
            st.rerun()

    with st.sidebar.expander("Save current as new", expanded=False):
        name = st.text_input("Preset name", key="preset_name_input")
        if name and st.button("Save", key="preset_save"):
            state = _capture_state(categories, taxonomy)
            save_preset(db_path, name, state)
            st.rerun()

    st.sidebar.divider()
