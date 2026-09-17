import json
import tempfile
from pathlib import Path

from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.exporters.taxonomy import TaxonomyExporter
from midi_analyzer_tagger.quantizers import ContinuousQuantizer


class DummyExtractor(FeatureExtractor):
    def __init__(self):
        self._levels = [
            Level("Low", 1, description="few notes"),
            Level("High", 2, description="many notes"),
        ]
        super().__init__(
            "dummy",
            [
                Concept(
                    name="dummy_density",
                    category="test",
                    family=["pitched"],
                    levels=self._levels,
                    quantizer=ContinuousQuantizer(
                        [(1.0, self._levels[0]), (float("inf"), self._levels[1])]
                    ),
                    description="Number of notes per unit time.",
                    default_weight=1.0,
                    mutually_exclusive=True,
                )
            ],
        )

    def extract(self, midi_data):
        return {"dummy_density": 0}


def test_taxonomy_export():
    registry = ExtractorRegistry([DummyExtractor()])
    exporter = TaxonomyExporter(registry)
    taxonomy = exporter.to_dict()
    assert "dummy_density" in taxonomy
    assert taxonomy["dummy_density"]["llm"]["description"] == "Number of notes per unit time."
    assert taxonomy["dummy_density"]["llm"]["scope"] == "summary"
    assert taxonomy["dummy_density"]["llm"]["levels"][0][1] == "Low"
    assert taxonomy["dummy_density"]["llm"]["levels"][1][1] == "High"


def test_taxonomy_to_json():
    registry = ExtractorRegistry([DummyExtractor()])
    exporter = TaxonomyExporter(registry)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "taxonomy.json"
        exporter.to_json(path)
        data = json.loads(path.read_text())
        assert "dummy_density" in data
        assert data["dummy_density"]["llm"]["category"] == "test"
