import json
import tempfile
from pathlib import Path

import pytest

from midi_exploration.presets import delete_preset, load_presets, save_preset
from midi_exploration.presets import _presets_path


def _temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


def _cleanup(db_path):
    db_path.unlink(missing_ok=True)
    _presets_path(db_path).unlink(missing_ok=True)


def test_presets_path_appends_suffix():
    db_path = _temp_db()
    try:
        expected = db_path.parent / (db_path.name + ".presets.json")
        assert _presets_path(db_path) == expected
    finally:
        _cleanup(db_path)


def test_load_presets_missing_file():
    db_path = _temp_db()
    try:
        _presets_path(db_path).unlink(missing_ok=True)
        assert load_presets(db_path) == {}
    finally:
        _cleanup(db_path)


def test_load_presets_invalid_json():
    db_path = _temp_db()
    try:
        _presets_path(db_path).write_text("not-json")
        assert load_presets(db_path) == {}
    finally:
        _cleanup(db_path)


def test_save_and_load_preset():
    db_path = _temp_db()
    try:
        state = {"family": "drums", "min_stats": 3}
        save_preset(db_path, "drums-only", state)
        presets = load_presets(db_path)
        assert presets == {"drums-only": state}
    finally:
        _cleanup(db_path)


def test_delete_preset():
    db_path = _temp_db()
    try:
        save_preset(db_path, "a", {"min_stats": 1})
        save_preset(db_path, "b", {"min_stats": 2})
        delete_preset(db_path, "a")
        presets = load_presets(db_path)
        assert "a" not in presets
        assert presets["b"] == {"min_stats": 2}
    finally:
        _cleanup(db_path)
