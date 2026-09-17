"""Persist last-used project settings across Streamlit sessions.

The state file lives in a dedicated ``workspace/.state`` subdirectory so the app
will reopen the last analyzed dataset without requiring a fresh import every
time.
"""

import json
from pathlib import Path
from typing import Any

from midi_exploration.orchestrator import WORKSPACE_DIR

_STATE_KEYS = (
    "project_db_path",
    "project_midi_root",
    "project_taxonomy_path",
    "label",
)


def _state_dir() -> Path:
    return WORKSPACE_DIR / ".state"


def _state_file() -> Path:
    return _state_dir() / "settings.json"


def _validate_state(data: Any) -> dict[str, Any]:
    """Return only recognized keys from a loaded state dict."""
    if not isinstance(data, dict):
        return {}
    return {k: data.get(k) for k in _STATE_KEYS if k in data}


def load_state() -> dict[str, Any]:
    """Load the persisted project settings if they exist."""
    file = _state_file()
    if not file.exists():
        return {}
    try:
        return _validate_state(json.loads(file.read_text()))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(
    project_db_path: str,
    project_midi_root: str,
    project_taxonomy_path: str,
    label: str | None = None,
) -> None:
    """Persist the given project settings for the next session."""
    data: dict[str, Any] = {
        "project_db_path": str(project_db_path),
        "project_midi_root": str(project_midi_root),
        "project_taxonomy_path": str(project_taxonomy_path),
    }
    if label is not None:
        data["label"] = label
    _state_dir().mkdir(parents=True, exist_ok=True)
    _state_file().write_text(json.dumps(data, indent=2))


__all__ = ["load_state", "save_state"]
