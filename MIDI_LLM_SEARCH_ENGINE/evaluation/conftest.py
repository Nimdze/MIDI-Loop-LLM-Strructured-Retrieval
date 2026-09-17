"""Shared fixtures for the evaluation suites."""
import pytest
from midi_llm_search_engine.index_loader import SearchIndex

from ._index_fixture import _build_index


@pytest.fixture
def index(tmp_path) -> SearchIndex:
    return _build_index(tmp_path)
