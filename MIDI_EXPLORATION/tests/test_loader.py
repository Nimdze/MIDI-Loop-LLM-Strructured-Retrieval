import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from midi_exploration.loader import AnalysisLoader


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
            "INSERT INTO files (id, path, family, duration, note_count) VALUES (1, 'a/b.mid', 'pitched', 10.0, 5)"
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


@pytest.fixture
def taxonomy():
    return {
        "duration": {
            "llm": {"category": "metadata", "levels": [[0, "short", 1]]},
        },
        "density": {
            "llm": {"category": "rhythm", "levels": [[1, "low", 2], [2, "high", 3]]},
        },
    }


@pytest.fixture
def loader(tmp_path, taxonomy):
    db_path = tmp_path / "analysis.db"
    _create_db(db_path)
    with AnalysisLoader(db_path) as loader:
        yield loader


def test_load_tag_categories(loader, taxonomy):
    categories = loader.load_tag_categories(taxonomy)
    assert categories["metadata"] == ["duration"]
    assert categories["rhythm"] == ["density"]


def test_load_audit_stats(loader, taxonomy):
    matrix = loader.load_feature_matrix(taxonomy)
    stats = loader.load_audit_stats(taxonomy=taxonomy, matrix=matrix)
    assert stats["total"] == 1
    assert stats["distributions"]["global"] == [3]
    assert stats["distributions"]["metadata"] == [1]
    assert stats["distributions"]["rhythm"] == [2]


def test_load_file_payload(loader, taxonomy):
    payload = loader.load_file_payload(1, taxonomy)
    assert payload["file_id"] == 1
    assert payload["concepts"]["metadata"]["duration"]["tag"] == "short"
    assert pytest.approx(payload["concepts"]["rhythm"]["density"]["raw"]) == 0.5
    assert pytest.approx(payload["concepts"]["rhythm"]["density"]["norm"]) == 0.2


def test_feature_matrix_has_file_id_column(loader, taxonomy):
    matrix = loader.load_feature_matrix(taxonomy)
    assert "file_id" in matrix.columns
    assert "id" not in matrix.columns


def test_load_feature_matrix_empty_db(tmp_path):
    db_path = tmp_path / "empty.db"
    _create_db(db_path, with_data=False)
    with AnalysisLoader(db_path) as loader:
        matrix = loader.load_feature_matrix({})
    assert matrix.empty
    assert "file_id" in matrix.columns


def test_load_feature_matrix_corrupted_taxonomy(loader):
    corrupted_taxonomy = {
        "duration": {"llm": {"category": "metadata", "levels": "not-a-list"}},
        "density": {"llm": {"category": "rhythm", "levels": [[1, "low", 2], [2, "high", 3]]}},
    }
    matrix = loader.load_feature_matrix(corrupted_taxonomy)
    assert "duration_tag" in matrix.columns
    assert matrix["duration_tag"].isna().all()
    assert "density_raw" in matrix.columns
    assert matrix["density_raw"].notna().all()
