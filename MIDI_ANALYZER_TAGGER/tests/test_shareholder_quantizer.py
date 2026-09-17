
from midi_analyzer_tagger.core import Level
from midi_analyzer_tagger.quantizers import ShareholderQuantizer

LEVELS = [
    Level("Defining", 5),
    Level("Primary", 4),
    Level("Significant", 3),
    Level("Present", 2),
    Level("Occasional", 1),
]

THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0]


def test_shareholder_quantizer_maps_percentages():
    q = ShareholderQuantizer(levels=LEVELS, thresholds=THRESHOLDS)
    assert q.quantize(80.0).name == "Defining"
    assert q.quantize(50.0).name == "Primary"
    assert q.quantize(30.0).name == "Significant"
    assert q.quantize(20.0).name == "Present"
    assert q.quantize(5.0).name == "Occasional"
    assert q.quantize(4.9) is None
    assert q.quantize(None) is None


def test_shareholder_quantizer_can_return_negligible_level():
    negligible = Level("Negligible", 0)
    q = ShareholderQuantizer(
        levels=LEVELS,
        thresholds=THRESHOLDS,
        negligible_level=negligible,
    )
    assert q.quantize(4.9) == negligible
