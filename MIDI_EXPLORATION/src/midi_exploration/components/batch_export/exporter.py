"""Backend logic for exporting filtered MIDI files to a folder."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from midi_exploration.orchestrator import WORKSPACE_DIR
from midi_exploration.utils import resolve_midi_path

DEFAULT_EXPORTS_DIR = WORKSPACE_DIR / "exports"


def _default_export_name() -> str:
    return datetime.now().strftime("export_%Y%m%d_%H%M%S")


def _ensure_export_dir(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)


def export_filtered_files(
    matrix: pd.DataFrame,
    midi_root: Path | None,
    export_name: str | None = None,
    export_dir: Path | None = None,
) -> dict[str, Any]:
    """Copy files matching the current matrix to the export folder.

    Returns a dict with the output path, copied count, skipped count, and
    any missing files.
    """
    if "path" not in matrix.columns:
        raise ValueError("Export requires a 'path' column in the matrix")

    name = export_name or _default_export_name()
    destination = export_dir or (DEFAULT_EXPORTS_DIR / name)
    _ensure_export_dir(destination)

    copied = 0
    skipped = 0
    missing: list[str] = []

    for stored_path in matrix["path"]:
        source = resolve_midi_path(stored_path, midi_root)
        if source is None or not source.exists():
            missing.append(str(stored_path))
            skipped += 1
            continue
        target = destination / Path(stored_path).name
        shutil.copy2(source, target)
        copied += 1

    return {
        "destination": destination,
        "copied": copied,
        "skipped": skipped,
        "missing": missing,
    }


__all__ = ["export_filtered_files", "DEFAULT_EXPORTS_DIR"]
