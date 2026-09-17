import importlib.util
from pathlib import Path

import streamlit as st

from midi_exploration.orchestrator import (
    WORKSPACE_DIR,
    _sanitize_label,
    run_folder_import,
    run_import_pipeline,
)

_DEFAULTS = {
    "input_label": "MyLibrary",
    "input_source": "Folder path",
    "input_mode": "Create / Replace",
    "input_normalize_tempo": True,
    "input_target_bpm": 120.0,
    "input_slicing": False,
    "input_slice_bars": 8,
    "input_split": True,
}


def _set_defaults() -> None:
    for key, value in _DEFAULTS.items():
        st.session_state.setdefault(key, value)


def _packages_available() -> bool:
    return (
        importlib.util.find_spec("midi_analyzer_tagger") is not None
        and importlib.util.find_spec("midi_preprocessor") is not None
    )


def render() -> None:
    """Render the Input/Import tab."""
    _set_defaults()

    st.header("Input / Import")
    st.write(
        "Point to a folder of MIDI files (or upload a ZIP). The app cleans and analyzes "
        "it, stores it internally, and automatically routes search to it."
    )

    packages_available = _packages_available()
    if not packages_available:
        st.warning(
            "The pre-processor and analyzer packages are not installed in the Python "
            "environment running this app. Install them with:\n\n"
            "cd MIDI_RETRIEVE/MIDI_EXPLORATION\n"
            ".venv/bin/python -m pip install -e ../MIDI_PREPROCESSOR\n"
            ".venv/bin/python -m pip install -e ../MIDI_ANALYZER_TAGGER\n\n"
            "Then reload the page."
        )

    st.radio("Source", options=["Folder path", "Upload ZIP"], key="input_source", horizontal=True)
    source = st.session_state.get("input_source", _DEFAULTS["input_source"])

    uploaded_file = None
    folder_path = None
    if source == "Folder path":
        folder_path = st.text_input(
            "MIDI library folder",
            key="input_folder",
            placeholder="/path/to/your/midi/library",
            help="A directory containing MIDI files. It is copied/cleaned/analyzed internally.",
        )
    else:
        uploaded_file = st.file_uploader("Upload library ZIP", type=["zip"], key="input_zip")

    with st.expander("Options", expanded=True):
        st.text_input("Dataset label", key="input_label")
        if source == "Upload ZIP":
            st.radio(
                "Import mode",
                options=["Create / Replace", "Append"],
                key="input_mode",
                help="Create replaces the whole dataset; Append adds the new files to the existing dataset.",
            )
        st.checkbox("Split by instrument", key="input_split")
        st.checkbox("Standardize tempo", key="input_normalize_tempo")
        st.number_input(
            "Target BPM",
            min_value=30.0,
            max_value=300.0,
            step=1.0,
            key="input_target_bpm",
        )
        st.checkbox("Enable loop slicing", key="input_slicing")
        slicing_enabled = st.session_state.get("input_slicing", _DEFAULTS["input_slicing"])
        st.number_input(
            "Slice length (bars)",
            min_value=1,
            max_value=128,
            step=1,
            key="input_slice_bars",
            disabled=not slicing_enabled,
        )

    can_run = packages_available and ((source == "Folder path" and folder_path) or uploaded_file)
    if st.button("Import and analyze", type="primary", key="input_run", disabled=not can_run):
        label = st.session_state.get("input_label", _DEFAULTS["input_label"])
        if not label:
            st.warning("Enter a dataset label.")
            return

        try:
            with st.status("Importing library...", expanded=True) as status:
                if source == "Folder path":
                    if not (folder_path and Path(folder_path).is_dir()):
                        st.warning("Enter a valid MIDI folder path.")
                        return
                    result = run_folder_import(
                        folder_path=folder_path,
                        label=label,
                        normalize_tempo=st.session_state.get("input_normalize_tempo", _DEFAULTS["input_normalize_tempo"]),
                        target_bpm=st.session_state.get("input_target_bpm", _DEFAULTS["input_target_bpm"]),
                        slice_bars=st.session_state.get("input_slice_bars", _DEFAULTS["input_slice_bars"])
                        if st.session_state.get("input_slicing", _DEFAULTS["input_slicing"])
                        else None,
                        no_split=not st.session_state.get("input_split", _DEFAULTS["input_split"]),
                        progress=status.write,
                    )
                else:
                    if not uploaded_file:
                        st.warning("Upload a ZIP file first.")
                        return
                    result = run_import_pipeline(
                        uploaded_file=uploaded_file,
                        label=label,
                        mode=st.session_state.get("input_mode", _DEFAULTS["input_mode"]),
                        normalize_tempo=st.session_state.get("input_normalize_tempo", _DEFAULTS["input_normalize_tempo"]),
                        target_bpm=st.session_state.get("input_target_bpm", _DEFAULTS["input_target_bpm"]),
                        slice_bars=st.session_state.get("input_slice_bars", _DEFAULTS["input_slice_bars"])
                        if st.session_state.get("input_slicing", _DEFAULTS["input_slicing"])
                        else None,
                        no_split=not st.session_state.get("input_split", _DEFAULTS["input_split"]),
                        progress=status.write,
                    )

            preprocess = result["preprocess_result"]
            analyze = result["analyze_result"]
            st.success(f"Done. {analyze['processed']} files analyzed, {analyze['failed']} failed.")
            st.caption(
                f"Preprocessed: {preprocess['processed']} valid, {preprocess['skipped']} skipped, "
                f"{preprocess.get('failed', 0)} failed; "
                f"analyzer: {analyze['processed']} processed, {analyze['skipped']} skipped, "
                f"{analyze['failed']} failed."
            )

            # Auto-route: make this the active library so search and the other tabs use it.
            st.session_state["_pending_active_library"] = label
            st.rerun()
        except ModuleNotFoundError as e:
            st.error(str(e))

    with st.expander("Where the data lives"):
        workspace_label = _sanitize_label(st.session_state.get("input_label", _DEFAULTS["input_label"]))
        st.code(str(WORKSPACE_DIR / workspace_label))
        st.caption("Each dataset is stored in its own folder under the workspace and routed automatically.")


__all__ = ["render"]
