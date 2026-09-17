def test_shareholder_quantizer_levels_are_ordered_by_threshold():
    from midi_analyzer_tagger.core import Level
    from midi_analyzer_tagger.quantizers import ShareholderQuantizer

    levels = [
        Level("Defining", 5),
        Level("Primary", 4),
        Level("Significant", 3),
        Level("Present", 2),
        Level("Occasional", 1),
    ]
    q = ShareholderQuantizer(levels=levels, thresholds=[75.0, 50.0, 30.0, 20.0, 5.0])

    assert q.quantize(80.0).weight == 5
    assert q.quantize(50.0).weight == 4
    assert q.quantize(30.0).weight == 3
    assert q.quantize(20.0).weight == 2
    assert q.quantize(5.0).weight == 1
    assert q.quantize(4.0) is None
