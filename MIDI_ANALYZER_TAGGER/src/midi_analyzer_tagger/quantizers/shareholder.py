from dataclasses import dataclass

from midi_analyzer_tagger.core import Level, Quantizer


@dataclass
class ShareholderQuantizer(Quantizer):
    """Map a percentage (0-100) to a tiered shareholder label.

    Thresholds are inclusive lower bounds from highest to lowest.
    Values below the lowest threshold return None by default, or a
    configurable negligible level when one is provided.
    """

    levels: list[Level]
    thresholds: list[float]
    negligible_level: Level | None = None

    def __post_init__(self):
        if len(self.levels) != len(self.thresholds):
            raise ValueError("levels and thresholds must have the same length")

    def quantize(self, raw_value: float) -> Level | None:
        if raw_value is None:
            return None
        for threshold, level in zip(self.thresholds, self.levels):
            if raw_value >= threshold:
                return level
        return self.negligible_level
