"""Workspace orchestrator for the Input / Import tab."""

import os
import time
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

WORKSPACE_DIR = Path(
    os.environ.get(
        "MIDI_EXPLORATION_WORKSPACE",
        str(Path.home() / "midi_exploration" / "workspace"),
    )
)


def _sanitize_label(label: str) -> str:
    """Turn a free-form label into a filesystem-safe directory name."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in label.strip()).strip("_")


def _project_paths(label: str) -> dict[str, Path]:
    base = WORKSPACE_DIR / _sanitize_label(label)
    return {k: base / k for k in ("raw", "clean", "output")}


def _ensure_dirs(paths: dict[str, Path]) -> None:
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)


def _extract_zip(uploaded_file: Any, raw_dir: Path) -> int:
    """Extract a Streamlit UploadedFile to the raw directory."""
    raw_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(uploaded_file) as z:
        z.extractall(raw_dir)
    return len(list(raw_dir.rglob("*")))


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


def _copytree(src: Path, dst: Path) -> None:
    import shutil

    shutil.copytree(src, dst)


def _unique_backup_path(final_base: Path) -> Path:
    """Return a non-conflicting backup path that cannot match a user label."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    candidate = final_base.with_name(f"{final_base.name}.backup_{timestamp}")
    counter = 1
    while candidate.exists():
        candidate = final_base.with_name(f"{final_base.name}.backup_{timestamp}_{counter}")
        counter += 1
    return candidate


def _noop(_message: str) -> None:
    pass


def run_import_pipeline(
    uploaded_file: Any,
    label: str,
    mode: str,
    normalize_tempo: bool,
    target_bpm: float,
    slice_bars: int | None,
    no_split: bool,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Extract, preprocess, and analyze a zip library in one go.

    Create / Replace mode extracts into a temporary staging directory first and
    swaps it into place only when all steps succeed, so a failed import does not
    leave the workspace empty.

    Returns a dict with the project paths, processing stats, and analyzer stats.
    """
    notify = progress or _noop

    try:
        from midi_analyzer_tagger.cli import analyze_folder

        from midi_preprocessor import process_folder
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "The preprocessor and/or analyzer packages are not installed in the Python "
            "environment running this app. Install them with:\n"
            "  cd MIDI_RETRIEVE/MIDI_EXPLORATION\n"
            "  .venv/bin/python -m pip install -e ../MIDI_PREPROCESSOR\n"
            "  .venv/bin/python -m pip install -e ../MIDI_ANALYZER_TAGGER"
        ) from e

    if mode not in ("Create / Replace", "Append"):
        raise ValueError(f"Unsupported import mode: {mode!r}")

    paths = _project_paths(label)
    is_create_replace = mode == "Create / Replace"

    if is_create_replace:
        staging = paths["raw"].parent.with_name(paths["raw"].parent.name + "_staging")
        _rmtree(staging)
        working_paths = _project_paths(staging.name)
    else:
        working_paths = paths

    backup_path: Path | None = None
    result: dict[str, Any] | None = None

    try:
        _ensure_dirs(working_paths)

        notify("Extracting ZIP...")
        _extract_zip(uploaded_file, working_paths["raw"])

        notify("Preprocessing MIDI files...")
        preprocess_result = process_folder(
            working_paths["raw"],
            working_paths["clean"],
            target_bpm=target_bpm if normalize_tempo else None,
            slice_bars=slice_bars,
            no_split=no_split,
            progress=progress,
        )

        notify("Analyzing features...")
        analyze_result = analyze_folder(
            working_paths["clean"],
            working_paths["output"],
            force=is_create_replace,
        )

        if is_create_replace:
            final_base = paths["raw"].parent
            backup_path = _unique_backup_path(final_base)
            if final_base.exists():
                final_base.rename(backup_path)
            working_paths["raw"].parent.rename(final_base)

        result = {
            "label": label,
            "paths": paths,
            "db_path": paths["output"] / "analysis.db",
            "taxonomy_path": paths["output"] / "taxonomy.json",
            "midi_root": paths["clean"],
            "preprocess_result": preprocess_result,
            "analyze_result": analyze_result,
        }
    except Exception:
        if is_create_replace:
            if backup_path is not None and backup_path.exists():
                # The swap started but did not finish; restore the previous project.
                final_base = paths["raw"].parent
                _rmtree(final_base)
                backup_path.rename(final_base)
            else:
                # No swap yet; remove the staging directory.
                _rmtree(working_paths["raw"].parent)
        raise

    if backup_path is not None and backup_path.exists():
        # Successful swap completed; remove the temporary backup.
        _rmtree(backup_path)

    return result


def list_libraries() -> list[str]:
    """Return labels of workspace libraries that have a completed analysis (DB + taxonomy)."""
    labels = []
    if WORKSPACE_DIR.exists():
        for child in sorted(WORKSPACE_DIR.iterdir()):
            if child.is_dir() and (child / "output" / "analysis.db").exists():
                labels.append(child.name)
    return labels


def library_paths(label: str) -> dict[str, Path] | None:
    """Resolve a workspace library's db / taxonomy / midi-root paths, or None if incomplete."""
    base = WORKSPACE_DIR / _sanitize_label(label)
    db = base / "output" / "analysis.db"
    tax = base / "output" / "taxonomy.json"
    if not db.exists() or not tax.exists():
        return None
    return {
        "db_path": db,
        "taxonomy_path": tax,
        "midi_root": base / "clean",
    }


def run_folder_import(
    folder_path: str | Path,
    label: str,
    normalize_tempo: bool = True,
    target_bpm: float = 120.0,
    slice_bars: int | None = None,
    no_split: bool = False,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Preprocess + analyze an existing MIDI folder into a workspace library.

    Points the pipeline at ``folder_path`` (a directory of MIDI files), cleans/
    analyzes it, and stores everything under ``WORKSPACE_DIR/<label>/`` so it can
    be auto-routed by the app. Returns the project paths and processing stats.
    """
    notify = progress or _noop

    from midi_analyzer_tagger.cli import analyze_folder
    from midi_preprocessor import process_folder

    src = Path(folder_path)
    if not src.is_dir():
        raise FileNotFoundError(f"Folder not found: {src}")

    base = WORKSPACE_DIR / _sanitize_label(label)
    backup_path: Path | None = None

    try:
        # Create / Replace: move any previous project aside, restore on failure.
        if base.exists():
            backup_path = _unique_backup_path(base)
            base.rename(backup_path)
        clean_dir = base / "clean"
        output_dir = base / "output"
        clean_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        notify("Preprocessing MIDI files...")
        preprocess_result = process_folder(
            src,
            clean_dir,
            target_bpm=target_bpm if normalize_tempo else None,
            slice_bars=slice_bars,
            no_split=no_split,
            progress=progress,
        )

        notify("Analyzing features...")
        analyze_result = analyze_folder(clean_dir, output_dir, force=True)

        result = {
            "label": label,
            "paths": {"clean": clean_dir, "output": output_dir},
            "db_path": output_dir / "analysis.db",
            "taxonomy_path": output_dir / "taxonomy.json",
            "midi_root": clean_dir,
            "preprocess_result": preprocess_result,
            "analyze_result": analyze_result,
        }
    except Exception:
        if backup_path is not None and backup_path.exists():
            _rmtree(base)
            backup_path.rename(base)
        raise

    if backup_path is not None and backup_path.exists():
        _rmtree(backup_path)

    return result


def ensure_default_libraries(
    progress: Callable[[str], None] | None = None,
) -> list[str]:
    """On app startup, make sure every ZIP in ``MIDI_RETRIEVE/default_dataset`` is
    processed into a ready-to-explore workspace library. Already-processed
    libraries (those with ``output/analysis.db``) are skipped, so reloads are fast.
    Returns the labels that were (re)processed.
    """
    default_dir = Path(__file__).resolve().parents[3] / "default_dataset"
    if not default_dir.is_dir():
        return []
    processed: list[str] = []
    for zip_path in sorted(default_dir.glob("*.zip")):
        label = zip_path.stem
        if library_paths(label) is not None:
            continue  # already ready
        if progress:
            progress(f"Preparing default dataset '{label}' from {zip_path.name}...")
        with open(zip_path, "rb") as f:
            run_import_pipeline(
                uploaded_file=f,
                label=label,
                mode="Create / Replace",
                normalize_tempo=True,
                target_bpm=120.0,
                slice_bars=None,
                no_split=False,
                progress=progress,
            )
        processed.append(label)
    return processed


__all__ = ["run_import_pipeline", "run_folder_import", "list_libraries",
           "library_paths", "ensure_default_libraries", "WORKSPACE_DIR", "_sanitize_label"]
