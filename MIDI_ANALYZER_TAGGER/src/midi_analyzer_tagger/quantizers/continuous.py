from dataclasses import dataclass
from typing import Any

from midi_analyzer_tagger.core import Level, Quantizer


@dataclass
class ContinuousQuantizer(Quantizer):
    """
    Ordered levels with upper-bound thresholds.
    Levels and thresholds must be ordered from low to high.
    """

    thresholds: list[tuple[float, Level]]  # [(upper_bound_inclusive, Level), ...]

    def quantize(self, raw_value: float) -> Level | None:
        if raw_value is None:
            return None
        for upper_bound, level in self.thresholds:
            if raw_value <= upper_bound:
                return level
        return None


@dataclass
class RawValueQuantizer(Quantizer):
    """Pass the raw value through as the level name (no bucketing).

    Used for factual metadata values (tempo, measures, note count) that should be
    stored at their exact value for search, rather than bucketed into presence or
    range labels. Returns None for absent/zero values so no spurious tag is
    written.
    """

    def quantize(self, raw_value: Any) -> Level | None:
        if raw_value is None or isinstance(raw_value, bool):
            return None
        if not isinstance(raw_value, (int, float)):
            return None
        if raw_value == 0:
            return None
        if isinstance(raw_value, float) and raw_value.is_integer():
            name = str(int(raw_value))
        else:
            name = str(raw_value)
        return Level(name=name, weight=1)
