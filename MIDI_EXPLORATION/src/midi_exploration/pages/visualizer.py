from pathlib import Path
from typing import Any

import pandas as pd
import pretty_midi
import streamlit as st

from midi_exploration.plotting.piano_rolls import plot_mosaic_roll_to_base64
from midi_exploration.utils import midi_download_link, resolve_midi_path


def _format_column_name(col: str) -> str:
    return col.rsplit("_", 1)[0].replace("_", " ").title()


def _highlight_family(sort_col: str | None) -> str | None:
    if not sort_col:
        return None
    col_lower = sort_col.lower()
    keywords = {
        "kick": "kick",
        "snare": "snare",
        "snare_clap": "snare",
        "hats": "hats",
        "cymbals": "cymbals",
        "hats_cymbals": "hats_cymbals",
        "perc": "perc",
    }
    for keyword, family in keywords.items():
        if keyword in col_lower or keyword.replace("_", "") in col_lower:
            return family
    return None


def _visible_columns(active_cols: list[str]) -> list[str]:
    if st.session_state.get("show_tag_norm", False):
        return active_cols
    return [c for c in active_cols if c.endswith("_raw")]


def _format_stat_value(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _stat_html(
    row: pd.Series,
    show_all: bool,
    active_cols: list[str],
    sort_col: str | None,
) -> str:
    lines = [
        f"<b>Family:</b> {row.get('family', '')}",
        f"<b>Duration:</b> {_format_stat_value(row.get('duration'))}",
        f"<b>Notes:</b> {_format_stat_value(row.get('note_count'))}",
    ]
    for col in row.index:
        if col in ("file_id", "path", "family", "metadata", "analyzed_at"):
            continue
        is_active = (col in active_cols) or (col == sort_col)
        if not show_all and not is_active:
            continue
        value = row[col]
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        color = "#00FFAA" if is_active else "#eee"
        lines.append(
            f"<span style='color:{color};'><b>{_format_column_name(col)}:</b> {_format_stat_value(value)}</span>"
        )
    return "<br>".join(lines)


def render(matrix: pd.DataFrame, midi_root: Path | None, taxonomy: dict[str, Any], active_cols: list[str]):
    _ok = midi_root.exists() if midi_root is not None else False
    st.caption(f"VIS root: `{midi_root}`  exists: `{_ok}`  type: `{type(midi_root).__name__}`")
    st.header("MIDI Visualizer Mosaic")
    st.caption('use sidebar to filter (upper left corner ">>" button)')

    if matrix.empty:
        st.warning("No files in the database.")
        return

    cluster_filter = st.session_state.get("active_cluster_filter")
    if cluster_filter:
        st.warning("Cluster filter active - only showing matching files.")
        matrix = matrix[matrix["path"].isin(cluster_filter)].reset_index(drop=True)
        if st.button("Clear cluster filter", key="clear_vis"):
            del st.session_state["active_cluster_filter"]
            st.rerun()

    visible_cols = _visible_columns(active_cols)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        n_files = st.number_input(
            "Files",
            min_value=1,
            max_value=1000,
            value=16,
            step=4,
            key="vis_files",
        )
        cell_height = st.slider(
            "Cell Height (px)", key="vis_cell_height", min_value=50, max_value=300, value=140, step=10
        )

    with c2:
        meta_cols = ["duration", "note_count"]
        sort_options = (
            ["No Sort"]
            + [c for c in meta_cols if c in matrix.columns]
            + [c for c in visible_cols if c in matrix.columns and pd.api.types.is_numeric_dtype(matrix[c])]
        )
        sort_selection = st.selectbox("Sort by", options=sort_options, key="vis_sort")
        sort_col = None if sort_selection == "No Sort" else sort_selection

        range_toggle = st.radio(
            "Vertical Range",
            options=["Standard (21-108)", "Full (0-127)", "Custom"],
            horizontal=True,
            key="vis_range",
        )
        if "Full" in range_toggle:
            y_min, y_max = 0, 127
        elif "Standard" in range_toggle:
            y_min, y_max = 21, 108
        else:
            y_min, y_max = st.slider("Custom Range", 0, 127, (36, 84), key="vis_custom_range")

    with c3:
        selection_mode = st.radio("Selection", options=["Top N", "Random N"], key="vis_selection")
        if selection_mode == "Random N":
            if "mosaic_seed" not in st.session_state:
                st.session_state.mosaic_seed = 42
            if st.button("Shuffle", width="stretch", key="vis_shuffle"):
                st.session_state.mosaic_seed += 1
                st.rerun()

    with c4:
        sort_order = st.radio("Order", options=["Descending", "Ascending"], key="vis_order")
        ascending = sort_order == "Ascending"
        show_velocity = st.checkbox("Show Velocity", value=True, key="vis_show_velocity")
        show_all_stats = st.checkbox("Show All Stats in Popups", value=False, key="vis_show_all_stats")

    filtered = matrix.copy()
    if sort_col and sort_col in filtered.columns:
        filtered = filtered.sort_values(by=sort_col, ascending=ascending, na_position="last")

    if selection_mode == "Random N":
        sample_size = min(n_files, len(filtered))
        seed = st.session_state.get("mosaic_seed", 42)
        display_df = filtered.sample(n=sample_size, random_state=seed).reset_index(drop=True)
        if sort_col and sort_col in display_df.columns:
            display_df = display_df.sort_values(by=sort_col, ascending=ascending, na_position="last")
    else:
        display_df = filtered.head(n_files).reset_index(drop=True)

    if display_df.empty:
        st.warning("No files match the filters.")
        return

    highlight = _highlight_family(sort_col)

    parts = [
        '<div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: flex-start; align-items: flex-start;">'
    ]

    for _, row in display_df.iterrows():
        relative_path = row["path"]
        midi_path = resolve_midi_path(relative_path, midi_root)

        # Debug: log unresolvable Dubstep paths
        if midi_path is None and "Dubstep" in str(relative_path):
            st.caption(f"VIS DEBUG: path=`{relative_path}` root=`{midi_root}` type=`{type(midi_root).__name__}`")

        title = str(relative_path)[:20]
        stat_name = _format_column_name(sort_col) if sort_col else "No Sort"
        stat_value = _format_stat_value(row[sort_col]) if sort_col else ""

        img_html = ""
        download_html = ""
        if midi_path and midi_path.exists():
            try:
                pm = pretty_midi.PrettyMIDI(str(midi_path))
                b64 = plot_mosaic_roll_to_base64(
                    pm,
                    title=title,
                    stat_name=stat_name,
                    stat_value=stat_value,
                    y_min=y_min,
                    y_max=y_max,
                    show_velocity=show_velocity,
                    highlight_family=highlight,
                )
                img_html = (
                    f'<img src="data:image/png;base64,{b64}" '
                    f'style="height:{cell_height}px; width:auto; border-radius:8px; '
                    f'border:1px solid #333; display:block;">'
                )
                download_html = midi_download_link(midi_path, label="Download")
            except Exception as e:
                img_html = f'<div style="color:red; padding:10px;">Error: {e}</div>'
        else:
            img_html = '<div style="color:#888; padding:10px;">File not found</div>'

        stats_html = _stat_html(row, show_all_stats, visible_cols, sort_col)

        parts.append(
            f'<div style="flex: 0 1 auto; position: relative; margin-bottom: 10px;">'
            f'<details style="cursor: pointer;">'
            f'<summary style="list-style: none; outline: none;">{img_html}</summary>'
            f'<div style="position: absolute; top: 10px; left: 0px; '
            f'min-width: 250px; max-height: 350px; overflow-y: auto; '
            f"background-color: rgb(20, 20, 20); padding: 15px; border-radius: 8px; "
            f"border: 1px solid #555; z-index: 1000; "
            f'box-shadow: 0px 8px 24px rgba(0,0,0,0.9); white-space: nowrap;">'
            f'<div style="font-size: 10px; color: #777; margin-bottom: 5px;">{relative_path}</div>'
            f"{download_html}"
            f'<div style="font-size: 12px; color: #eee; line-height: 1.6;">{stats_html}</div>'
            f"</div>"
            f"</details>"
            f"</div>"
        )

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
