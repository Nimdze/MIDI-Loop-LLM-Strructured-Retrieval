"""Small utilities for the exploration UI."""

import base64
from pathlib import Path
from typing import Any


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # MIDI_RETRIEVE/


def resolve_midi_path(stored_path: str, midi_root: Path | None) -> Path | None:
    """Resolve a stored path against roots in priority order:

    1. combined root (midi_root / stored_path)
    2. stored_path as absolute/relative path
    3. workspace dir (~/midi_exploration/workspace / stored_path)
    4. default_dataset/<dataset>_preprocessed/clean/<basename>
    """
    # Priority 1: combined / midi_root
    if midi_root and midi_root.exists():
        candidate = midi_root / stored_path
        if candidate.exists():
            return candidate

    # Priority 2: stored_path as-is (absolute or CWD-relative)
    candidate = Path(stored_path)
    if candidate.exists():
        return candidate

    # Priority 3: workspace-relative (e.g. "ASF-4/foo.mid")
    workspace = Path.home() / "midi_exploration" / "workspace"
    if workspace.exists():
        candidate = workspace / stored_path
        if candidate.exists():
            return candidate

    # Priority 4: default_dataset/<dataset>_preprocessed/clean/<basename>
    if "/" in stored_path:
        ds = stored_path.split("/")[0]
        base = _PROJECT_ROOT / "default_dataset" / f"{ds}_preprocessed" / "clean"
        tail = stored_path.split("/", 1)[1] if "/" in stored_path else stored_path
        candidate = base / tail
        if candidate.exists():
            return candidate

    return None


def format_value(value: Any) -> str:
    """Pretty-print a raw feature value for HTML display."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, list):
        return ", ".join(format_value(item) for item in value)
    return str(value)


def midi_download_link(midi_path: Path | str, label: str = "Download", filename: str | None = None) -> str:
    """Return a HTML download link for a MIDI file."""
    path = Path(midi_path)
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    filename = filename or path.name
    return (
        f'<a href="data:audio/midi;base64,{b64}" download="{filename}" '
        f'style="display:inline-block; width:100%; text-align:center; margin-top:8px; '
        f"padding:4px 0px; background-color:#4A5568; color:white; text-decoration:none; "
        f'font-weight:500; border-radius:4px; font-size:10px; border:1px solid #718096;">'
        f"{label}</a>"
    )
