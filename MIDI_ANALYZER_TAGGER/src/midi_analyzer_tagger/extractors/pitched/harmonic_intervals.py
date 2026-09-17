from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.pitched.pitch_segments import _get_pitch_segments
from midi_analyzer_tagger.quantizers import ShareholderQuantizer

SHAREHOLDER_THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0, 0.0]

HARMONIC_INTERVAL_NAMES: dict[int, str] = {
    0: "unison (same pitch)",
    1: "minor second",
    2: "major second",
    3: "minor third",
    4: "major third",
    5: "perfect fourth",
    6: "tritone / augmented fourth / diminished fifth",
    7: "perfect fifth",
    8: "minor sixth",
    9: "major sixth",
    10: "minor seventh",
    11: "major seventh",
    12: "octave",
    13: "minor ninth (octave + minor second)",
    14: "major ninth (octave + major second)",
    15: "minor tenth (octave + minor third)",
    16: "major tenth (octave + major third)",
    17: "eleventh (octave + perfect fourth)",
    18: "augmented eleventh (octave + tritone)",
    19: "twelfth / perfect twelfth (octave + perfect fifth)",
    20: "minor thirteenth (octave + minor sixth)",
    21: "major thirteenth (octave + major sixth)",
    22: "minor fourteenth (octave + minor seventh)",
    23: "major fourteenth (octave + major seventh)",
    24: "double octave / fifteenth",
}

def _shareholder_levels(label: str) -> list[Level]:
    return [
        Level(f"Defining {label}", 5),
        Level(f"Primary {label}", 4),
        Level(f"Significant {label}", 3),
        Level(f"Present {label}", 2),
        Level(f"Occasional {label}", 1),
        Level(f"Negligible {label}", 0),
    ]


DETAIL_SHARE_LEVELS = [
    Level("Defining", 5),
    Level("Primary", 4),
    Level("Significant", 3),
    Level("Present", 2),
    Level("Occasional", 1),
    Level("Negligible", 0),
]

DETAIL_PROFILE_THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0, 0.0]

DETAIL_LEVEL_DESCRIPTIONS = {
    "Defining": ">= 75% of vertical intervals.",
    "Primary": ">= 50% of vertical intervals.",
    "Significant": ">= 30% of vertical intervals.",
    "Present": ">= 20% of vertical intervals.",
    "Occasional": ">= 5% of vertical intervals.",
    "Negligible": "No vertical intervals at this distance (< 5%).",
}

PERFECT_INTERVALS = {0, 5, 7}
IMPERFECT_INTERVALS = {3, 4, 8, 9}
DISSONANT_INTERVALS = {1, 2, 6, 10, 11}

SUMMARY_LABELS = {
    "harmonic_perfect_consonance_pct": "Perfect Consonance",
    "harmonic_imperfect_consonance_pct": "Imperfect Consonance",
    "harmonic_dissonance_pct": "Dissonance",
}

SUMMARY_LEVEL_DESCRIPTIONS = {
    "harmonic_perfect_consonance_pct": {
        "Perfect Consonance": "Open, stable power-chord intervals (4ths, 5ths, octaves).",
    },
    "harmonic_imperfect_consonance_pct": {
        "Imperfect Consonance": "Rich, tonal intervals (3rds, 6ths).",
    },
    "harmonic_dissonance_pct": {
        "Dissonance": "Tense intervals (2nds, 7ths, tritone).",
    },
}


class HarmonicIntervalsExtractor(FeatureExtractor):
    def __init__(self):
        detail_concepts = [
            Concept(
                name=f"profile_harmonic_intervals_pct_{i:02d}_semitones",
                category="voicing",
                family=["pitched"],
                levels=DETAIL_SHARE_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DETAIL_SHARE_LEVELS,
                    thresholds=DETAIL_PROFILE_THRESHOLDS,
                ),
                description=f"Percentage of vertical harmonic intervals that are exactly {i} semitones apart.",
                llm_description=(
                    f"Individual vertical interval percentages for {i} semitones "
                    f"({HARMONIC_INTERVAL_NAMES[i]}). Use the concept name suffix (XX_semitones) to identify which interval."
                ) if i == 0 else (
                    f"Percentage of vertical (chordal) intervals that are {i} semitones "
                    f"({HARMONIC_INTERVAL_NAMES[i]})."
                ) if i in HARMONIC_INTERVAL_NAMES else "",
                llm_interpretation=(
                    f"Use for queries that name a specific vertical interval or chord voicing "
                    f"(e.g. 'open fifths', 'octave voicings', 'dissonant seconds'). "
                    f"The semitone suffix in the concept name identifies the interval "
                    f"(00 = unison, 07 = perfect fifth, 12 = octave). "
                    f"Pair these micro-interval shares with the consonance aggregates for the overall character."
                    if i == 0 else
                    f"Vertical chordal interval — {i} semitones = {HARMONIC_INTERVAL_NAMES[i]}. "
                    f"Use for queries naming this specific vertical interval."
                ) if i in HARMONIC_INTERVAL_NAMES else "",
                llm_examples=(
                    [f"vertical intervals are mostly {HARMONIC_INTERVAL_NAMES[i].split('(')[0].strip()}",
                     f"predominantly {HARMONIC_INTERVAL_NAMES[i].split('(')[0].strip()} chord voicings"]
                ) if i in HARMONIC_INTERVAL_NAMES else [],
                llm_level_descriptions=DETAIL_LEVEL_DESCRIPTIONS,
                scope="detail",
                default_weight=1.0,
            )
            for i in range(25)
        ]

        summary_concepts = [
            Concept(
                name="harmonic_perfect_consonance_pct",
                category="voicing",
                family=["pitched"],
                levels=_shareholder_levels(SUMMARY_LABELS["harmonic_perfect_consonance_pct"]),
                quantizer=ShareholderQuantizer(
                    levels=_shareholder_levels(SUMMARY_LABELS["harmonic_perfect_consonance_pct"]),
                    thresholds=SHAREHOLDER_THRESHOLDS,
                ),
                description="Percentage of vertical intervals that are perfect consonances (unison/octave, 4th, 5th).",
                llm_description="Share of perfect consonant intervals (4ths, 5ths, octaves).",
                llm_interpretation="Use for 'open', 'stable', 'power chord', or 'fifths/octaves' character. High perfect consonance gives an open, grounded, stable acoustic character. Pair with the specific interval concepts for the micro-vocabulary.",
                llm_examples=["the vertical harmony is mostly perfect consonances", "stable perfect consonance harmony"],
                llm_level_descriptions={
                    **{
                        level.name: f"{level.name.split(' ', 1)[0]} share of perfect consonance (>= {SHAREHOLDER_THRESHOLDS[i]}%)."
                        for i, level in enumerate(_shareholder_levels(SUMMARY_LABELS["harmonic_perfect_consonance_pct"])[:-1])
                    },
                    "Negligible Perfect Consonance": "No perfect consonance intervals present.",
                },
                llm_subcategory="harmonic intervals",
                scope="summary",
                llm_bin_family="harmonic_consonance_pct",
                llm_bin_label="Perfect Consonance",
            ),
            Concept(
                name="harmonic_imperfect_consonance_pct",
                category="voicing",
                family=["pitched"],
                levels=_shareholder_levels(SUMMARY_LABELS["harmonic_imperfect_consonance_pct"]),
                quantizer=ShareholderQuantizer(
                    levels=_shareholder_levels(SUMMARY_LABELS["harmonic_imperfect_consonance_pct"]),
                    thresholds=SHAREHOLDER_THRESHOLDS,
                ),
                description="Percentage of vertical intervals that are imperfect consonances (3rds and 6ths).",
                llm_description="Share of imperfect consonant intervals (major/minor 3rds and 6ths).",
                llm_interpretation="Use for 'rich', 'tonal', 'triadic', or 'warm' harmony. High imperfect consonance gives a full, warm, tonal character (the classic triad sound).",
                llm_examples=["warm rich thirds and sixths harmony", "imperfect consonance creates warm tonality"],
                llm_level_descriptions={
                    **{
                        level.name: f"{level.name.split(' ', 1)[0]} share of imperfect consonance (>= {SHAREHOLDER_THRESHOLDS[i]}%)."
                        for i, level in enumerate(_shareholder_levels(SUMMARY_LABELS["harmonic_imperfect_consonance_pct"])[:-1])
                    },
                    "Negligible Imperfect Consonance": "No imperfect consonance intervals present.",
                },
                llm_subcategory="harmonic intervals",
                scope="summary",
                llm_bin_family="harmonic_consonance_pct",
                llm_bin_label="Imperfect Consonance",
            ),
            Concept(
                name="harmonic_dissonance_pct",
                category="voicing",
                family=["pitched"],
                levels=_shareholder_levels(SUMMARY_LABELS["harmonic_dissonance_pct"]),
                quantizer=ShareholderQuantizer(
                    levels=_shareholder_levels(SUMMARY_LABELS["harmonic_dissonance_pct"]),
                    thresholds=SHAREHOLDER_THRESHOLDS,
                ),
                description="Percentage of vertical intervals that are dissonances (2nds, 7ths, tritone).",
                llm_description="Share of dissonant intervals (2nds, 7ths, tritone).",
                llm_interpretation="Use for 'dissonant', 'jazzy', 'tense', or 'atonal' harmony. High dissonance gives a tense, unstable acoustic character. Combine with the specific interval concepts to identify which clashes dominate.",
                llm_examples=["very dissonant tense harmony", "tritone clashes are prominent", "atonal unstable sound"],
                llm_level_descriptions={
                    **{
                        level.name: f"{level.name.split(' ', 1)[0]} share of dissonance (>= {SHAREHOLDER_THRESHOLDS[i]}%)."
                        for i, level in enumerate(_shareholder_levels(SUMMARY_LABELS["harmonic_dissonance_pct"])[:-1])
                    },
                    "Negligible Dissonance": "No dissonance intervals present.",
                },
                llm_subcategory="harmonic intervals",
                scope="summary",
                llm_bin_family="harmonic_consonance_pct",
                llm_bin_label="Dissonance",
            ),
        ]

        super().__init__(
            "harmonic_intervals",
            detail_concepts + summary_concepts,
            llm_description="A histogram of the vertical intervals between simultaneously sounding notes (chord voicings), granular to each semitone — from perfect consonance through specific sizes like fifths and octaves to dissonance.",
            llm_subcategory="harmonic intervals",
        )

    def extract(self, midi_data) -> dict:
        notes = midi_data.notes
        segments = _get_pitch_segments(notes)
        profile = _get_harmonic_intervals_profile(segments)
        summaries = _summarize_consonance(profile)
        return {**profile, **summaries}


def _get_harmonic_intervals_profile(segments):
    bins = {f"profile_harmonic_intervals_pct_{i:02d}_semitones": 0.0 for i in range(25)}

    if not segments:
        return bins

    total_interval_dur = 0.0
    raw_counts = {i: 0.0 for i in range(25)}

    for pitches, dur in segments:
        if len(pitches) >= 2:
            for i in range(len(pitches)):
                for j in range(i + 1, len(pitches)):
                    interval = abs(pitches[i] - pitches[j])
                    if interval <= 24:
                        raw_counts[interval] += dur
                        total_interval_dur += dur

    if total_interval_dur > 0:
        for i in range(25):
            key = f"profile_harmonic_intervals_pct_{i:02d}_semitones"
            bins[key] = round((raw_counts[i] / total_interval_dur) * 100.0, 2)

    return bins


def _summarize_consonance(profile):
    perfect = 0.0
    imperfect = 0.0
    dissonant = 0.0

    for i in range(25):
        key = f"profile_harmonic_intervals_pct_{i:02d}_semitones"
        value = profile[key]
        interval_class = i % 12

        if interval_class in PERFECT_INTERVALS:
            perfect += value
        elif interval_class in IMPERFECT_INTERVALS:
            imperfect += value
        elif interval_class in DISSONANT_INTERVALS:
            dissonant += value

    return {
        "harmonic_perfect_consonance_pct": round(perfect, 2),
        "harmonic_imperfect_consonance_pct": round(imperfect, 2),
        "harmonic_dissonance_pct": round(dissonant, 2),
    }
