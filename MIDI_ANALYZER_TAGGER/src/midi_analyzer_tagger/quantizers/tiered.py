from dataclasses import dataclass

from midi_analyzer_tagger.core import Level, Quantizer


@dataclass
class TieredQuantizer(Quantizer):
    thresholds: list[float]
    levels: list[Level]

    def __post_init__(self):
        if len(self.levels) != len(self.thresholds) + 1:
            raise ValueError("levels must have exactly one more entry than thresholds")

    def quantize(self, raw_value: float) -> Level | None:
        if raw_value is None:
            return None
        for threshold, level in zip(self.thresholds, self.levels):
            if raw_value >= threshold:
                return level
        return self.levels[-1]
