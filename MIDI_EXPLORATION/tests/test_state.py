import json

import pytest

from midi_exploration.state import load_state, save_state


def test_save_and_load_state(monkeypatch, tmp_path):
    monkeypatch.setattr("midi_exploration.state.WORKSPACE_DIR", tmp_path)

    save_state(
        project_db_path="db.db",
        project_midi_root="root",
        project_taxonomy_path="tax.json",
        label="MyLibrary",
    )

    settings_file = tmp_path / ".state" / "settings.json"
    assert settings_file.exists()
    assert json.loads(settings_file.read_text()) == {
        "project_db_path": "db.db",
        "project_midi_root": "root",
        "project_taxonomy_path": "tax.json",
        "label": "MyLibrary",
    }

    assert load_state() == {
        "project_db_path": "db.db",
        "project_midi_root": "root",
        "project_taxonomy_path": "tax.json",
        "label": "MyLibrary",
    }


def test_load_state_missing_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr("midi_exploration.state.WORKSPACE_DIR", tmp_path)
    assert load_state() == {}


def test_load_state_bad_json_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr("midi_exploration.state.WORKSPACE_DIR", tmp_path)
    state_dir = tmp_path / ".state"
    state_dir.mkdir(parents=True)
    (state_dir / "settings.json").write_text("not json")
    assert load_state() == {}


def test_save_state_without_label(monkeypatch, tmp_path):
    monkeypatch.setattr("midi_exploration.state.WORKSPACE_DIR", tmp_path)
    save_state(
        project_db_path="db.db",
        project_midi_root="root",
        project_taxonomy_path="tax.json",
    )
    assert load_state() == {
        "project_db_path": "db.db",
        "project_midi_root": "root",
        "project_taxonomy_path": "tax.json",
    }
