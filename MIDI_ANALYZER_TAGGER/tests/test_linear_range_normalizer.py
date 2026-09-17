import pytest
from midi_analyzer_tagger.normalizers.linear_range import LinearRangeNormalizer


class TestLinearRangeNormalizer:
    def test_normalize_midpoint(self):
        normalizer = LinearRangeNormalizer(0.0, 100.0)
        assert normalizer.normalize(50.0, None, None) == 0.5

    def test_normalize_min(self):
        normalizer = LinearRangeNormalizer(0.0, 100.0)
        assert normalizer.normalize(0.0, None, None) == 0.0

    def test_normalize_max(self):
        normalizer = LinearRangeNormalizer(0.0, 100.0)
        assert normalizer.normalize(100.0, None, None) == 1.0

    def test_normalize_clamps_below(self):
        normalizer = LinearRangeNormalizer(0.0, 100.0)
        assert normalizer.normalize(-10.0, None, None) == 0.0

    def test_normalize_clamps_above(self):
        normalizer = LinearRangeNormalizer(0.0, 100.0)
        assert normalizer.normalize(150.0, None, None) == 1.0

    def test_normalize_none_returns_none(self):
        normalizer = LinearRangeNormalizer(0.0, 100.0)
        assert normalizer.normalize(None, None, None) is None

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            LinearRangeNormalizer(100.0, 0.0)
