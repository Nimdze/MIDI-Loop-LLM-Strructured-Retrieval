"""Tests for the translator's paired-concept handling (grid attempt/success)."""
import types

from midi_llm_search_engine.llm_client import LLMTranslator
from midi_llm_search_engine.models import Target


def test_missing_pairs_detects_grid_partner(index):
    tr = LLMTranslator(index, api_key="test")
    attempt = Target(concept_name="grid_attempt_pct_even1", level_name="High Attempts", importance=4)
    assert tr._missing_pairs([attempt]) == [("grid_attempt_pct_even1", "grid_success_pct_even1")]
    both = [attempt, Target(concept_name="grid_success_pct_even1", level_name="High Success", importance=4)]
    assert tr._missing_pairs(both) == []


def test_translate_returns_single_member_when_pair_ignored(index, monkeypatch):
    """If the model never supplies the pair partner, return the single member
    rather than fabricating a level for the missing partner."""
    tr = LLMTranslator(index, api_key="test")
    content = ('{"family_classification": "pitched", "targets": ['
               '{"concept_name": "grid_attempt_pct_even1", "level_name": "High Attempts", "importance": 4}]}')

    def fake_chat(self, messages):
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))],
            usage=None,
        )

    monkeypatch.setattr(tr, "_chat", types.MethodType(fake_chat, tr))
    translation, record = tr.translate("hits consistently on even one", "pitched")
    concepts = {t.concept_name for t in translation.targets}
    assert "grid_attempt_pct_even1" in concepts
    assert "grid_success_pct_even1" not in concepts  # not fabricated
    assert record.error is None
