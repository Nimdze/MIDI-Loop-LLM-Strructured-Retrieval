from dataclasses import dataclass
from typing import Any

from midi_analyzer_tagger.core import Level, Quantizer


@dataclass
class CategoricalQuantizer(Quantizer):
    """Map a discrete value to a Level using a fixed mapping."""

    mapping: dict[Any, Level]
    default: Level | None = None

    def quantize(self, raw_value: Any) -> Level | None:
        return self.mapping.get(raw_value, self.default)
