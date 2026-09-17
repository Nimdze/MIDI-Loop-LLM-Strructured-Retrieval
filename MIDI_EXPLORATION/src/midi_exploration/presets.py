"""Persist feature-focus and filter presets next to an analysis database.

Presets are stored as JSON in a file named ``<analysis.db>.presets.json`` in the
same directory as the database. This keeps presets tied to the project they
belong to.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _presets_path(db_path: str | Path) -> Path:
    path = Path(db_path)
    return path.parent / (path.name + ".presets.json")


def _validate_presets(data: Any) -> dict[str, Any]:
    """Ensure loaded presets are a JSON object."""
    return data if isinstance(data, dict) else {}


def load_presets(db_path: str | Path) -> dict[str, Any]:
    """Return all saved presets for a database."""
    path = _presets_path(db_path)
    if not path.exists():
        return {}
    try:
        return _validate_presets(json.loads(path.read_text()))
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not load presets from %s", path, exc_info=True)
        return {}


def _write_presets(path: Path, presets: dict[str, Any]) -> None:
    """Write presets to disk, logging I/O errors instead of crashing."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(presets, indent=2))
    except OSError:
        logger.warning("Could not write presets to %s", path, exc_info=True)


def save_preset(db_path: str | Path, name: str, state: dict[str, Any]) -> None:
    """Save a named filter/focus state to the preset file."""
    presets = load_presets(db_path)
    presets[name] = state
    _write_presets(_presets_path(db_path), presets)


def delete_preset(db_path: str | Path, name: str) -> None:
    """Delete a named preset."""
    presets = load_presets(db_path)
    presets.pop(name, None)
    _write_presets(_presets_path(db_path), presets)
