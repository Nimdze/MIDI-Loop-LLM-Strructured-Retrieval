from collections import Counter

import numpy as np
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps, group_notes_into_events
from midi_analyzer_tagger.quantizers import ShareholderQuantizer, TieredQuantizer

PROFILE_INTERVALS = list(range(1, 13))

MELODIC_INTERVAL_NAMES: dict[int, str] = {
    1: "minor second (1 semitone)",
    2: "major second (2 semitones)",
    3: "minor third (3 semitones)",
    4: "major third (4 semitones)",
    5: "perfect fourth (5 semitones)",
    6: "tritone (6 semitones)",
    7: "perfect fifth (7 semitones)",
    8: "minor sixth (8 semitones)",
    9: "major sixth (9 semitones)",
    10: "minor seventh (10 semitones)",
    11: "major seventh (11 semitones)",
    12: "octave (12 semitones)",
}

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
    "Defining": ">= 75% of melodic intervals.",
    "Primary": ">= 50% of melodic intervals.",
    "Significant": ">= 30% of melodic intervals.",
    "Present": ">= 20% of melodic intervals.",
    "Occasional": ">= 5% of melodic intervals.",
    "Negligible": "No melodic intervals of this kind (< 5%).",
}

MEDIAN_INTERVAL_LEVELS = [
    Level("Angular / Leaping Melodic Motion", 3),
    Level("Medium Melodic Motion", 2),
    Level("Stepwise / Scalar Melodic Motion", 1),
]

MEDIAN_INTERVAL_THRESHOLDS = [4.0, 2.0]

MAX_LEAP_LEVELS = [
    Level("Contains Extreme Leaps (>= Octave)", 3),
    Level("Contains Standard Leaps", 2),
    Level("No Leaps (< Perfect 4th)", 1),
]

MAX_LEAP_THRESHOLDS = [12.0, 5.0]

DIRECTION_LEVELS = [
    Level("Defining Ascending Motion", 6),
    Level("Primary Ascending Motion", 5),
    Level("Significant Ascending Motion", 4),
    Level("Present Ascending Motion", 3),
    Level("Occasional Ascending Motion", 2),
    Level("Negligible Ascending Motion", 1),
]

DIRECTION_LEVELS_DESC = [
    Level("Defining Descending Motion", 6),
    Level("Primary Descending Motion", 5),
    Level("Significant Descending Motion", 4),
    Level("Present Descending Motion", 3),
    Level("Occasional Descending Motion", 2),
    Level("Negligible Descending Motion", 1),
]

DIRECTION_THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0, 0.0]

SEQUENCE_REPETITION_LEVELS = [
    Level("Repetitive Interval Patterns", 5),
    Level("Mid-High Interval Pattern Repetition", 4),
    Level("Medium Interval Pattern Repetition", 3),
    Level("Mid-Low Interval Pattern Repetition", 2),
    Level("Varying Interval Patterns", 1),
]

SEQUENCE_REPETITION_THRESHOLDS = [90.0, 80.0, 50.0, 15.0]

VOCABULARY_COUNT_LEVELS = [
    Level("Highly Diverse Melodic Interval Palette", 3),
    Level("Standard Melodic Interval Palette", 2),
    Level("Focused Melodic Interval Palette", 1),
]

VOCABULARY_COUNT_THRESHOLDS = [5.5, 2.5]


class MelodicExtractor(FeatureExtractor):
    def __init__(self):
        profile_concepts = [
            Concept(
                name=f"profile_melodic_intervals_pct_asc_{i}_semitones",
                category="melody",
                family=["pitched"],
                levels=DETAIL_SHARE_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DETAIL_SHARE_LEVELS,
                    thresholds=DETAIL_PROFILE_THRESHOLDS,
                ),
                description=f"Percentage of melodic intervals that jump a {i} semitone(s) UP.",
                llm_description=(
                    f"Percentage of melodic (horizontal) intervals that jump UP by "
                    f"{MELODIC_INTERVAL_NAMES[i]}."
                ),
                llm_interpretation=(
                    "Use for queries that name a specific ascending melodic interval "
                    "(e.g. 'rising fifths', 'upward stepwise motion', 'octave leaps up'). "
                    "The concept name suffix gives the size (1-12 semitones, or 13plus = more than an octave up)."
                ),
                llm_examples=[f"melody mostly leaps up by {MELODIC_INTERVAL_NAMES[i].split('(')[0].strip()}"],
                llm_level_descriptions=DETAIL_LEVEL_DESCRIPTIONS,
                scope="detail",
                default_weight=1.0,
            )
            for i in PROFILE_INTERVALS
        ]
        profile_concepts += [
            Concept(
                name=f"profile_melodic_intervals_pct_desc_{i}_semitones",
                category="melody",
                family=["pitched"],
                levels=DETAIL_SHARE_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DETAIL_SHARE_LEVELS,
                    thresholds=DETAIL_PROFILE_THRESHOLDS,
                ),
                description=f"Percentage of melodic intervals that jump a {i} semitone(s) DOWN.",
                llm_description=(
                    f"Percentage of melodic (horizontal) intervals that jump DOWN by "
                    f"{MELODIC_INTERVAL_NAMES[i]}."
                ),
                llm_interpretation=(
                    "Use for queries that name a specific descending melodic interval "
                    "(e.g. 'falling fourths', 'downward leaps', 'octave leaps down'). "
                    "The concept name suffix gives the size (1-12 semitones, or 13plus = more than an octave down)."
                ),
                llm_examples=[f"melody mostly falls down by {MELODIC_INTERVAL_NAMES[i].split('(')[0].strip()}"],
                llm_level_descriptions=DETAIL_LEVEL_DESCRIPTIONS,
                scope="detail",
                default_weight=1.0,
            )
            for i in PROFILE_INTERVALS
        ]
        profile_concepts += [
            Concept(
                name="profile_melodic_intervals_pct_static",
                category="melody",
                family=["pitched"],
                levels=DETAIL_SHARE_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DETAIL_SHARE_LEVELS,
                    thresholds=DETAIL_PROFILE_THRESHOLDS,
                ),
                description="Percentage of intervals that are repeated notes (0 semitones).",
                llm_description="Percentage of melodic intervals that are repeated notes (0 semitones).",
                llm_interpretation="Use for 'repeated notes', 'static melody', or '0-semitone intervals'. A high share means the melody frequently restates the same pitch; a low share means it keeps moving to new notes.",
                llm_examples=["melody restates the same note", "lots of repeated notes", "keeps moving to new notes"],
                llm_level_descriptions=DETAIL_LEVEL_DESCRIPTIONS,
                scope="detail",
                default_weight=1.0,
            ),
            Concept(
                name="profile_melodic_intervals_pct_asc_13plus_semitones",
                category="melody",
                family=["pitched"],
                levels=DETAIL_SHARE_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DETAIL_SHARE_LEVELS,
                    thresholds=DETAIL_PROFILE_THRESHOLDS,
                ),
                description="Percentage of melodic intervals jumping UP by more than an octave (13+ semitones).",
                llm_description="Percentage of ascending melodic intervals larger than an octave (13+ semitones).",
                llm_interpretation="Use for 'extreme upward leaps' — ascending intervals beyond an octave. The asc_13plus bin captures dramatic, wide upward jumps.",
                llm_examples=["huge upward leaps beyond an octave", "extreme ascending jumps"],
                llm_level_descriptions=DETAIL_LEVEL_DESCRIPTIONS,
                scope="detail",
                default_weight=1.0,
            ),
            Concept(
                name="profile_melodic_intervals_pct_desc_13plus_semitones",
                category="melody",
                family=["pitched"],
                levels=DETAIL_SHARE_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DETAIL_SHARE_LEVELS,
                    thresholds=DETAIL_PROFILE_THRESHOLDS,
                ),
                description="Percentage of melodic intervals jumping DOWN by more than an octave (13+ semitones).",
                llm_description="Percentage of descending melodic intervals larger than an octave (13+ semitones).",
                llm_interpretation="Use for 'extreme downward leaps' — descending intervals beyond an octave. The desc_13plus bin captures dramatic, wide downward jumps.",
                llm_examples=["huge downward leaps beyond an octave", "extreme descending jumps"],
                llm_level_descriptions=DETAIL_LEVEL_DESCRIPTIONS,
                scope="detail",
                default_weight=1.0,
            ),
        ]

        summary_concepts = [
            Concept(
                name="melodic_intervals_absolute_median_semitones",
                category="melody",
                family=["pitched"],
                levels=MEDIAN_INTERVAL_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=MEDIAN_INTERVAL_THRESHOLDS,
                    levels=MEDIAN_INTERVAL_LEVELS,
                ),
                description="Median absolute semitone distance between consecutive lead notes.",
                llm_description="Typical melodic interval size.",
                llm_interpretation="Use this for 'stepwise', 'scalar', 'leaps', or 'angular melody'. Small median = stepwise; large = leaping.",
                llm_examples=["lots of stepwise scalar motion", "angular leaps and jumps", "mostly small intervals"],
                llm_level_descriptions={
                    "Angular / Leaping Melodic Motion": "Large typical intervals — the melody mostly leaps and jumps.",
                    "Medium Melodic Motion": "Moderate typical intervals — a mix of steps and small leaps.",
                    "Stepwise / Scalar Melodic Motion": "Small typical intervals — the melody mostly moves by step.",
                },
                llm_subcategory="melodic intervals",
                scope="summary",
            ),
            Concept(
                name="melodic_intervals_max_leap_semitones",
                category="melody",
                family=["pitched"],
                levels=MAX_LEAP_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=MAX_LEAP_THRESHOLDS,
                    levels=MAX_LEAP_LEVELS,
                ),
                description="The largest single absolute jump found in the lead line.",
                llm_description="Largest single melodic interval in the line.",
                llm_interpretation="Use this for 'melodic octaves', 'big leaps', or 'smooth melody'. As the largest interval in the line, it acts as a ceiling — use it to confirm that no melodic jump exceeds a certain size (e.g. 'never leaps more than a 4th', 'stays within an octave').",
                llm_examples=["melody has huge octave leaps", "smooth stepwise melody no jumps", "very large interval leaps"],
                llm_level_descriptions={
                    "Contains Extreme Leaps (>= Octave)": "The line contains very large jumps — an octave or more (dramatic resets).",
                    "Contains Standard Leaps": "The line contains moderate jumps — from a perfect 4th up to an octave.",
                    "No Leaps (< Perfect 4th)": "The line is very smooth — no large jumps, mostly steps.",
                },
                llm_subcategory="melodic intervals",
                scope="summary",
            ),
            Concept(
                name="melodic_intervals_pct_ascending",
                category="melody",
                family=["pitched"],
                levels=DIRECTION_LEVELS,
                quantizer=ShareholderQuantizer(
                    levels=DIRECTION_LEVELS,
                    thresholds=DIRECTION_THRESHOLDS,
                ),
                description="Percentage of melodic movements that climb UP.",
                llm_description="Percentage of intervals that climb UP.",
                llm_interpretation="Use this for 'rising melody', 'ascending line', or 'climbing'. Use the descending concept for the opposite.",
                llm_examples=["melody rises upward throughout", "mostly ascending melodic lines", "climbing contour"],
                llm_level_descriptions={
                    "Defining Ascending Motion": ">= 75% of intervals move in this direction.",
                    "Primary Ascending Motion": ">= 50% of intervals move in this direction.",
                    "Significant Ascending Motion": ">= 30% of intervals move in this direction.",
                    "Present Ascending Motion": ">= 20% of intervals move in this direction.",
                    "Occasional Ascending Motion": ">= 5% of intervals move in this direction.",
                    "Negligible Ascending Motion": "No measurable motion in this direction (< 5%).",
                },
                llm_subcategory="melodic intervals",
                scope="summary",
                llm_bin_family="melodic_direction",
                llm_bin_label="ascending",
            ),
            Concept(
                name="melodic_intervals_pct_descending",
                category="melody",
                family=["pitched"],
                levels=DIRECTION_LEVELS_DESC,
                quantizer=ShareholderQuantizer(
                    levels=DIRECTION_LEVELS_DESC,
                    thresholds=DIRECTION_THRESHOLDS,
                ),
                description="Percentage of melodic movements that fall DOWN.",
                llm_description="Percentage of intervals that fall DOWN.",
                llm_interpretation="Use this for 'falling melody', 'descending line', or 'descending contour'. Use the ascending concept for the opposite.",
                llm_examples=["melody falls downward throughout", "mostly descending melodic lines", "dropping contour"],
                llm_level_descriptions={
                    "Defining Descending Motion": ">= 75% of intervals move in this direction.",
                    "Primary Descending Motion": ">= 50% of intervals move in this direction.",
                    "Significant Descending Motion": ">= 30% of intervals move in this direction.",
                    "Present Descending Motion": ">= 20% of intervals move in this direction.",
                    "Occasional Descending Motion": ">= 5% of intervals move in this direction.",
                    "Negligible Descending Motion": "No measurable motion in this direction (< 5%).",
                },
                llm_subcategory="melodic intervals",
                scope="summary",
                llm_bin_family="melodic_direction",
                llm_bin_label="descending",
            ),
            Concept(
                name="melodic_intervals_sequence_repetition_pct",
                category="melody",
                family=["pitched"],
                levels=SEQUENCE_REPETITION_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=SEQUENCE_REPETITION_THRESHOLDS,
                    levels=SEQUENCE_REPETITION_LEVELS,
                ),
                description="Percentage of the melody that belongs to a structured, repeating sequence.",
                llm_description="How repetitive the melodic pattern is.",
                llm_interpretation="Use this for 'repetitive', 'motivic', 'loop-based', or 'through-composed'. High repetition means looping motifs; low means varying.",
                llm_examples=["repetitive melodic patterns", "motivic repeating phrases", "through-composed constantly changing"],
                llm_level_descriptions={
                    "Repetitive Interval Patterns": "Highly repetitive — the melody is dominated by looping motifs.",
                    "Mid-High Interval Pattern Repetition": "Mostly repetitive with some variation.",
                    "Medium Interval Pattern Repetition": "A balance of repetition and variation.",
                    "Mid-Low Interval Pattern Repetition": "Mostly varied with occasional repetition.",
                    "Varying Interval Patterns": "Non-repetitive — the melody keeps changing.",
                },
                llm_subcategory="melodic intervals",
                scope="summary",
            ),
            Concept(
                name="melodic_interval_vocabulary_count",
                category="melody",
                family=["pitched"],
                levels=VOCABULARY_COUNT_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=VOCABULARY_COUNT_THRESHOLDS,
                    levels=VOCABULARY_COUNT_LEVELS,
                ),
                description="Number of distinct melodic interval classes used in the lead line.",
                llm_description="How many different melodic interval types the melody uses.",
                llm_interpretation="Use this for 'focused' interval palette vs 'diverse' or 'wide' melodic vocabulary.",
                llm_examples=["focused narrow interval palette", "diverse interval vocabulary", "wide range of melodic intervals"],
                llm_level_descriptions={
                    "Highly Diverse Melodic Interval Palette": "Uses a wide, diverse set of interval types — complex melodic vocabulary.",
                    "Standard Melodic Interval Palette": "Uses a moderate, typical set of interval types.",
                    "Focused Melodic Interval Palette": "Uses only a small, focused set of interval types.",
                },
                llm_subcategory="melodic intervals",
                scope="summary",
                default_weight=1.0,
            ),
        ]

        super().__init__(
            "melodic",
            summary_concepts + profile_concepts,
            llm_description="Melodic analysis describes the shape, motion, direction, repetition, and interval palette of the lead line.",
            llm_subcategory="melodic intervals",
        )

    def extract(self, midi_data) -> dict:
        notes = midi_data.notes
        if not notes or len(notes) < 2:
            return self._empty_profile()

        mel_ints = _get_melodic_intervals(notes, midi_data.midi)
        results = _get_melodic_intervals_macro(mel_ints)
        results.update(_get_melodic_intervals_profile(mel_ints))
        return results

    def _empty_profile(self) -> dict:
        results = {
            "melodic_intervals_absolute_median_semitones": 0.0,
            "melodic_intervals_max_leap_semitones": 0,
            "melodic_intervals_pct_ascending": 0.0,
            "melodic_intervals_pct_descending": 0.0,
            "melodic_intervals_sequence_repetition_pct": 0.0,
            "melodic_interval_vocabulary_count": 0,
        }
        for i in PROFILE_INTERVALS:
            results[f"profile_melodic_intervals_pct_asc_{i}_semitones"] = 0.0
            results[f"profile_melodic_intervals_pct_desc_{i}_semitones"] = 0.0
        results["profile_melodic_intervals_pct_static"] = 0.0
        results["profile_melodic_intervals_pct_asc_13plus_semitones"] = 0.0
        results["profile_melodic_intervals_pct_desc_13plus_semitones"] = 0.0
        return results


def _get_melodic_intervals(notes, midi):
    if len(notes) < 2:
        return []

    bps = get_bps(midi)
    events = group_notes_into_events(notes, bps)
    lead_pitches = [max(note["pitch"] for note in group) for group in events]
    return [lead_pitches[i] - lead_pitches[i - 1] for i in range(1, len(lead_pitches))]


def _get_melodic_intervals_macro(mel_ints):
    abs_mel = [abs(i) for i in mel_ints]
    asc_ints = [i for i in mel_ints if i > 0]
    desc_ints = [i for i in mel_ints if i < 0]
    total_mel = len(mel_ints)

    return {
        "melodic_intervals_absolute_median_semitones": _calc_melodic_median(abs_mel),
        "melodic_intervals_max_leap_semitones": _calc_max_leap(abs_mel),
        "melodic_intervals_pct_ascending": _calc_direction_percent(len(asc_ints), total_mel),
        "melodic_intervals_pct_descending": _calc_direction_percent(len(desc_ints), total_mel),
        "melodic_intervals_sequence_repetition_pct": _calc_sequence_repetition(abs_mel),
        "melodic_interval_vocabulary_count": _calc_vocabulary_count(mel_ints),
    }


def _calc_vocabulary_count(mel_ints):
    return len({abs(i) for i in mel_ints}) if mel_ints else 0



def _calc_melodic_median(abs_mel):
    return round(float(np.median(abs_mel)), 2) if abs_mel else 0.0


def _calc_max_leap(abs_mel):
    return int(np.max(abs_mel)) if abs_mel else 0


def _calc_direction_percent(subset_len, total_len):
    if total_len == 0:
        return 0.0
    return round((subset_len / total_len) * 100, 2)


def _calc_sequence_repetition(abs_mel):
    if len(abs_mel) < 2:
        return 0.0

    n = len(abs_mel)
    in_pattern = [False] * n

    for length in [8, 7, 6, 5, 4, 3, 2, 1]:
        for i in range(n - 2 * length + 1):
            if abs_mel[i : i + length] == abs_mel[i + length : i + 2 * length]:
                for j in range(i, i + 2 * length):
                    in_pattern[j] = True

    repeating_count = sum(in_pattern)
    return round((repeating_count / n) * 100, 2)


def _get_melodic_intervals_profile(mel_ints):
    stats = {f"profile_melodic_intervals_pct_asc_{i}_semitones": 0.0 for i in PROFILE_INTERVALS}
    stats.update({f"profile_melodic_intervals_pct_desc_{i}_semitones": 0.0 for i in PROFILE_INTERVALS})
    stats.update({
        "profile_melodic_intervals_pct_static": 0.0,
        "profile_melodic_intervals_pct_asc_13plus_semitones": 0.0,
        "profile_melodic_intervals_pct_desc_13plus_semitones": 0.0,
    })

    if not mel_ints:
        return stats

    total = len(mel_ints)
    counts = Counter(mel_ints)

    for i in PROFILE_INTERVALS:
        stats[f"profile_melodic_intervals_pct_asc_{i}_semitones"] = round((counts[i] / total * 100), 2)
        stats[f"profile_melodic_intervals_pct_desc_{i}_semitones"] = round((counts[-i] / total * 100), 2)

    stats["profile_melodic_intervals_pct_static"] = round((counts[0] / total * 100), 2)

    asc_13_plus = sum(counts[k] for k in counts.keys() if k > 12)
    desc_13_plus = sum(counts[k] for k in counts.keys() if k < -12)

    stats["profile_melodic_intervals_pct_asc_13plus_semitones"] = round((asc_13_plus / total * 100), 2)
    stats["profile_melodic_intervals_pct_desc_13plus_semitones"] = round((desc_13_plus / total * 100), 2)

    return stats
