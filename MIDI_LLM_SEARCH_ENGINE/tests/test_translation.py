"""Smoke tests for the LLM translation layer."""
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from midi_llm_search_engine.index_loader import SearchIndex
from midi_llm_search_engine.prompt_builder import SystemPromptBuilder
from midi_llm_search_engine.models import Target


def _make_analyzer_outputs(tmp_path: Path):
    db_path = tmp_path / "analysis.db"
    taxonomy_path = tmp_path / "taxonomy.json"

    taxonomy = {
        "llm_categories": {
            "rhythm": {
                "description": "When and how often notes occur.",
                "interpretation": "Queries about speed, busyness, or rhythm belong here.",
                "examples": ["busy", "sparse", "fast", "slow"],
            }
        },
        "rhythmic_density": {
            "extractor": "rhythmic_density",
            "base_weight": 1.0,
            "llm": {
                "name": "rhythmic_density",
                "category": "rhythm",
                "scope": "summary",
                "instrument_family": ["pitched"],
                "levels": [
                    [10, "Frantic", 6],
                    [11, "Busy", 5],
                    [12, "Moderately (not too) Busy", 4],
                    [13, "Moderately (not too) Sparse", 3],
                    [14, "Sparse", 2],
                    [15, "Minimalist/Drone-like", 1],
                ],
                "description": "Average number of note events per beat.",
                "interpretation": "Use this for queries about speed, busyness, or density.",
                "subcategory": "rhythmic density",
                "examples": ["busy", "sparse", "fast"],
                "level_descriptions": {
                    "Frantic": "Extremely busy, >= 4.0 events per beat.",
                    "Busy": "Active rhythm, >= 2.0 events per beat.",
                },
            },
        },
    }
    taxonomy_path.write_text(json.dumps(taxonomy))

    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE files (id INTEGER PRIMARY KEY, path TEXT, family TEXT);
            CREATE TABLE tags (file_id INTEGER, concept_name TEXT, level_name TEXT, level_index INTEGER, level_weight INTEGER);
        """)
        conn.execute("INSERT INTO files (path, family) VALUES ('loop_a.mid', 'pitched')")
        conn.execute("INSERT INTO tags (file_id, concept_name, level_name, level_index, level_weight) VALUES (1, 'rhythmic_density', 'Busy', 11, 5)")
        conn.commit()

    return db_path, taxonomy_path


def test_index_loader_builds_inverted_index(tmp_path):
    db_path, taxonomy_path = _make_analyzer_outputs(tmp_path)
    index = SearchIndex(db_path, taxonomy_path)
    assert index.level_names("rhythmic_density") == [
        "Frantic", "Busy", "Moderately (not too) Busy",
        "Moderately (not too) Sparse", "Sparse", "Minimalist/Drone-like",
    ]
    assert index.files_for_tag("rhythmic_density", "Busy") == {1}


def test_prompt_builder_includes_concept(tmp_path):
    db_path, taxonomy_path = _make_analyzer_outputs(tmp_path)
    index = SearchIndex(db_path, taxonomy_path)
    prompt = SystemPromptBuilder(index).build()
    assert "rhythmic_density" in prompt
    assert "Average number of note events per beat" in prompt
    assert "### rhythmic density" in prompt


def test_prompt_builder_single_subcategory_skips_category_docs(tmp_path):
    """A category with exactly one subcategory skips its own prose (avoids duplication)."""
    db_path, taxonomy_path = _make_analyzer_outputs(tmp_path)
    index = SearchIndex(db_path, taxonomy_path)
    prompt = SystemPromptBuilder(index).build()
    # Category header still present, but its description/interpretation is skipped.
    assert "[RHYTHM]" in prompt
    assert "When and how often notes occur" not in prompt
    # The single subcategory still carries the content.
    assert "### rhythmic density" in prompt


def test_prompt_builder_family_order(tmp_path):
    """build(first_family=...) reorders sections."""
    db_path, taxonomy_path = _make_analyzer_outputs(tmp_path)
    index = SearchIndex(db_path, taxonomy_path)
    prompt_drums = SystemPromptBuilder(index).build(first_family="drums")
    prompt_pitched = SystemPromptBuilder(index).build(first_family="pitched")
    # Both should contain the concept (only pitched in fixture)
    assert "rhythmic_density" in prompt_drums
    assert "rhythmic_density" in prompt_pitched


def test_target_model():
    t = Target(concept_name="rhythmic_density", level_name="Busy", importance=3, fallback="nearest")
    assert t.concept_name == "rhythmic_density"
    assert t.level_name == "Busy"
    assert t.importance == 3
    assert t.fallback == "nearest"
