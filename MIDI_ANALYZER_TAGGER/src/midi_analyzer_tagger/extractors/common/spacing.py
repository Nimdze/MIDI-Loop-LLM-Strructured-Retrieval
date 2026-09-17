import numpy as np

from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps, group_notes_into_events
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


MAX_SILENCE_LEVELS = [
    Level("Massive Max Silence (>= 4 Bars)", 8),
    Level("Long Max Silence (3-4 Bars)", 7),
    Level("Long Max Silence (2-3 Bars)", 6),
    Level("Long Max Silence (1-2 Bars)", 5),
    Level("Moderate Max Silence (1/2-1 Bars)", 4),
    Level("Short Max Silence 1/4-1/2 Bar", 3),
    Level("Short Max Silence 1/8-1/4 Bar", 2),
    Level("Short Max Silence < 1/8 Bar", 1),
]

GAP_BINS = [
    ("32nd", "spacing_pct_32nd_range"),
    ("16th", "spacing_pct_16th_range"),
    ("8th", "spacing_pct_8th_range"),
    ("quarter", "spacing_pct_quarter_range"),
    ("half", "spacing_pct_half_range"),
    ("whole", "spacing_pct_whole_range"),
    ("above_whole", "spacing_pct_above_whole_range"),
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

MACRO_EXAMPLES = {
    "short": "the general onset spacing profile is short and compact",
    "medium": "the gaps between attacks are moderate in length",
    "long": "the general onset spacing profile is long and spread out",
}

GAP_BIN_EXAMPLES = {
    "32nd": "notes cluster at the 32nd note level",
    "16th": "steady 16th note spacing between attacks",
    "8th": "attacks land on every eighth note",
    "quarter": "notes are spaced a quarter note apart",
    "half": "attacks every half note creating an open feel",
    "whole": "whole note gap between each attack",
    "above_whole": "gaps longer than a whole measure",
}
MACRO_BUCKET_MAP = {
    "short": ["32nd", "16th", "8th"],
    "medium": ["quarter", "half"],
    "long": ["whole", "above_whole"],
}

MACRO_DISPLAY = {
    "short": "Short Spacing",
    "medium": "Medium Spacing",
    "long": "Long Spacing",
}

MACRO_USE = {
    "short": "tight / driving",
    "medium": "moderate gaps",
    "long": "wide / open",
}


def compute_raw_features(midi, notes) -> dict:
    if not notes:
        return empty_raw_features()

    bps = get_bps(midi)
    events = group_notes_into_events(notes, bps)
    profile = _calc_gap_profile(events, bps)

    results = {"spacing_max_silence_beats": _calc_max_silence(events, bps)}

    for macro, bins in MACRO_BUCKET_MAP.items():
        total = sum(profile.get(f"spacing_pct_{b}_range", 0.0) for b in bins)
        results[f"spacing_{macro}_profile"] = round(total, 2)

    for bin_name, key in GAP_BINS:
        results[f"spacing_{bin_name}_share"] = profile.get(key, 0.0)

    return results


def empty_raw_features() -> dict:
    results = {"spacing_max_silence_beats": 0.0}
    for macro in MACRO_BUCKET_MAP:
        results[f"spacing_{macro}_profile"] = 0.0
    for bin_name, key in GAP_BINS:
        results[f"spacing_{bin_name}_share"] = 0.0
    return results


def _macro_concept(macro: str) -> Concept:
    label = MACRO_DISPLAY[macro]
    levels = _shareholder_levels(label)
    bins = MACRO_BUCKET_MAP[macro]
    bin_display = ", ".join(f"{b}" for b in bins)
    return Concept(
        name=f"spacing_{macro}_profile",
        category="rhythm",
        family=["pitched"],
        levels=levels,
        quantizer=ShareholderQuantizer(
            levels=levels,
            thresholds=SHAREHOLDER_THRESHOLDS,
        ),
        description=f"Sum of the {bin_display} note spacing bins.",
        llm_description=f"Sum of the {bin_display} note spacing bins (distance between note starts).",
        llm_interpretation=f"Aggregate of the {bin_display} spacing bins (how far apart onsets start). Use for {MACRO_USE[macro]}. Note: a gap between onsets doesn't tell you whether notes ring through that gap — combine with the duration histogram for that.",
        # Examples: user-type queries for each concept
        llm_examples=[MACRO_EXAMPLES.get(macro, f"{macro} spacing")],
        llm_level_descriptions={
            **{
                level.name: f"{level.name.split(' ', 1)[0]} share of the loop is {macro}-range spacing (>= {SHAREHOLDER_THRESHOLDS[i]}%)."
                for i, level in enumerate(levels[:-1])
            },
            levels[-1].name: f"Negligible {macro}-range spacing occurs (share below {SHAREHOLDER_THRESHOLDS[-2]}%).",
        },
        llm_subcategory="spacing",
        scope="summary",
    )


def _bin_concept(bin_name: str, key: str) -> Concept:
    display = BIN_DISPLAY[bin_name]
    label = f"{display} Note Spacing"
    levels = _shareholder_levels(label)
    return Concept(
        name=f"spacing_{bin_name}_share",
        category="rhythm",
        family=["pitched"],
        levels=levels,
        quantizer=ShareholderQuantizer(
            levels=levels,
            thresholds=SHAREHOLDER_THRESHOLDS,
        ),
        description=f"Share of {display} note spacing.",
        llm_description=f"Percentage of note gaps that are {display} note spacing.",
        llm_interpretation=f"Use for exact subdivision queries about the spacing between note starts (the 'motor'). Example: '8th note piano runs' should target a high value here. {display} spacing = the dominant gap between attacks lands at the {display} note value. '16th/32nd' = very tight, dense spacing; 'quarter/half/whole' = wide, open spacing.",
        # Examples: user-type queries for each concept
        llm_examples=[GAP_BIN_EXAMPLES.get(bin_name, f"{display.lower()} note spacing")],
        llm_level_descriptions={
            **{
                level.name: (
                    f"{display} note spacing is the dominant gap size, making up 75% or more of gaps."
                    if i == 0
                    else f"{display} note spacing makes up {SHAREHOLDER_THRESHOLDS[i]}%–{SHAREHOLDER_THRESHOLDS[i-1]}% of gaps."
                )
                for i, level in enumerate(levels[:-1])
            },
            levels[-1].name: f"Negligible {display} note spacing occurs (share below {SHAREHOLDER_THRESHOLDS[-2]}%).",
        },
        llm_subcategory="spacing",
        scope="detail",
    )


class SpacingExtractor(FeatureExtractor):
    def __init__(self):
        summary_concepts = [_macro_concept(macro) for macro in ("short", "medium", "long")]
        detail_concepts = [_bin_concept(bin_name, key) for bin_name, key in GAP_BINS]

        max_silence = Concept(
            name="spacing_max_silence_beats",
            category="rhythm",
            family=["pitched"],
            levels=MAX_SILENCE_LEVELS,
            quantizer=TieredQuantizer(
                thresholds=[16.0, 8.0, 6.0, 4.0, 2.0, 1.0, 0.5],
                levels=MAX_SILENCE_LEVELS,
            ),
            description="Longest gap between any two consecutive notes in beats.",
            llm_description="Longest continuous silence in the loop.",
            llm_interpretation="Use for queries about breaks, pauses, rests, or negative space. This is the longest continuous period of true silence (dead air) — where no notes ring — NOT the gap between onsets (which the spacing histogram measures regardless of whether notes sustain through the gap). It is a ceiling on the maximal silence: it can be used to limit silence to at most a certain length, and (being a maximum) it says nothing about the length of the silence parts below it — they can be close to the max or much shorter. Works for both long-silence and little-or-no-silence queries.",
            # Examples: user-type queries for each concept
        llm_examples=["a long break with nothing ringing", "tight continuous sound with no real silence", "a big dead-air gap in the middle"],
            llm_level_descriptions={},
            llm_subcategory="spacing",
            scope="summary",
        )

        super().__init__(
            "spacing",
            [max_silence, *summary_concepts, *detail_concepts],
            llm_description="Spacing measures the distance (gaps) between event onsets.",
            llm_subcategory="spacing",
        )

    def extract(self, midi_data) -> dict:
        return compute_raw_features(midi_data.midi, midi_data.notes)

    def _empty_profile(self) -> dict:
        return empty_raw_features()


def _calc_max_silence(events, bps: float) -> float:
    if not events:
        return 0.0

    times = []
    for group in events:
        start = min(n["start"] for n in group) * bps
        end = max(n["end"] for n in group) * bps
        times.append((start, end))

    silences = [times[0][0]]
    current_end = times[0][1]
    for start, end in times[1:]:
        if start > current_end:
            silences.append(start - current_end)
        if end > current_end:
            current_end = end

    loop_boundary = max(4.0, np.ceil((current_end - 0.01) / 4.0) * 4.0)
    silences.append(max(0.0, loop_boundary - current_end))

    return round(float(np.max(silences)), 3)


def _calc_gap_profile(events, bps: float) -> dict[str, float]:
    if len(events) < 2:
        return {key: 0.0 for _, key in GAP_BINS}

    event_starts = [min(n["start"] for n in group) * bps for group in events]
    gaps = np.diff(event_starts)
    gaps = gaps[gaps > 0.05]
    total = len(gaps)
    if total == 0:
        return {key: 0.0 for _, key in GAP_BINS}

    return {
        "spacing_pct_32nd_range": round(np.sum(gaps < 0.18) / total * 100, 2),
        "spacing_pct_16th_range": round(np.sum((gaps >= 0.18) & (gaps < 0.35)) / total * 100, 2),
        "spacing_pct_8th_range": round(np.sum((gaps >= 0.35) & (gaps < 0.75)) / total * 100, 2),
        "spacing_pct_quarter_range": round(np.sum((gaps >= 0.75) & (gaps < 1.5)) / total * 100, 2),
        "spacing_pct_half_range": round(np.sum((gaps >= 1.5) & (gaps < 3.0)) / total * 100, 2),
        "spacing_pct_whole_range": round(np.sum((gaps >= 3.0) & (gaps < 5.0)) / total * 100, 2),
        "spacing_pct_above_whole_range": round(np.sum(gaps >= 5.0) / total * 100, 2),
    }
