import tempfile
from pathlib import Path

import pretty_midi
from midi_analyzer_tagger.analysis import ExtractorRegistry, Pipeline
from midi_analyzer_tagger.analysis.midi_data import MidiData
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.quantizers import ContinuousQuantizer
from midi_analyzer_tagger.storage import AnalysisDatabase


class DummyExtractor(FeatureExtractor):
    def __init__(self):
        self._levels = [Level("Low", 1), Level("High", 2)]
        super().__init__(
            "dummy",
            [
                Concept(
                    name="dummy_level",
                    category="test",
                    family=["pitched"],
                    levels=self._levels,
                    quantizer=ContinuousQuantizer(
                        [(1.0, self._levels[0]), (float("inf"), self._levels[1])]
                    ),
                )
            ],
        )

    def extract(self, midi_data):
        return {"dummy_level": len(midi_data.notes)}


def _make_midi():
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    inst.notes.append(
        pretty_midi.Note(pitch=60, velocity=100, start=0, end=0.5)
    )
    midi.instruments.append(inst)
    return MidiData(midi)


def test_database_stores_payload():
    registry = ExtractorRegistry([DummyExtractor()])
    registry.compile_taxonomy()  # assigns level indices

    payload = Pipeline(registry).analyze(_make_midi())

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        with AnalysisDatabase(db_path) as db:
            db.store("test.mid", payload)
            tags = db.connection.execute(
                "SELECT * FROM tags WHERE concept_name = ?", ("dummy_level",)
            ).fetchall()
            assert len(tags) == 1
            assert tags[0]["level_name"] == "Low"
            assert tags[0]["level_index"] == 0
