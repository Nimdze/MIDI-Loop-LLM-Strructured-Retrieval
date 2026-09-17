from midi_analyzer_tagger.core import Level, Normalizer


class LinearRangeNormalizer(Normalizer):
    """Scale a raw value to the [0, 1] interval using a fixed range.

    The quantizer already assigns a tag; this normalizer provides a
    continuous normalized value suitable for downstream analysis such as
    correlation matrices.
    """

    def __init__(self, min_value: float = 0.0, max_value: float = 1.0):
        if max_value <= min_value:
            raise ValueError("max_value must be greater than min_value")
        self.min_value = min_value
        self.max_value = max_value

    def normalize(self, raw_value: float, level: Level | None, concept) -> float | None:
        if raw_value is None:
            return None
        ratio = (raw_value - self.min_value) / (self.max_value - self.min_value)
        return max(0.0, min(1.0, ratio))
