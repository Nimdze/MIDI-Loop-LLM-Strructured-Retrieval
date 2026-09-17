import logging

from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.quantizers import ContinuousQuantizer


class DummyExtractor(FeatureExtractor):
    def __init__(self, name="dummy", concept_name="density"):
        super().__init__(
            name,
            [
                Concept(
                    name=concept_name,
                    category="test",
                    family=["pitched"],
                    levels=[Level("Low", 1), Level("High", 2)],
                    quantizer=ContinuousQuantizer([]),
                )
            ],
        )

    def extract(self, midi_data):
        return {}


def test_registry_assigns_indices():
    reg = ExtractorRegistry([DummyExtractor("alpha", "density")])
    taxonomy = reg.compile_taxonomy()
    assert "density" in taxonomy
    levels = taxonomy["density"]["llm"]["levels"]
    assert len(levels) == 2
    assert levels[0][0] == 0
    assert levels[1][0] == 1


def test_registry_detects_duplicate_concepts(caplog):
    caplog.set_level(logging.WARNING)
    reg = ExtractorRegistry()
    reg.register(DummyExtractor("alpha", "density"))
    reg.register(DummyExtractor("beta", "density"))
    taxonomy = reg.compile_taxonomy()
    assert "Duplicate concept 'density'" in caplog.text
    assert "density" in taxonomy
    assert len(taxonomy["density"]["llm"]["levels"]) == 2


def test_registry_preserves_existing_taxonomy_indices():
    existing = {
        "density": {"llm": {"levels": [[5, "Low", 1], [6, "High", 2]]}},
        "other": {"llm": {"levels": [[0, "Low", 1], [1, "High", 2]]}},
    }
    reg = ExtractorRegistry([DummyExtractor("alpha", "density")], existing_taxonomy=existing)
    taxonomy = reg.compile_taxonomy()
    levels = taxonomy["density"]["llm"]["levels"]
    assert levels[0][0] == 5
    assert levels[1][0] == 6


def test_registry_assigns_new_indices_after_existing():
    existing = {
        "other": {"llm": {"levels": [[5, "Low", 1], [6, "High", 2]]}},
    }
    reg = ExtractorRegistry([DummyExtractor("alpha", "density")], existing_taxonomy=existing)
    taxonomy = reg.compile_taxonomy()
    levels = taxonomy["density"]["llm"]["levels"]
    assert levels[0][0] == 7
    assert levels[1][0] == 8


def test_registry_owns_concept_and_owned_concepts():
    reg = ExtractorRegistry()
    reg.register(DummyExtractor("alpha", "density"))
    reg.register(DummyExtractor("beta", "other"))
    assert reg.owns_concept("alpha", "density")
    assert reg.owns_concept("beta", "other")
    assert not reg.owns_concept("beta", "density")
    assert reg.owned_concepts("alpha") == {"density"}
    assert reg.owned_concepts("beta") == {"other"}
