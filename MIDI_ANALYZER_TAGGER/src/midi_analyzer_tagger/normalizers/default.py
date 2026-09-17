from midi_analyzer_tagger.core import Level, Normalizer


class DefaultNormalizer(Normalizer):
    """Normalize by the position of the matched level within the concept's ordered levels.

    Returns a scalar in [0, 1].
    """

    def normalize(self, raw_value, level: Level | None, concept) -> float | None:
        if level is None or not concept.levels:
            return None
        for i, lvl in enumerate(concept.levels):
            if lvl.name == level.name:
                position = i
                break
        else:
            return None
        if len(concept.levels) == 1:
            return 0.0
        return position / (len(concept.levels) - 1)
