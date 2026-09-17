"""Shared in-memory taxonomy + SQLite index used by the evaluation suites.

Builds pitched concepts (rhythmic_density, dynamics_avg_velocity), a drum-only
concept (snare_density), and paired grid concepts (attempt/success). Everything
is deterministic and LLM-free.
"""
import json
import sqlite3
from pathlib import Path

from midi_llm_search_engine.index_loader import SearchIndex

TAXONOMY = {
    "llm_categories": {
        "rhythm": {"description": "When and how often notes occur."},
        "dynamics": {"description": "Loudness."},
        "percussive": {"description": "Drum behavior."},
    },
    "rhythmic_density": {
        "base_weight": 1.0,
        "llm": {
            "category": "rhythm",
            "subcategory": "rhythmic density",
            "instrument_family": ["pitched"],
            "levels": [
                [0, "Frantic", 4],
                [1, "Busy", 3],
                [2, "Moderate", 2],
                [3, "Sparse", 1],
            ],
        },
    },
    "dynamics_avg_velocity": {
        "base_weight": 1.0,
        "llm": {
            "category": "dynamics",
            "subcategory": "average velocity",
            "instrument_family": ["pitched"],
            "levels": [
                [0, "Hard", 4],
                [1, "Balanced", 3],
                [2, "Light", 2],
                [3, "Whisper", 1],
            ],
        },
    },
    "snare_density": {
        "base_weight": 1.0,
        "llm": {
            "category": "percussive",
            "subcategory": "snare density",
            "instrument_family": ["drum"],
            "levels": [
                [0, "Dense", 4],
                [1, "Regular", 2],
                [2, "Sparse", 1],
            ],
        },
    },
    "grid_attempt_pct_even1": {
        "base_weight": 1.0,
        "llm": {
            "category": "rhythm",
            "subcategory": "grid",
            "instrument_family": ["pitched"],
            "pair_with": "grid_success_pct_even1",
            "pair_role": "attempt",
            "levels": [[0, "High Attempts", 4], [1, "Low Attempts", 2]],
        },
    },
    "grid_success_pct_even1": {
        "base_weight": 1.0,
        "llm": {
            "category": "rhythm",
            "subcategory": "grid",
            "instrument_family": ["pitched"],
            "pair_with": "grid_attempt_pct_even1",
            "pair_role": "success",
            "levels": [
                [0, "High Success", 4],
                [1, "Medium Success", 2],
                [2, "Low Success", 1],
            ],
        },
    },
}

# file_id -> (path, family, {concept: level})
FILES = [
    (1, "loop_frantic_bal.mid", "pitched",
     {"rhythmic_density": "Frantic", "dynamics_avg_velocity": "Balanced"}),
    (2, "loop_busy_hard.mid", "pitched",
     {"rhythmic_density": "Busy", "dynamics_avg_velocity": "Hard"}),
    (3, "loop_sparse_whisper.mid", "pitched",
     {"rhythmic_density": "Sparse", "dynamics_avg_velocity": "Whisper"}),
    (4, "loop_moderate_no_dyn.mid", "pitched",
     {"rhythmic_density": "Moderate"}),
    (5, "loop_dyn_only.mid", "pitched",
     {"dynamics_avg_velocity": "Light"}),
    (6, "loop_null_levels.mid", "pitched",
     {"rhythmic_density": None}),
    (7, "drum_dense_regular.mid", "drum",
     {"snare_density": "Dense"}),
    (8, "drum_sparse.mid", "drum",
     {"snare_density": "Sparse"}),
]


def _build_index(tmp_path: Path) -> SearchIndex:
    db_path = tmp_path / "analysis.db"
    taxonomy_path = tmp_path / "taxonomy.json"
    taxonomy_path.write_text(json.dumps(TAXONOMY))
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE files (id INTEGER PRIMARY KEY, path TEXT, family TEXT);
            CREATE TABLE tags (
                file_id INTEGER, concept_name TEXT, level_name TEXT,
                level_index INTEGER, level_weight INTEGER
            );
        """)
        for fid, path, family, tags in FILES:
            conn.execute(
                "INSERT INTO files (path, family) VALUES (?, ?)", (path, family)
            )
            for concept, level in tags.items():
                conn.execute(
                    "INSERT INTO tags (file_id, concept_name, level_name, level_index, level_weight) "
                    "VALUES (?, ?, ?, ?, 0)",
                    (fid, concept, level, 0),
                )
        # Paired grid tags on file 1, for pair/conjunction tests.
        conn.execute(
            "INSERT INTO tags (file_id, concept_name, level_name, level_index, level_weight) "
            "VALUES (1, 'grid_attempt_pct_even1', 'High Attempts', 0, 4)"
        )
        conn.execute(
            "INSERT INTO tags (file_id, concept_name, level_name, level_index, level_weight) "
            "VALUES (1, 'grid_success_pct_even1', 'Medium Success', 1, 2)"
        )
        conn.commit()
    return SearchIndex(db_path, taxonomy_path)
