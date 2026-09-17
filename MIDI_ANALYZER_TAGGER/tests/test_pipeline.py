import pretty_midi
from midi_analyzer_tagger.analysis.midi_data import MidiData
from midi_analyzer_tagger.analysis.pipeline import Pipeline
from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.core import AnalysisPayload, Concept, FeatureExtractor, Level
from midi_analyzer_tagger.quantizers import ContinuousQuantizer


class DummyExtractor(FeatureExtractor):
    def __init__(self):
        levels = [Level("Low", 1), Level("High", 2)]
        super().__init__(
            "dummy",
            [
                Concept(
                    name="dummy_level",
                    category="test",
                    family=["pitched"],
                    levels=levels,
                    quantizer=ContinuousQuantizer(
                        [(1.0, levels[0]), (float("inf"), levels[1])]
                    ),
                )
            ],
        )

    def extract(self, midi_data):
        return {"dummy_level": len(midi_data.notes)}


def _make_midi(note_count: int) -> MidiData:
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    for i in range(note_count):
        instrument.notes.append(
            pretty_midi.Note(
                velocity=100,
                pitch=60,
                start=i * 0.25,
                end=i * 0.25 + 0.1,
            )
        )
    midi.instruments.append(instrument)
    return MidiData(midi)


def test_pipeline_runs_dummy_extractor():
    registry = ExtractorRegistry([DummyExtractor()])
    pipeline = Pipeline(registry)
    data = _make_midi(note_count=5)
    payload = pipeline.analyze(data)
    assert payload.family == "pitched"
    assert payload.tags["dummy_level"].name == "High"
    assert payload.raw_features["dummy_level"] == 5
    assert isinstance(payload, AnalysisPayload)
    assert payload.normalized_features["dummy_level"] == 1.0


class DuplicateExtractor(FeatureExtractor):
    def __init__(self, name: str, value: int):
        levels = [Level("Low", 1), Level("High", 2)]
        self._value = value
        super().__init__(
            name,
            [
                Concept(
                    name="shared",
                    category="test",
                    family=["pitched"],
                    levels=levels,
                    quantizer=ContinuousQuantizer(
                        [(1.0, levels[0]), (float("inf"), levels[1])]
                    ),
                )
            ],
        )

    def extract(self, midi_data):
        return {"shared": self._value}


def test_pipeline_ignores_duplicate_concepts():
    registry = ExtractorRegistry([DuplicateExtractor("alpha", 5), DuplicateExtractor("beta", 99)])
    pipeline = Pipeline(registry)
    data = _make_midi(note_count=5)
    payload = pipeline.analyze(data)

    assert "shared" in payload.tags
    assert payload.tags["shared"].name == "High"
    assert payload.raw_features["shared"] == 5
    assert "shared" in payload.normalized_features

    assert payload.tags["shared"] is not None
    assert payload.tags["shared"].name == "High"
