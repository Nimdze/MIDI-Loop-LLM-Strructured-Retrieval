"""Tests for the end-to-end SearchEngine orchestration."""
import pytest
from midi_llm_search_engine.llm_client import LLMTranslator
from midi_llm_search_engine.models import QueryTranslation, Target
from midi_llm_search_engine.scorer import FileScorer
from midi_llm_search_engine.search import SearchEngine, SearchError


class _FakeTranslator:
    def __init__(self, targets):
        self._targets = targets

    def translate(self, query, instrument_family="pitched"):
        return (
            QueryTranslation(
                family_classification=instrument_family,
                targets=self._targets,
            ),
            None,
        )


class _FailingTranslator:
    def translate(self, query, instrument_family="pitched"):
        raise RuntimeError("boom")


def test_search_engine_wires_translator_to_scorer(index):
    targets = [Target(concept_name="rhythmic_density", level_name="Frantic", importance=5, fallback="nearest")]
    engine = SearchEngine(index, translator=_FakeTranslator(targets))
    response = engine.search("relentless and busy", instrument_family="pitched")
    assert response.query == "relentless and busy"
    assert response.targets == targets
    assert response.instrument_family == "pitched"
    assert response.results
    assert response.results[0].file_path == "loop_frantic_bal.mid"
    assert response.results[0].score == pytest.approx(1.0)


def test_search_engine_uses_provided_scorer(index):
    targets = [Target(concept_name="rhythmic_density", level_name="Frantic", importance=5, fallback="nearest")]
    scorer = FileScorer(index, use_base_weight=True)
    engine = SearchEngine(index, translator=_FakeTranslator(targets), scorer=scorer)
    response = engine.search("relentless", instrument_family="pitched")
    assert response.results[0].score == pytest.approx(1.0)


def test_search_engine_defaults_to_real_translator_type(index):
    engine = SearchEngine(index)
    assert isinstance(engine.translator, LLMTranslator)
    assert isinstance(engine.scorer, FileScorer)


def test_search_engine_wraps_translation_failure(index):
    engine = SearchEngine(index, translator=_FailingTranslator())
    with pytest.raises(SearchError) as exc_info:
        engine.search("anything")
    assert "Failed to translate query" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, RuntimeError)
