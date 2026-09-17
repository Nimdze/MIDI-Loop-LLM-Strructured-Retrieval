import json
import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from midi_exploration import orchestrator, state


def _create_db(db_path: Path, with_data: bool = True) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            family TEXT,
            duration REAL,
            note_count INTEGER,
            metadata TEXT,
            analyzed_at TEXT
        );
        CREATE TABLE tags (
            file_id INTEGER,
            concept_name TEXT,
            level_name TEXT,
            level_index INTEGER,
            level_weight INTEGER
        );
        CREATE TABLE raw_features (
            file_id INTEGER,
            concept_name TEXT,
            value TEXT
        );
        CREATE TABLE normalized_features (
            file_id INTEGER,
            concept_name TEXT,
            value TEXT
        );
        """
    )
    if with_data:
        conn.execute(
            "INSERT INTO files (id, path, family, duration, note_count) VALUES (1, 'a.mid', 'pitched', 10.0, 5)"
        )
        conn.execute(
            "INSERT INTO tags (file_id, concept_name, level_name, level_index, level_weight) VALUES (1, 'duration', 'short', 0, 1)"
        )
        conn.execute(
            "INSERT INTO raw_features (file_id, concept_name, value) VALUES (1, 'density', '0.5')"
        )
        conn.execute(
            "INSERT INTO normalized_features (file_id, concept_name, value) VALUES (1, 'density', '0.2')"
        )
    conn.commit()
    conn.close()


def _create_taxonomy(taxonomy_path: Path) -> None:
    taxonomy = {
        "duration": {
            "category": "rhythm",
            "instrument_family": ["pitched"],
            "levels": [[0, "short", 1]],
            "llm": {"subcategory": "duration"},
        },
        "density": {
            "category": "rhythm",
            "instrument_family": ["pitched"],
            "levels": [[1, "low", 2], [2, "high", 3]],
            "llm": {"subcategory": "rhythmic density"},
        },
        "subcategories": {
            "duration": {"description": "Duration measures how long notes are held."},
            "rhythmic density": {"description": "Average note density over time."},
        },
    }
    taxonomy_path.write_text(json.dumps(taxonomy))


def _make_app_test(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "analysis.db"
    taxonomy_path = tmp_path / "taxonomy.json"
    root = tmp_path / "root"
    root.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _create_db(db_path)
    _create_taxonomy(taxonomy_path)
    (root / "a.mid").write_bytes(b"0")

    monkeypatch.setenv("MIDI_RETRIEVE_DB", str(db_path))
    monkeypatch.setenv("MIDI_RETRIEVE_ROOT", str(root))
    monkeypatch.setenv("MIDI_RETRIEVE_TAXONOMY", str(taxonomy_path))
    monkeypatch.setattr(orchestrator, "WORKSPACE_DIR", workspace)
    monkeypatch.setattr(state, "WORKSPACE_DIR", workspace)

    app_path = Path(__file__).parent.parent / "src" / "midi_exploration" / "app.py"
    at = AppTest.from_file(str(app_path)).run()
    return at, db_path, root


def test_app_renders_without_exception(tmp_path, monkeypatch):
    at, _db_path, _root = _make_app_test(tmp_path, monkeypatch)
    assert len(at.exception) == 0


def test_sidebar_has_focus_and_filters(tmp_path, monkeypatch):
    at, _db_path, _root = _make_app_test(tmp_path, monkeypatch)
    assert len(at.exception) == 0
    sidebar = at.sidebar
    labels = [e.label for e in sidebar.expander]
    assert "duration" in labels
    assert "rhythmic density" in labels


def test_input_tab_shows_without_database(tmp_path, monkeypatch):
    monkeypatch.setenv("MIDI_RETRIEVE_DB", str(tmp_path / "__not_a_real_db__.db"))
    monkeypatch.setenv("MIDI_RETRIEVE_ROOT", str(tmp_path / "__not_a_real_root__"))
    monkeypatch.setenv(
        "MIDI_RETRIEVE_TAXONOMY", str(tmp_path / "__not_a_real_taxonomy__.json")
    )

    app_path = Path(__file__).parent.parent / "src" / "midi_exploration" / "app.py"
    at = AppTest.from_file(str(app_path)).run()
    assert len(at.exception) == 0
    assert "Input" in [t.label for t in at.tabs]
    assert any(b.label == "Import and analyze" for b in at.button)


def test_app_renders_with_empty_database(tmp_path, monkeypatch):
    db_path = tmp_path / "empty.db"
    taxonomy_path = tmp_path / "taxonomy.json"
    root = tmp_path / "root"
    root.mkdir()

    _create_db(db_path, with_data=False)
    _create_taxonomy(taxonomy_path)

    monkeypatch.setenv("MIDI_RETRIEVE_DB", str(db_path))
    monkeypatch.setenv("MIDI_RETRIEVE_ROOT", str(root))
    monkeypatch.setenv("MIDI_RETRIEVE_TAXONOMY", str(taxonomy_path))

    app_path = Path(__file__).parent.parent / "src" / "midi_exploration" / "app.py"
    at = AppTest.from_file(str(app_path)).run()
    assert len(at.exception) == 0
    assert "Input" in [t.label for t in at.tabs]


def test_app_renders_with_corrupted_taxonomy(tmp_path, monkeypatch):
    db_path = tmp_path / "analysis.db"
    taxonomy_path = tmp_path / "taxonomy.json"
    root = tmp_path / "root"
    root.mkdir()

    _create_db(db_path)
    taxonomy_path.write_text("not a valid json object")

    monkeypatch.setenv("MIDI_RETRIEVE_DB", str(db_path))
    monkeypatch.setenv("MIDI_RETRIEVE_ROOT", str(root))
    monkeypatch.setenv("MIDI_RETRIEVE_TAXONOMY", str(taxonomy_path))

    app_path = Path(__file__).parent.parent / "src" / "midi_exploration" / "app.py"
    at = AppTest.from_file(str(app_path)).run()
    assert len(at.exception) == 0
    assert "Input" in [t.label for t in at.tabs]
