import numpy as np
import pandas as pd
import pytest
import streamlit as st

from midi_exploration.pages.correlations.categories import get_category, get_column_category
from midi_exploration.pages.correlations.engine import (
    apply_cross_category_mask,
    compute_correlation_matrices,
    detect_constant_columns,
    mask_diagonal,
    prepare_correlation_data,
    select_numeric_columns,
)
from midi_exploration.pages.correlations.heatmaps import _draw_heatmap
from midi_exploration.pages.correlations.utils import clamp


class TestUtils:
    def test_clamp_inside(self):
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_clamp_below(self):
        assert clamp(-3.0, 0.0, 10.0) == 0.0

    def test_clamp_above(self):
        assert clamp(15.0, 0.0, 10.0) == 10.0


class TestCategories:
    def test_get_category_rhythm_density(self):
        taxonomy = {"rhythmic_density_note_count": {"llm": {"category": "rhythm"}}}
        assert get_category("rhythmic_density_note_count", taxonomy) == "rhythm/rhythmic_density"

    def test_get_category_harmony_density(self):
        taxonomy = {"chord_density": {"llm": {"category": "harmony"}}}
        assert get_category("chord_density", taxonomy) == "harmony/density"

    def test_get_category_drum_stem(self):
        taxonomy = {"drum_kick_density": {"llm": {"category": "drums"}}}
        assert get_category("drum_kick_density", taxonomy) == "drums/drum_kick/density"

    def test_get_column_category_strips_suffix(self):
        taxonomy = {"rhythmic_density_note_count": {"llm": {"category": "rhythm"}}}
        assert (
            get_column_category("rhythmic_density_note_count_norm", taxonomy)
            == "rhythm/rhythmic_density"
        )

    def test_get_category_unknown_concept(self):
        taxonomy = {}
        assert get_category("missing_concept", taxonomy) == "unknown"

    def test_get_category_drum_without_subcategory(self):
        taxonomy = {"drum_kick_prevalence": {"llm": {"category": "drums"}}}
        assert get_category("drum_kick_prevalence", taxonomy) == "drums/drum_kick/prevalence"

    def test_get_category_metadata_without_subcategory(self):
        taxonomy = {"note_count": {"llm": {"category": "metadata"}}}
        assert get_category("note_count", taxonomy) == "metadata"


class TestEngine:
    def test_select_numeric_columns_keeps_norm_only(self):
        matrix = pd.DataFrame(
            {
                "a_norm": [1.0, 2.0, 3.0],
                "a_raw": [10.0, 20.0, 30.0],
                "a_tag": [0, 1, 0],
                "b_norm": ["x", "y", "z"],
                "c_norm": [3.0, 2.0, 1.0],
            }
        )
        selected, skipped = select_numeric_columns(
            matrix, ["a_norm", "a_raw", "a_tag", "b_norm", "c_norm"], {}
        )
        assert selected == ["a_norm", "c_norm"]
        assert "a_raw: not _norm" in skipped
        assert "a_tag: not _norm" in skipped
        assert "b_norm: non-numeric" in skipped

    def test_detect_constant_columns(self):
        matrix = pd.DataFrame(
            {
                "a_norm": [1.0, 1.0, 1.0],
                "b_norm": [1.0, 2.0, 3.0],
                "c_norm": [np.nan, np.nan, np.nan],
            }
        )
        constant = detect_constant_columns(matrix, ["a_norm", "b_norm", "c_norm"])
        assert "a_norm" in constant
        assert "b_norm" not in constant
        assert "c_norm" in constant

    def test_prepare_correlation_data(self):
        matrix = pd.DataFrame(
            {
                "a_norm": [1.0, 2.0, 3.0],
                "b_norm": [3.0, 2.0, 1.0],
                "c_norm": [1.0, 1.0, 1.0],
                "d_raw": [10.0, 20.0, 30.0],
            }
        )
        taxonomy = {
            "a": {"llm": {"category": "rhythm"}},
            "b": {"llm": {"category": "rhythm"}},
            "c": {"llm": {"category": "harmony"}},
        }
        analysis_df, feature_cols, skipped, constant = prepare_correlation_data(
            matrix, ["a_norm", "b_norm", "c_norm", "d_raw"], taxonomy
        )
        assert feature_cols == ["a_norm", "b_norm"]
        assert "c_norm" in constant
        assert "d_raw: not _norm" in skipped
        assert list(analysis_df.columns) == ["a_norm", "b_norm"]

    def test_compute_correlation_matrices(self):
        df = pd.DataFrame(
            {
                "a_norm": [1.0, 2.0, 3.0, 4.0, 5.0],
                "b_norm": [5.0, 4.0, 3.0, 2.0, 1.0],
            }
        )
        pearson, spearman, diff = compute_correlation_matrices(df)
        assert pearson.shape == (2, 2)
        assert spearman.shape == (2, 2)
        assert diff.shape == (2, 2)
        assert np.isclose(pearson.loc["a_norm", "b_norm"], -1.0, atol=1e-6)
        assert np.isclose(spearman.loc["a_norm", "b_norm"], -1.0, atol=1e-6)
        assert np.all(diff.values >= 0)

    def test_mask_diagonal(self):
        matrix = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]], index=["a", "b"], columns=["a", "b"]
        )
        masked = mask_diagonal(matrix)
        assert np.isnan(masked.loc["a", "a"])
        assert np.isnan(masked.loc["b", "b"])
        assert masked.loc["a", "b"] == 0.5

    def test_apply_cross_category_mask(self):
        matrix = pd.DataFrame(
            [[1.0, 0.5, 0.2], [0.5, 1.0, 0.3], [0.2, 0.3, 1.0]],
            index=["a_norm", "b_norm", "c_norm"],
            columns=["a_norm", "b_norm", "c_norm"],
        )
        taxonomy = {
            "a": {"llm": {"category": "rhythm"}},
            "b": {"llm": {"category": "rhythm"}},
            "c": {"llm": {"category": "harmony"}},
        }
        masked = apply_cross_category_mask(matrix, taxonomy)
        assert np.isnan(masked.loc["a_norm", "b_norm"])
        assert np.isnan(masked.loc["b_norm", "a_norm"])
        assert masked.loc["a_norm", "c_norm"] == 0.2
        assert masked.loc["c_norm", "a_norm"] == 0.2


class TestHeatmapsDraw:
    def test_draw_heatmap_empty_range(self, monkeypatch):
        calls = []

        def mock_info(msg):
            calls.append(msg)

        monkeypatch.setattr(st, "info", mock_info)

        matrix = pd.DataFrame(
            [[1.0, 0.1], [0.1, 1.0]],
            index=["a_norm", "b_norm"],
            columns=["a_norm", "b_norm"],
        )
        temp = mask_diagonal(matrix)
        taxonomy = {"a": {"llm": {"category": "rhythm"}}, "b": {"llm": {"category": "harmony"}}}
        _draw_heatmap(matrix, temp, (0.9, 1.0), "Test", taxonomy, False)
        assert len(calls) == 1
        assert "No features in focus range" in calls[0]
