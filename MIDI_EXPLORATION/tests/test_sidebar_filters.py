import pandas as pd
import pytest

from midi_exploration.components.sidebar_filters.apply import _apply_filters
from midi_exploration.components.sidebar_filters.helpers import (
    _all_concepts,
    _apply_numeric_filter,
    _apply_tag_filter,
    _build_concept_categories,
    _range_is_active,
    _stat_cols,
)
from midi_exploration.pages.overview import _numeric_columns, _resolve_focus_column


TAXONOMY = {
    "duration": {
        "llm": {
            "category": "rhythm",
            "subcategory": "duration",
            "instrument_family": ["pitched"],
            "levels": [[0, "short", 1]],
        },
    },
    "density": {
        "llm": {
            "category": "rhythm",
            "subcategory": "rhythmic density",
            "instrument_family": ["pitched"],
            "levels": [[1, "low", 2], [2, "high", 3]],
        },
    },
    "placeholder_note_count": {
        "llm": {
            "category": "placeholder",
            "subcategory": "metadata",
            "instrument_family": ["pitched"],
        },
    },
    "novel_concept": {
        "llm": {"instrument_family": ["pitched"]},
    },
    "drum_spacing": {
        "llm": {
            "category": "drums",
            "subcategory": "spacing",
            "instrument_family": ["drums"],
        },
    },
}


def test_build_concept_categories():
    categories = _build_concept_categories(TAXONOMY)
    assert categories["duration"] == ["duration"]
    assert categories["rhythmic density"] == ["density"]
    assert categories["metadata"] == ["placeholder_note_count"]
    assert categories["unsorted"] == ["novel_concept"]
    # Drum-only concepts are excluded from the pitched categories
    assert "drum_spacing" not in _all_concepts(categories)


def test_stat_cols():
    df = pd.DataFrame({"a_raw": [1], "b_tag": [1], "c_norm": [1], "d": [1]})
    cols = _stat_cols(df)
    assert sorted(cols) == ["a_raw", "b_tag", "c_norm"]


def test_apply_numeric_filter():
    df = pd.DataFrame({"density_raw": [0.0, 0.5, 1.0]})
    result = _apply_numeric_filter(df, "density_raw", (0.25, 0.75))
    assert result["density_raw"].tolist() == [0.5]


def test_apply_numeric_filter_missing_column():
    df = pd.DataFrame({"other": [1, 2, 3]})
    result = _apply_numeric_filter(df, "missing", (0, 1))
    pd.testing.assert_frame_equal(result, df)


def test_apply_tag_filter_include():
    df = pd.DataFrame({"density_tag": [1, 2, 1]})
    result = _apply_tag_filter(df, "density", ["low"], [], TAXONOMY)
    assert result["density_tag"].tolist() == [1, 1]


def test_apply_tag_filter_exclude():
    df = pd.DataFrame({"density_tag": [1, 2, 1]})
    result = _apply_tag_filter(df, "density", [], ["high"], TAXONOMY)
    assert result["density_tag"].tolist() == [1, 1]


def test_range_is_active():
    df = pd.DataFrame({"density_raw": [0.0, 0.5, 1.0]})
    assert _range_is_active((0.0, 1.0), df, "density_raw") is False
    assert _range_is_active((0.25, 1.0), df, "density_raw") is True
    assert _range_is_active((0.0, 0.75), df, "density_raw") is True


def test_apply_filters_by_family():
    matrix = pd.DataFrame({
        "family": ["drums", "drums", "pitched"],
        "duration_tag": [1, 1, 1],
    })
    state = {"family": "drums", "active_concepts": [], "concept_filters": {}}
    result = _apply_filters(matrix, TAXONOMY, state, _stat_cols(matrix))
    assert len(result) == 2
    assert (result["family"] == "drums").all()


def test_apply_filters_by_active_concept_tag():
    matrix = pd.DataFrame({
        "family": ["drums", "drums"],
        "path": ["a.mid", "b.mid"],
        "density_tag": [1, 2],
    })
    state = {
        "family": "All",
        "active_concepts": ["density"],
        "concept_filters": {
            "density": {"tag_include": ["low"]},
        },
    }
    result = _apply_filters(matrix, TAXONOMY, state, _stat_cols(matrix))
    assert len(result) == 1
    assert result.iloc[0]["path"] == "a.mid"


def test_resolve_focus_column_prefers_raw():
    matrix = pd.DataFrame({
        "density_raw": [0.1, 0.2],
        "density_norm": [0.2, 0.4],
        "density_tag": [1, 2],
    })
    active_cols = ["density_raw", "density_norm", "density_tag"]
    assert _resolve_focus_column(matrix, active_cols, "density") == "density_raw"


def test_resolve_focus_column_falls_back_to_numeric_norm():
    matrix = pd.DataFrame({
        "density_raw": ["a", "b"],
        "density_norm": [0.2, 0.4],
        "density_tag": [1, 2],
    })
    active_cols = ["density_raw", "density_norm", "density_tag"]
    assert _resolve_focus_column(matrix, active_cols, "density") == "density_norm"


def test_resolve_focus_column_falls_back_to_tag():
    matrix = pd.DataFrame({"density_tag": [1, 2]})
    active_cols = ["density_tag"]
    assert _resolve_focus_column(matrix, active_cols, "density") == "density_tag"


def test_resolve_focus_column_missing_concept():
    matrix = pd.DataFrame({"density_raw": [0.1, 0.2]})
    active_cols = ["density_raw"]
    assert _resolve_focus_column(matrix, active_cols, "duration") is None


def test_numeric_columns_only_active():
    matrix = pd.DataFrame({
        "duration_raw": [1.0, 2.0],
        "note_count_raw": [10, 20],
        "stat_count": [3, 3],
    })
    active_cols = ["duration_raw", "note_count_raw"]
    assert sorted(_numeric_columns(matrix, active_cols)) == ["duration_raw", "note_count_raw"]


def test_numeric_columns_includes_active_tag_and_raw():
    matrix = pd.DataFrame({
        "density_tag": [1, 2],
        "density_raw": [0.5, 0.7],
    })
    active_cols = ["density_tag", "density_raw"]
    assert sorted(_numeric_columns(matrix, active_cols)) == ["density_raw", "density_tag"]
