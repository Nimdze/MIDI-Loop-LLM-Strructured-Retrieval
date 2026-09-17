"""Single-file gallery/auditor view with tag display and rhythm debug tools."""

import html
from pathlib import Path
from typing import Any

import pandas as pd
import pretty_midi
import streamlit as st

from midi_exploration.loader import AnalysisLoader
from midi_exploration.plotting import debug_grid
from midi_exploration.plotting.piano_rolls import plot_inspector_roll_to_base64
from midi_exploration.utils import format_value, resolve_midi_path

CATEGORY_COLORS = {
    "metadata": "#569CD6",
    "rhythm": "#CE9178",
    "harmony": "#4EC9B0",
    "melody": "#C586C0",
    "expression": "#DCDCAA",
    "tonality": "#B5CEA8",
    "drums": "#D16969",
    "placeholder": "#AAAAAA",
}


def _category_label(category: str) -> str:
    return "META" if category == "metadata" else category.upper()


def _active_concepts(active_cols: list[str]) -> set[str]:
    concepts = set()
    for col in active_cols:
        if col.endswith(("_raw", "_tag", "_norm")):
            concepts.add(col[:-4])
    return concepts


def _tag_payload_html(payload: dict[str, Any], active_concepts: set[str] | None = None) -> str:
    concepts = payload.get("concepts", {})
    if not concepts:
        return "No tags stored for this file."

    _CATEGORY_ORDER = [
        "metadata",
        "rhythm",
        "expression",
        "tonality",
        "harmony",
        "melody",
        "drums",
        "placeholder",
    ]

    def _category_order_key(category: str) -> int:
        try:
            return _CATEGORY_ORDER.index(category)
        except ValueError:
            return 999

    rows = []
    for category in sorted(concepts.keys(), key=_category_order_key):
        entries = concepts.get(category, {})
        if not entries:
            continue
        category_rows = []
        color = CATEGORY_COLORS.get(category, "#AAAAAA")
        for concept_name, values in entries.items():
            level = values.get("tag")
            if level is None:
                continue
            raw = values.get("raw")
            raw_text = f" (raw: {format_value(raw)})" if raw is not None else ""
            is_active = active_concepts is not None and concept_name in active_concepts
            marker = " ■" if is_active else ""
            category_rows.append(
                f"<div style='margin-bottom:4px;'>"
                f"<span style='color:{html.escape(color)}; font-weight:bold;'>"
                f"[{html.escape(concept_name.upper())}]</span>"
                f"{html.escape(marker)} "
                f"{html.escape(str(level))}{html.escape(raw_text)}"
                f"</div>"
            )
        if category_rows:
            rows.append(
                f"<div style='margin-bottom:12px;'>"
                f"<div style='color:{html.escape(color)}; font-weight:bold; margin-bottom:4px;'>"
                f"[{html.escape(_category_label(category))}]</div>"
                f"{''.join(category_rows)}"
                f"</div>"
            )
    return "".join(rows) if rows else "No tags stored for this file."


def _rhythm_stats_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rhythm = payload.get("concepts", {}).get("rhythm", {})
    return {name: entry["raw"] for name, entry in rhythm.items() if entry.get("raw") is not None}


def _render_groove_stats(rhythm_stats: dict[str, Any]) -> None:
    if not rhythm_stats:
        st.text("No groove data found in rhythm stats")
        return
    groove_fields = [
        k for k in rhythm_stats.keys() if k.startswith(("grid_attempt_pct", "grid_success_pct", "groove_"))
    ]
    if groove_fields:
        st.markdown("**Grid Dual-Metrics (Attempt | Success):**")
        for field in sorted(groove_fields):
            val = rhythm_stats[field]
            if isinstance(val, (int, float)):
                st.code(f"{field}: {val:.2f}%")
            else:
                st.code(f"{field}: {val}")
    total = rhythm_stats.get("groove_total_events")
    st.markdown(f"**Total Events:** {total if total is not None else 'N/A'}")


def _render_grid_debug(midi_path: Path, rhythm_stats: dict[str, Any]) -> None:
    result = debug_grid.render_grid_debug(str(midi_path), rhythm_stats)
    if result is None:
        return
    st.markdown(
        f'<img src="data:image/png;base64,{result["base64"]}" style="width:100%;">',
        unsafe_allow_html=True,
    )
    st.markdown("### Assignment Summary")
    st.dataframe(pd.DataFrame(result["summary"]), width="stretch", hide_index=True)
    st.markdown("### Detailed Assignments")
    st.dataframe(pd.DataFrame(result["detail"]), width="stretch", height=300, hide_index=True)


def _render_fresh_comparison(rhythm_stats: dict[str, Any], fresh_results: dict[str, float]) -> None:
    st.markdown("### Fresh Calculation vs Stored")
    comparison = []
    for key in sorted(fresh_results.keys()):
        stored = rhythm_stats.get(key, "N/A")
        fresh = fresh_results[key]
        stored_str = f"{stored:.2f}%" if isinstance(stored, (int, float)) else str(stored)
        fresh_str = f"{fresh:.2f}%"
        match = isinstance(stored, (int, float)) and abs(stored - fresh) < 1e-6
        comparison.append(
            {
                "metric": key,
                "stored": stored_str,
                "fresh": fresh_str,
                "match": "✅" if match else "❌",
            }
        )
    st.dataframe(pd.DataFrame(comparison), width="stretch", hide_index=True)


def render(
    matrix: pd.DataFrame, midi_root: Path | None, taxonomy: dict[str, Any], active_cols: list[str], db_path: str
):
    st.header("Inspector / Gallery")
    st.caption('use sidebar to filter (upper left corner ">>" button)')

    active_concepts = _active_concepts(active_cols)

    if matrix.empty:
        st.warning("No files in the database.")
        return

    show_debug = st.toggle("Show Debug Stats", value=False)
    show_grid_debug = st.toggle("Show Grid Assignment", value=False)

    file_options = [
        {
            "file_id": row["file_id"],
            "label": row["path"],
            "path": row["path"],
            "library": row.get("library", ""),
        }
        for _, row in matrix.iterrows()
    ]

    if not file_options:
        st.warning("No files available.")
        return

    if "viz_idx" not in st.session_state:
        st.session_state.viz_idx = 0
    if st.session_state.viz_idx >= len(file_options):
        st.session_state.viz_idx = 0

    file_labels = [f["label"] for f in file_options]
    current_expected = file_labels[st.session_state.viz_idx]
    if "file_selector_key" not in st.session_state or st.session_state.file_selector_key != current_expected:
        st.session_state.file_selector_key = current_expected

    def _on_change():
        label = st.session_state.file_selector_key
        if label in file_labels:
            st.session_state.viz_idx = file_labels.index(label)
        else:
            st.session_state.viz_idx = 0

    st.selectbox("Select MIDI file:", options=file_labels, key="file_selector_key", on_change=_on_change)

    current = file_options[st.session_state.viz_idx]

    file_id = current["file_id"]
    relative_path = current["path"]
    midi_path = resolve_midi_path(relative_path, midi_root)

    if db_path == "__all__":
        from midi_exploration.orchestrator import library_paths as _lp
        _lib = current.get("library", "")
        _resolved = _lp(_lib)
        _db = str(_resolved["db_path"]) if _resolved else None
        _raw_id = int(str(file_id).split("_", 1)[-1]) if _resolved else int(file_id)
    else:
        _db = db_path
        _raw_id = int(file_id)

    with AnalysisLoader(_db) as loader:
        payload = loader.load_file_payload(_raw_id, taxonomy)
    rhythm_stats = _rhythm_stats_from_payload(payload)

    col_image, col_tag = st.columns([2, 1])
    with col_image:
        if midi_path and midi_path.exists():
            try:
                pm = pretty_midi.PrettyMIDI(str(midi_path))
                b64 = plot_inspector_roll_to_base64(pm, title=relative_path)
                st.markdown(
                    f'<img src="data:image/png;base64,{b64}" '
                    f'style="width:100%; border-radius:8px; border:1px solid #333; display:block;">',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"Could not render piano roll: {e}")
        else:
            st.info(f"MIDI file not found at: {midi_path}. Set the correct MIDI library root folder in the sidebar.")

    with col_tag:
        st.subheader("Tags")
        tag_html = _tag_payload_html(payload, active_concepts)
        st.markdown(
            f'<div style="border:1px solid #333; border-radius:8px; overflow:hidden; background:#0E1117; padding:20px; '
            f'font-family: monospace; font-size:0.9rem; line-height:1.8; color:#EEE;">'
            f"{tag_html}"
            f"</div>",
            unsafe_allow_html=True,
        )

    if show_debug:
        with st.expander("DEBUG: Raw Groove Stats", expanded=True):
            _render_groove_stats(rhythm_stats)

    if show_grid_debug and midi_path and midi_path.exists():
        with st.expander("GRID ASSIGNMENT DEBUG", expanded=True):
            _render_grid_debug(midi_path, rhythm_stats)
            if st.button("Recalculate Groove Fresh", key=f"recalc_{file_id}"):
                fresh_results = debug_grid.recalculate_groove_fresh(str(midi_path))
                if fresh_results:
                    _render_fresh_comparison(rhythm_stats, fresh_results)

    st.write("")
    col_prev, col_next, col_dl = st.columns([1, 1, 4])
    with col_prev:
        if st.button("Previous", width="stretch") and st.session_state.viz_idx > 0:
            st.session_state.viz_idx -= 1
            st.rerun()
    with col_next:
        if st.button("Next", width="stretch") and st.session_state.viz_idx < len(file_options) - 1:
            st.session_state.viz_idx += 1
            st.rerun()
    with col_dl:
        if midi_path and midi_path.exists():
            with open(midi_path, "rb") as f:
                st.download_button("Download MIDI", f, file_name=Path(relative_path).name, key=f"dl_{file_id}")
