import numpy as np

from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import _note_attr, get_bps, group_notes_into_events
from midi_analyzer_tagger.quantizers import ShareholderQuantizer, TieredQuantizer


SHAREHOLDER_THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0, 0.0]


def _shareholder_levels(label: str) -> list[Level]:
    return [
        Level(f"Defining {label}", 5),
        Level(f"Primary {label}", 4),
        Level(f"Significant {label}", 3),
        Level(f"Present {label}", 2),
        Level(f"Occasional {label}", 1),
        Level(f"Negligible {label}", 0),
    ]


MAX_DURATION_LEVELS = [
    Level("Contains Massive Sustained Notes (>= 4 Bars)", 8),
    Level("Contains Long Sustained Notes (3-4 Bars)", 7),
    Level("Contains Long Sustained Notes (2-3 Bars)", 6),
    Level("Contains Sustained Notes (1-2 Bars)", 5),
    Level("Max Sustain 1/2-1 Bar", 4),
    Level("Max Sustain 1/4-1/2 Bar", 3),
    Level("Max Sustain 1/8-1/4 Bar", 2),
    Level("Max Sustain < 1/8 Bar", 1),
]

DURATION_BINS = [
    ("32nd", "duration_pct_32nd_range"),
    ("16th", "duration_pct_16th_range"),
    ("8th", "duration_pct_8th_range"),
    ("quarter", "duration_pct_quarter_range"),
    ("half", "duration_pct_half_range"),
    ("whole", "duration_pct_whole_range"),
    ("above_whole", "duration_pct_above_whole_range"),
]

BIN_DISPLAY = {
    "32nd": "32nd",
    "16th": "16th",
    "8th": "8th",
    "quarter": "Quarter",
    "half": "Half",
    "whole": "Whole",
    "above_whole": "Above Whole",
}

MACRO_BUCKET_MAP = {
    "short": ["32nd", "16th", "8th"],
    "medium": ["quarter", "half"],
    "long": ["whole", "above_whole"],
}

MACRO_DISPLAY = {
    "short": "Short Duration",
    "medium": "Medium Duration",
    "long": "Long Duration",
}

MACRO_USE = {
    "short": "staccato / plucks",
    "medium": "moderate note lengths",
    "long": "sustained / pads",
}


def compute_raw_features(midi, notes) -> dict:
    if not notes:
        return empty_raw_features()

    bps = get_bps(midi)
    events = group_notes_into_events(notes, bps)
    durations_whole = _event_durations(events, bps)
    profile = _calc_duration_profile(durations_whole)

    results = {"duration_max_length_beats": round(_calc_max_duration_beats(durations_whole), 3)}

    for macro, bins in MACRO_BUCKET_MAP.items():
        total = sum(profile.get(f"duration_pct_{b}_range", 0.0) for b in bins)
        results[f"duration_{macro}_profile"] = round(total, 2)

    for bin_name, key in DURATION_BINS:
        results[f"duration_{bin_name}_share"] = profile.get(key, 0.0)

    return results


def empty_raw_features() -> dict:
    results = {"duration_max_length_beats": 0.0}
    for macro in MACRO_BUCKET_MAP:
        results[f"duration_{macro}_profile"] = 0.0
    for bin_name, key in DURATION_BINS:
        results[f"duration_{bin_name}_share"] = 0.0
    return results


def _macro_concept(macro: str) -> Concept:
    label = MACRO_DISPLAY[macro]
    levels = _shareholder_levels(label)
    bins = MACRO_BUCKET_MAP[macro]
    bin_display = ", ".join(f"{b}" for b in bins)
    return Concept(
        name=f"duration_{macro}_profile",
        category="rhythm",
        family=["pitched"],
        levels=levels,
        quantizer=ShareholderQuantizer(
            levels=levels,
            thresholds=SHAREHOLDER_THRESHOLDS,
        ),
        description=f"Sum of the {bin_display} note duration bins.",
        llm_description=f"Sum of the {bin_display} note duration bins (how long notes are held/sustained).",
        llm_interpretation=f"Aggregate of the {bin_display} duration bins. Use for {MACRO_USE[macro]}.",
        llm_examples=[
            "most notes are sustained a long time" if macro == "long" else
            "overall note durations are short staccato" if macro == "short" else
            "note lengths are moderate",
        ],
        llm_level_descriptions={
            **{
                level.name: f"{level.name.split(' ', 1)[0]} share of the loop is {macro}-range duration (>= {SHAREHOLDER_THRESHOLDS[i]}%)."
                for i, level in enumerate(levels[:-1])
            },
            levels[-1].name: f"Negligible {macro}-range duration occurs (share below {SHAREHOLDER_THRESHOLDS[-2]}%).",
        },
        llm_subcategory="duration",
        scope="summary",
    )


def _bin_concept(bin_name: str, key: str) -> Concept:
    display = BIN_DISPLAY[bin_name]
    label = f"{display} Note Duration"
    levels = _shareholder_levels(label)
    BIN_EXAMPLES = {
        "32nd": "notes are very short 32nd note bursts",
        "16th": "note lengths around a 16th note",
        "8th": "each note lasts an eighth note",
        "quarter": "notes sustain for a quarter note",
        "half": "notes are held for a half note",
        "whole": "notes sustain a full whole note",
        "above_whole": "notes sustain longer than a measure",
    }
    return Concept(
        name=f"duration_{bin_name}_share",
        category="rhythm",
        family=["pitched"],
        levels=levels,
        quantizer=ShareholderQuantizer(
            levels=levels,
            thresholds=SHAREHOLDER_THRESHOLDS,
        ),
        description=f"Share of {display} note durations.",
        llm_description=f"Percentage of note sustain lengths that are {display} note durations.",
        llm_interpretation=f"Use for exact articulation queries. 'Staccato' or 'plucks' map to short durations; 'sustained pads' or 'held chords' map to long durations. {display} duration = notes sustain at the {display} note value.",
        llm_examples=[BIN_EXAMPLES.get(bin_name, f"{display.lower()} duration")],
        llm_level_descriptions={
            **{
                level.name: (
                    f"{display} note duration is the dominant sustain length, making up 75% or more of total sustained time."
                    if i == 0
                    else f"{display} note duration makes up {SHAREHOLDER_THRESHOLDS[i]}%–{SHAREHOLDER_THRESHOLDS[i-1]}% of total sustained time."
                )
                for i, level in enumerate(levels[:-1])
            },
            levels[-1].name: f"Negligible {display} note duration occurs (share below {SHAREHOLDER_THRESHOLDS[-2]}%).",
        },
        llm_subcategory="duration",
        scope="summary",
    )


class DurationExtractor(FeatureExtractor):
    def __init__(self):
        summary_concepts = [_macro_concept(macro) for macro in ("short", "medium", "long")]
        detail_concepts = [_bin_concept(bin_name, key) for bin_name, key in DURATION_BINS]

        max_duration = Concept(
            name="duration_max_length_beats",
            category="rhythm",
            family=["pitched"],
            levels=MAX_DURATION_LEVELS,
            quantizer=TieredQuantizer(
                thresholds=[16.0, 8.0, 6.0, 4.0, 2.0, 1.0, 0.5],
                levels=MAX_DURATION_LEVELS,
            ),
            description="Length of the longest sustained event in quarter-note beats.",
            llm_description="Longest single note duration in the file.",
            llm_interpretation="Use for 'sustained chords' or 'pads' vs 'staccato' or 'plucks'. This is the longest single sustained event in the file — it is a ceiling on the maximal note length. It can be used to enforce that no note ever goes above a certain duration ('no note longer than X'). Note: the longest sustain reaching somewhere says nothing about the other notes — they can be almost as long, slightly shorter, extremely short, or any mixture of these and anything in between. Do NOT use this to fulfill a specific 'no X sustains' negation (e.g. 'no half-note sustains', 'no eighth-note sustains') — a ceiling at X also excludes everything longer (X AND above), which is broader than the user asked; use the matching share bin (e.g. duration_half_share, duration_8th_share) with its 'No X' negation level instead.",
            llm_examples=["the longest note is very extended", "no note longer than a quarter", "all notes are short"],
            llm_level_descriptions={},
            llm_subcategory="duration",
            scope="summary",
        )

        super().__init__(
            "duration",
            [max_duration, *summary_concepts, *detail_concepts],
            llm_description="Duration measures how long notes are held or ring.",
            llm_subcategory="duration",
        )

    def extract(self, midi_data) -> dict:
        return compute_raw_features(midi_data.midi, midi_data.notes)

    def _empty_profile(self) -> dict:
        return empty_raw_features()


def _event_durations(events, bps: float) -> list[float]:
    durations = []
    for group in events:
        start_beat = min(_note_attr(n, "start") for n in group) * bps
        end_beat = max(_note_attr(n, "end") for n in group) * bps
        durations.append((end_beat - start_beat) / 4.0)
    return durations


def _calc_max_duration_beats(durations: list[float]) -> float:
    if not durations:
        return 0.0
    return float(np.max(durations)) * 4.0


def _calc_duration_profile(durations: list[float]) -> dict[str, float]:
    clean = [d for d in durations if d > 0.01]
    total_time = sum(clean)
    if total_time == 0:
        return {key: 0.0 for _, key in DURATION_BINS}

    weights = {
        "xxs": 0.0,
        "xs": 0.0,
        "s": 0.0,
        "m": 0.0,
        "l": 0.0,
        "xl": 0.0,
        "xxl": 0.0,
    }
    for d in clean:
        if d <= 0.04:
            weights["xxs"] += d
        elif d <= 0.075:
            weights["xs"] += d
        elif d <= 0.15:
            weights["s"] += d
        elif d <= 0.35:
            weights["m"] += d
        elif d <= 0.75:
            weights["l"] += d
        elif d <= 1.25:
            weights["xl"] += d
        else:
            weights["xxl"] += d

    return {
        "duration_pct_32nd_range": round((weights["xxs"] / total_time) * 100.0, 2),
        "duration_pct_16th_range": round((weights["xs"] / total_time) * 100.0, 2),
        "duration_pct_8th_range": round((weights["s"] / total_time) * 100.0, 2),
        "duration_pct_quarter_range": round((weights["m"] / total_time) * 100.0, 2),
        "duration_pct_half_range": round((weights["l"] / total_time) * 100.0, 2),
        "duration_pct_whole_range": round((weights["xl"] / total_time) * 100.0, 2),
        "duration_pct_above_whole_range": round((weights["xxl"] / total_time) * 100.0, 2),
    }
