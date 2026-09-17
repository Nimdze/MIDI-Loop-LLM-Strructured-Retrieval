"""Streamlit UI for the batch export panel."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.components.batch_export.exporter import (
    DEFAULT_EXPORTS_DIR,
    export_filtered_files,
)
from midi_exploration.components.batch_export.mixtape import generate_mixtape


def _default_name() -> str:
    return datetime.now().strftime("export_%Y%m%d")


def _render_name_and_destination() -> tuple[str, Path]:
    st.session_state.setdefault("export_name", _default_name())
    st.session_state.setdefault(
        "export_destination",
        str(DEFAULT_EXPORTS_DIR / st.session_state.get("export_name", _default_name())),
    )

    st.sidebar.text_input("Export name", key="export_name")
    st.sidebar.text_input("Destination folder", key="export_destination")

    name = st.session_state.get("export_name", _default_name())
    destination = Path(st.session_state.get("export_destination", str(DEFAULT_EXPORTS_DIR / name)))
    return name, destination


def _show_result(result: dict[str, Any]) -> None:
    if result["missing"]:
        st.sidebar.warning(f"Copied {result['copied']} files. Skipped {result['skipped']} missing files.")
    else:
        st.sidebar.success(f"Copied {result['copied']} files to {result['destination']}")

    st.sidebar.text_area(
        "Missing files" if result["missing"] else "Files copied",
        "\n".join(str(p) for p in (result["missing"] or list(result["destination"].iterdir()))),
        height=120,
        key="export_result",
    )


def render_export_section(
    matrix: pd.DataFrame | None,
    midi_root: Path | None,
) -> None:
    """Render the batch export controls below the feature filters."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Batch Export")

    if matrix is None or matrix.empty:
        st.sidebar.info("No files to export. Activate some features or filters.")
        return

    name, destination = _render_name_and_destination()

    if st.sidebar.button("Export matching files", key="export_button", width="stretch"):
        result = export_filtered_files(matrix, midi_root, name, destination)
        _show_result(result)

    if st.sidebar.button("Generate continuous mixtape", key="mixtape_button", width="stretch"):
        result = generate_mixtape(matrix, midi_root, destination, name)
        if result["output_path"] is None:
            st.sidebar.warning("No valid MIDI files could be concatenated.")
        else:
            st.sidebar.success(
                f"Mixtape saved to {result['output_path']} ({result['included']} files, {result['skipped']} skipped)."
            )

    st.sidebar.caption(f"{len(matrix)} file(s) match the current filters and are ready to export.")
