import pandas as pd
import pytest
import streamlit as st

from midi_exploration.components.filters import apply_filters, maybe_show_cluster_filter


def test_apply_filters_by_family():
    df = pd.DataFrame(
        {
            "family": ["drums", "drums", "pitched"],
            "path": ["a.mid", "b.mid", "c.mid"],
            "duration": [1.0, 2.0, 3.0],
        }
    )
    result = apply_filters(df, "drums", 0, ["duration"])
    assert len(result) == 2
    assert "c.mid" not in result["path"].values
    assert "a.mid" in result["path"].values


def test_apply_filters_by_min_stats():
    df = pd.DataFrame(
        {
            "family": ["drums", "drums"],
            "path": ["a.mid", "b.mid"],
            "duration": [1.0, None],
            "note_count": [5, 10],
        }
    )
    result = apply_filters(df, "All", 1, ["duration"])
    assert len(result) == 1
    assert result.iloc[0]["path"] == "a.mid"


def test_maybe_show_cluster_filter_no_filter(monkeypatch):
    monkeypatch.setattr(st, "session_state", {})
    df = pd.DataFrame({"path": ["a.mid", "b.mid"]})
    result = maybe_show_cluster_filter(df)
    pd.testing.assert_frame_equal(result, df)


def test_maybe_show_cluster_filter_active(monkeypatch):
    session_state = {"active_cluster_filter": ["a.mid"]}
    monkeypatch.setattr(st, "session_state", session_state)
    monkeypatch.setattr(st, "warning", lambda msg: None)
    monkeypatch.setattr(st, "button", lambda *args, **kwargs: False)
    df = pd.DataFrame({"path": ["a.mid", "b.mid"]})
    result = maybe_show_cluster_filter(df)
    assert result["path"].tolist() == ["a.mid"]
    assert "active_cluster_filter" in session_state


def test_maybe_show_cluster_filter_clears_on_button(monkeypatch):
    session_state = {"active_cluster_filter": ["a.mid"]}
    monkeypatch.setattr(st, "session_state", session_state)
    monkeypatch.setattr(st, "warning", lambda msg: None)
    monkeypatch.setattr(st, "button", lambda *args, **kwargs: True)
    monkeypatch.setattr(st, "rerun", lambda: None)
    df = pd.DataFrame({"path": ["a.mid", "b.mid"]})
    maybe_show_cluster_filter(df)
    assert "active_cluster_filter" not in session_state
