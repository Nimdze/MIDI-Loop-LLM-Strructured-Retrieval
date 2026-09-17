"""Fixtures for the unit tests under tests/.

The shared in-memory SearchIndex (taxonomy + SQLite) used by test_search.py
lives in the evaluation package so the unit tests and the evaluation suites
share one source of truth.
"""
import pytest
from midi_llm_search_engine.index_loader import SearchIndex

from evaluation._index_fixture import _build_index


@pytest.fixture
def index(tmp_path) -> SearchIndex:
    return _build_index(tmp_path)
