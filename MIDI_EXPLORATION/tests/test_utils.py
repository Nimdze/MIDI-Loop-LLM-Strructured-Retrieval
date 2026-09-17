from pathlib import Path
import tempfile

import pytest

from midi_exploration.utils import format_value, midi_download_link, resolve_midi_path


def test_format_value_rounds_floats():
    assert format_value(1.23456) == "1.235"


def test_format_value_handles_none():
    assert format_value(None) == ""


def test_format_value_handles_lists():
    assert format_value([1.0, 2.0]) == "1.000, 2.000"


def test_resolve_midi_path_uses_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "loops"
        root.mkdir()
        file = root / "x.mid"
        file.write_text("midi")
        assert resolve_midi_path("x.mid", root) == file


def test_resolve_midi_path_falls_back_to_absolute():
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp)/ "x.mid"
        file.write_text("midi")
        assert resolve_midi_path(str(file), None) == file


def test_midi_download_link_embeds_data():
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "x.mid"
        file.write_bytes(b"midi data")
        link = midi_download_link(file)
        assert file.name in link
        assert "data:audio/midi;base64" in link


def test_resolve_midi_path_returns_none_for_missing_relative_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert resolve_midi_path("missing.mid", root) is None
        assert resolve_midi_path("missing.mid", root / "nonexistent_root") is None
