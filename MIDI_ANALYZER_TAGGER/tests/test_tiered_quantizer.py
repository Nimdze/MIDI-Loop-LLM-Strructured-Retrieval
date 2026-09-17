from midi_analyzer_tagger.core import Level
from midi_analyzer_tagger.quantizers import TieredQuantizer


def test_tiered_quantizer_maps_to_threshold_tiers():
    levels = [
        Level("High", 3),
        Level("Medium", 2),
        Level("Low", 1),
    ]
    q = TieredQuantizer(thresholds=[10.0, 5.0], levels=levels)
    assert q.quantize(15.0) == levels[0]
    assert q.quantize(10.0) == levels[0]
    assert q.quantize(7.0) == levels[1]
    assert q.quantize(5.0) == levels[1]
    assert q.quantize(4.0) == levels[2]
    assert q.quantize(None) is None


def test_tiered_quantizer_requires_one_more_level_than_thresholds():
    try:
        TieredQuantizer(thresholds=[10.0, 5.0], levels=[Level("High", 3)])
    except ValueError as e:
        assert "one more entry" in str(e)
    else:
        assert False, "expected ValueError"
