import io
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pretty_midi
import pytest

from midi_exploration import orchestrator
from midi_exploration.orchestrator import run_import_pipeline


def _build_zip(entries: dict[str, bytes]) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)
    buffer.seek(0)
    return buffer


def _midi_bytes(note_count: int = 1) -> bytes:
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    for i in range(note_count):
        inst.notes.append(
            pretty_midi.Note(
                velocity=100, pitch=60, start=i * 0.1, end=i * 0.1 + 0.05
            )
        )
    midi.instruments.append(inst)
    buffer = io.BytesIO()
    midi.write(buffer)
    return buffer.getvalue()


def _make_zip_with_midi(note_count: int = 1) -> io.BytesIO:
    return _build_zip({"file1.mid": _midi_bytes(note_count)})


def test_run_import_pipeline_creates_db_and_taxonomy():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "workspace"
        with patch.object(orchestrator, "WORKSPACE_DIR", workspace):
            result = run_import_pipeline(
                uploaded_file=_make_zip_with_midi(note_count=5),
                label="test",
                mode="Create / Replace",
                normalize_tempo=False,
                target_bpm=120.0,
                slice_bars=None,
                no_split=False,
            )

            assert result["db_path"].exists()
            assert result["taxonomy_path"].exists()
            assert result["midi_root"].exists()
            assert result["analyze_result"]["processed"] > 0


def test_run_import_pipeline_replace_wipes_existing_project():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "workspace"
        with patch.object(orchestrator, "WORKSPACE_DIR", workspace):
            first = run_import_pipeline(
                uploaded_file=_make_zip_with_midi(1),
                label="replace",
                mode="Create / Replace",
                normalize_tempo=False,
                target_bpm=120.0,
                slice_bars=None,
                no_split=False,
            )
            first_processed = first["analyze_result"]["processed"]
            assert first_processed > 0

            second = run_import_pipeline(
                uploaded_file=_make_zip_with_midi(5),
                label="replace",
                mode="Create / Replace",
                normalize_tempo=False,
                target_bpm=120.0,
                slice_bars=None,
                no_split=False,
            )
            assert second["analyze_result"]["processed"] > 0


def test_run_import_pipeline_appends_to_existing_project():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "workspace"
        with patch.object(orchestrator, "WORKSPACE_DIR", workspace):
            first = run_import_pipeline(
                uploaded_file=_make_zip_with_midi(1),
                label="append",
                mode="Create / Replace",
                normalize_tempo=False,
                target_bpm=120.0,
                slice_bars=None,
                no_split=False,
            )
            first_processed = first["analyze_result"]["processed"]
            assert first_processed > 0

            second = run_import_pipeline(
                uploaded_file=_build_zip({"sub/file2.mid": _midi_bytes(1)}),
                label="append",
                mode="Append",
                normalize_tempo=False,
                target_bpm=120.0,
                slice_bars=None,
                no_split=False,
            )
            assert second["analyze_result"]["processed"] > 0
            assert second["analyze_result"]["skipped"] == first_processed
