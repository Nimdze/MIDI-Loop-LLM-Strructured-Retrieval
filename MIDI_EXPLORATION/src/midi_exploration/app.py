import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import streamlit as st

from midi_exploration.combined import (
    ALL_DATASETS_LABEL,
    build_combined,
    build_combined_root,
    cleanup_combined_root,
)
from midi_exploration.components.batch_export import render_export_section
from midi_exploration.components.sidebar_filters import render_filter_sidebar
from midi_exploration.loader import load_feature_matrix_cached, load_tags_cached
from midi_exploration.orchestrator import (
    WORKSPACE_DIR,
    ensure_default_libraries,
    library_paths,
    list_libraries,
)
from midi_exploration.pages import correlations, input, inspector, overview, search, visualizer

st.set_page_config(page_title="MIDI Inspection", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("MIDI Inspection")

# Auto-prepare default datasets so their libraries are ready to explore.
with st.spinner("Preparing default datasets..."):
    ensure_default_libraries()

# Apply a pending library selection (written by the Input tab) BEFORE the
# active_library widget is instantiated, so it becomes the new default.
_pending_active = st.session_state.pop("_pending_active_library", None)
if _pending_active:
    st.session_state["active_library"] = _pending_active

with st.sidebar:
    st.subheader("Library")
    available = list_libraries()
    options = ([ALL_DATASETS_LABEL] + available) if available else []
    active = st.session_state.get("active_library")
    if active not in options:
        active = options[0] if options else None
    if options:
        idx = options.index(active) if active in options else 0
        active = st.selectbox("Dataset", options, index=idx, key="active_library")
    else:
        st.info("No library imported yet. Use the Input tab to import a folder or ZIP.")
        active = None

    all_mode = active == ALL_DATASETS_LABEL
    if all_mode:
        # Sentinel cache key: switching into/out of All-mode resets filters.
        db_path = "__all__"
        taxonomy_path = None
        midi_root = None
        root_path = None
    elif active:
        lp = library_paths(active)
        db_path = str(lp["db_path"]) if lp else None
        taxonomy_path = str(lp["taxonomy_path"]) if lp else None
        midi_root = str(lp["midi_root"]) if lp else None
        root_path = Path(midi_root) if midi_root else None
    else:
        db_path = taxonomy_path = midi_root = None
        root_path = None

    if root_path and not root_path.exists():
        st.warning("Preprocessed MIDI folder not found. Piano roll will not render automatically.")

    required_tables = {"files", "tags", "raw_features", "normalized_features"}

    @st.cache_data
    def _db_is_valid(path: str) -> bool:
        if not path or not Path(path).exists():
            return False
        try:
            conn = sqlite3.connect(path)
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            conn.close()
            return required_tables.issubset(tables)
        except Exception:
            return False

    @st.cache_data
    def _load_taxonomy(path: str) -> dict[str, Any]:
        if not path or not Path(path).exists():
            return {}
        try:
            loaded = json.loads(Path(path).read_text())
            if isinstance(loaded, dict):
                return loaded
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    _CACHE_DB_KEY = "_cached_db_path"
    _CACHE_TAX_KEY = "_cached_taxonomy_path"

    db_path_str = str(db_path) if db_path and db_path != "__all__" else ""
    taxonomy_path_str = str(taxonomy_path) if taxonomy_path else ""

    filtered_matrix = None
    tags_df = None
    active_cols = None
    taxonomy: dict[str, Any] = {}

    if all_mode:
        # Build the full-corpus pooled view (all files from every library).
        _cached = st.session_state.get("_all_pooled")
        if _cached is None or _cached.get("_libs") != list_libraries():
            with st.spinner("Loading all datasets..."):
                matrix, tags, merged_tax, root = build_combined()
                if matrix.empty:
                    st.info("No libraries available. Import a dataset via the Input tab first.")
                    st.stop()
                # Drop any previously cached pooled root before replacing it.
                if _cached is not None:
                    cleanup_combined_root(_cached.get("root"))
                _cached = {"matrix": matrix, "tags": tags, "tax": merged_tax, "root": root,
                           "_libs": list_libraries()}
                st.session_state["_all_pooled"] = _cached
        matrix = _cached["matrix"]
        tags_df = _cached["tags"]
        taxonomy = _cached["tax"]
        root_path = _cached["root"]
        db_path = "__all__"  # sentinel for filter-sidebar cache reset
        db_path_str = "__all__"

        if matrix.empty:
            st.warning("All datasets pooled but contains no files.")
        else:
            filtered_matrix, active_cols = render_filter_sidebar(matrix, taxonomy, db_path)
            render_export_section(filtered_matrix, root_path)
    else:
        db_valid = _db_is_valid(db_path_str) if db_path_str else False
        taxonomy = _load_taxonomy(taxonomy_path_str) if db_valid else {}

        if db_valid:
            db_changed = st.session_state.get(_CACHE_DB_KEY) != db_path_str
            tax_changed = st.session_state.get(_CACHE_TAX_KEY) != taxonomy_path_str

            if db_changed or tax_changed or "_cached_matrix" not in st.session_state:
                matrix = load_feature_matrix_cached(db_path_str, json.dumps(taxonomy))
                tags_df = load_tags_cached(db_path_str)
                st.session_state["_cached_matrix"] = matrix
                st.session_state["_cached_tags"] = tags_df
                st.session_state[_CACHE_DB_KEY] = db_path_str
                st.session_state[_CACHE_TAX_KEY] = taxonomy_path_str
            else:
                matrix = st.session_state["_cached_matrix"]
                tags_df = st.session_state["_cached_tags"]

            if matrix.empty:
                st.warning("Database is valid but contains no files.")
            else:
                filtered_matrix, active_cols = render_filter_sidebar(matrix, taxonomy, db_path)
                render_export_section(filtered_matrix, root_path)
        else:
            st.info("Import a library using the Input tab to start exploring.")


tabs = st.tabs(["Search", "Input", "Overview", "Visualizer", "Inspector", "Correlations"])

with tabs[0]:
    if all_mode:
        search.render(corpus=True, corpus_root=root_path)
    elif db_path and taxonomy_path:
        search.render(str(db_path), str(taxonomy_path), root_path)
    else:
        st.info("Import a library using the Input tab to start exploring.")

with tabs[1]:
    input.render()

with tabs[2]:
    if filtered_matrix is not None:
        overview.render(filtered_matrix, tags_df, taxonomy, active_cols)
    else:
        st.info("No database loaded. Import a library using the Input tab.")

with tabs[3]:
    if filtered_matrix is not None:
        visualizer.render(filtered_matrix, root_path, taxonomy, active_cols)
    else:
        st.info("No database loaded. Import a library using the Input tab.")

with tabs[4]:
    if filtered_matrix is not None and db_path is not None:
        inspector.render(filtered_matrix, root_path, taxonomy, active_cols, db_path)
    else:
        st.info("No database loaded. Import a library using the Input tab.")

with tabs[5]:
    if filtered_matrix is not None and active_cols is not None:
        correlations.page.render(filtered_matrix, active_cols, taxonomy)
    else:
        st.info("No database loaded. Import a library using the Input tab.")
