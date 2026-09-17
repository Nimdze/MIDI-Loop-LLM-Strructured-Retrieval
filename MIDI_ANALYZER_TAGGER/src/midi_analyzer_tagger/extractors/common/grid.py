import numpy as np

from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps, group_notes_into_events
from midi_analyzer_tagger.quantizers import ContinuousQuantizer, ShareholderQuantizer, TieredQuantizer

TOTAL_EVENTS_LEVELS = [
    Level("Has Events", 1),
    Level("No Events", 0),
]

SWING_LEVELS = [
    Level("Heavy Swing / Shuffle", 3),
    Level("Light Swing / Shuffle", 2),
    Level("Straight (Even Subdivisions)", 1),
]

JITTER_16TH_LEVELS = [
    Level("Loose Macro Pocket", 2),
    Level("Organic Macro Pocket", 1),
    Level("Tight Macro Pocket", 0),
]

JITTER_32ND_LEVELS = [
    Level("Loose Micro Execution", 2),
    Level("Organic Micro Execution", 1),
    Level("Tight Micro Execution", 0),
]

ATTEMPT_LEVELS = [
    Level("High Attempts", 4),
    Level("Moderate Attempts", 3),
    Level("Low Attempts", 2),
    Level("Very Low Attempts", 1),
    Level("Negligible Attempts", 0),
]

ATTEMPT_THRESHOLDS = [75.0, 40.0, 15.0, 1.0, 0.0]

SUCCESS_LEVELS = [
    Level("High Success", 4),
    Level("Moderate Success", 3),
    Level("Low Success", 2),
    Level("Very Low Success", 1),
]

SUCCESS_THRESHOLDS = [75.0, 50.0, 25.0, 0.0]

GRID_POSITIONS = [
    ("odd1", "odd-bar downbeats"),
    ("even1", "even-bar downbeats"),
    ("beat3", "beat three"),
    ("2and4", "backbeats two and four"),
    ("offbeat", "eighth-note upbeats"),
]


GRID_ATTEMPT_LABELS = {
    "odd1": "the odd bar downbeat is hit consistently",
    "even1": "the even bar downbeat is attacked regularly",
    "beat3": "beat three receives a strong attack",
    "2and4": "the two and four positions are attacked very consistently",
    "offbeat": "the offbeat upbeats are accented regularly",
}

GRID_SUCCESS_LABELS = {
    "odd1": "the odd bar downbeats are landed perfectly",
    "even1": "the even bar downbeats are accurate",
    "beat3": "each beat three lands on the grid",
    "2and4": "the two and four positions land with perfect accuracy",
    "offbeat": "every offbeat lands in the pocket",
}


def compute_raw_features(midi, notes) -> dict:
    if not notes:
        return empty_raw_features()

    bps = get_bps(midi)
    events = group_notes_into_events(notes, bps)
    total_events = len(events)

    ticks_per_beat = midi.resolution
    beats = np.array([midi.time_to_tick(g[0]["start"]) / ticks_per_beat for g in events])
    ts_num = midi.time_signature_changes[0].numerator if midi.time_signature_changes else 4

    results = {
        "groove_total_events": total_events,
        **calc_humanization_jitter(beats),
        **calc_grid_metrics(beats, ts_num),
    }

    if total_events >= 4:
        results["groove_swing_shuffle_ratio"] = calc_swing_shuffle_ratio(beats)
    else:
        results["groove_swing_shuffle_ratio"] = 1.0

    return results


def empty_raw_features() -> dict:
    empty = {
        "groove_total_events": 0,
        "groove_swing_shuffle_ratio": 1.0,
        "grid_macro_jitter": None,
        "grid_micro_jitter": None,
    }
    for key, _ in GRID_POSITIONS:
        empty[f"grid_attempt_pct_{key}"] = None
        empty[f"grid_success_pct_{key}"] = None
    return empty


class GridExtractor(FeatureExtractor):
    def __init__(self):
        concepts = [
            Concept(
                name="groove_total_events",
                category="rhythm",
                family=["pitched"],
                levels=TOTAL_EVENTS_LEVELS,
                quantizer=ContinuousQuantizer(
                    [(0, TOTAL_EVENTS_LEVELS[1]), (float("inf"), TOTAL_EVENTS_LEVELS[0])]
                ),
                description="Total number of unique rhythmic events.",
                scope="detail",
                default_weight=0.0,
            ),
            Concept(
                name="groove_swing_shuffle_ratio",
                default_weight=0.0,
                category="rhythm",
                family=["pitched"],
                levels=SWING_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[1.5, 1.15],
                    levels=SWING_LEVELS,
                ),
                description="Straight vs. swung feel derived from inter-onset interval ratios.",
                llm_description="Swing or shuffle feel from adjacent note timing ratios.",
                llm_interpretation="Use for 'swing'/'shuffle' vs. 'straight'. Measures how unevenly adjacent note-spacings divide the beat — the ratio of the larger to the smaller of each neighboring gap pair. Ratio ~1 = even, straight subdivisions. Ratio > 1 = an alternating long-short (or short-long) division, i.e. a swung/shuffled feel. Higher ratio = more pronounced swing. It indicates the magnitude of swing, not the exact musical interval behind it.",
                    llm_examples=["the rhythm has a pronounced swing feel", "a straight locked feel", "a subtle shuffle groove"],
                llm_level_descriptions={
                    "Heavy Swing / Shuffle": "Pronounced swing — adjacent spacings alternate strongly (ratio >= 1.5).",
                    "Light Swing / Shuffle": "Subtle swing — mild long-short alternation (ratio 1.15 to < 1.5).",
                    "Straight (Even Subdivisions)": "Even, straight subdivisions (ratio < 1.15).",
                },
                llm_subcategory="groove",
                scope="summary",
            ),
            Concept(
                name="grid_macro_jitter",
                category="rhythm",
                family=["pitched"],
                levels=JITTER_16TH_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[0.6, 0.25],
                    levels=JITTER_16TH_LEVELS,
                ),
                description="Average deviation from a strict 16th-note grid.",
                llm_description="Macro timing feel at the 16th-note level — execution quality.",
                llm_interpretation="Use to indicate how far the 16th-note timing deviates from a strict grid — i.e. whether the execution is tight/locked or loose. Low jitter = notes land very close to the 16th grid (tight, clean). High jitter = notes drift noticeably off the grid. This drift could come from a deliberate layback or push, or from less precise/sloppy playing; the metric reflects the magnitude of the deviation but does not distinguish between layback, push, and slop. It captures the overall timing deviation at the 16th-note level.",
                llm_examples=["the timing is very tight and locked", "loose timing that drifts", "sloppy playing", "very cleanly played"],
                llm_level_descriptions={
                    "Loose Macro Pocket": "Timing drifts noticeably off the 16th grid — loose, imprecise execution.",
                    "Organic Macro Pocket": "Timing has subtle natural variation around the 16th grid.",
                    "Tight Macro Pocket": "Timing stays very close to the 16th grid — locked, clean execution.",
                },
                llm_subcategory="grid",
                scope="summary",
            ),
            Concept(
                name="grid_micro_jitter",
                category="rhythm",
                family=["pitched"],
                levels=JITTER_32ND_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[0.6, 0.25],
                    levels=JITTER_32ND_LEVELS,
                ),
                description="Average deviation from a strict 32nd-note micro-grid.",
                llm_description="Micro timing feel at the 32nd-note level — humanization of a tight groove.",
                llm_interpretation="Fine timing deviation from the 32nd grid — how precisely onsets land within a 16th. Low = rigidly on a 32nd grid (machine-like / quantized). Higher = more natural, humanized feel. Because these are small deviations, they generally register as organic humanization rather than slop; sloppiness becomes apparent mainly with larger deviations or at slower tempos. Best read together with macro jitter: if macro is low (correct 16th placement), this captures the humanized vs machine-like character.",
                llm_examples=["humanized natural feel", "organic slightly varied micro timing", "robotic machine-like precision", "crisp but subtly human"],
                llm_level_descriptions={
                    "Loose Micro Execution": "More human, organic micro timing — subtly varied but still correct.",
                    "Organic Micro Execution": "Slight humanization on the micro grid. Natural, subtle.",
                    "Tight Micro Execution": "Machine-like, rigidly precise micro timing — fully quantized.",
                },
                llm_subcategory="grid",
                scope="summary",
            ),
        ]

        for key, description in GRID_POSITIONS:
            attempt_name = f"grid_attempt_pct_{key}"
            success_name = f"grid_success_pct_{key}"
            concepts.append(
                Concept(
                    name=attempt_name,
                    category="rhythm",
                    family=["pitched"],
                    levels=ATTEMPT_LEVELS,
                    quantizer=ShareholderQuantizer(
                        levels=ATTEMPT_LEVELS,
                        thresholds=ATTEMPT_THRESHOLDS,
                    ),
                    description=f"Percentage of {description} positions with an attempt.",
                    llm_description=f"How often the {description} position is attacked.",
                    llm_interpretation="Use for rhythm patterns. Attempt = how often the position is PLAYED (independent of accuracy). Example: 'four-on-the-floor' needs high attempts on downbeats; 'backbeat snare' needs high attempts on beats 2 and 4. Always consider this with the paired success concept.",
                    llm_examples=[GRID_ATTEMPT_LABELS.get(key, f"hits the {description.lower()} frequently")],
                    llm_level_descriptions={
                        "High Attempts": "75-100% of positions attacked. Consistent, anchoring presence.",
                        "Moderate Attempts": "40-74% of positions attacked. Active but not constant.",
                        "Low Attempts": "15-39% of positions attacked. Light, occasional presence.",
                        "Very Low Attempts": "1-14% of positions attacked. Rare.",
                        "Negligible Attempts": "0% of positions attacked. Never played.",
                    },
                    llm_subcategory="grid",
                    scope="summary",
                    pair_with=success_name,
                    pair_role="attempt",
                )
            )
            concepts.append(
                Concept(
                    name=success_name,
                    category="rhythm",
                    family=["pitched"],
                    levels=SUCCESS_LEVELS,
                    quantizer=ShareholderQuantizer(
                        levels=SUCCESS_LEVELS,
                        thresholds=SUCCESS_THRESHOLDS,
                    ),
                    description=f"Percentage of {description} attempts that land accurately.",
                    llm_description=f"How accurately the {description} position is landed when attempted.",
                    llm_interpretation="Success = how accurately the played attempts land ON the grid. High success means the attacked position is tight; low success means the attempts are scattered/sloppy. Consider with the paired attempt concept: 'nails it' = high attempt + high success; 'hits but misses' = high attempt + low success.",
                    llm_examples=[GRID_SUCCESS_LABELS.get(key, f"lands the {description.lower()} perfectly")],
                    llm_level_descriptions={
                        "High Success": "75-100% of attempts land accurately. Tight, on the grid.",
                        "Moderate Success": "50-74% of attempts land accurately. Decent, slightly loose.",
                        "Low Success": "25-49% of attempts land accurately. Loose, sloppy.",
                        "Very Low Success": "0-24% of attempts land accurately. Scattered, imprecise.",
                    },
                    llm_subcategory="grid",
                    scope="summary",
                    pair_with=attempt_name,
                    pair_role="success",
                )
            )

        super().__init__(
            "grid",
            concepts,
            llm_description="Grid measures timing accuracy — beat-position alignment and overall timing feel.",
            llm_subcategory="grid",
        )

    def extract(self, midi_data) -> dict:
        return compute_raw_features(midi_data.midi, midi_data.notes)

    def _empty_profile(self) -> dict:
        return empty_raw_features()


def calc_grid_metrics(beats, ts_num=4):
    if len(beats) == 0:
        return {
            "grid_attempt_pct_odd1": None,
            "grid_success_pct_odd1": None,
            "grid_attempt_pct_even1": None,
            "grid_success_pct_even1": None,
            "grid_attempt_pct_beat3": None,
            "grid_success_pct_beat3": None,
            "grid_attempt_pct_2and4": None,
            "grid_success_pct_2and4": None,
            "grid_attempt_pct_offbeat": None,
            "grid_success_pct_offbeat": None,
        }

    beats_arr = np.asarray(beats)
    max_beat = np.max(beats_arr) if len(beats_arr) > 0 else 0
    bars = max(1, int(np.ceil((max_beat - 0.25) / ts_num)))
    if bars == 3:
        bars = 4
    elif 4 < bars < 8:
        bars = 8
    elif 8 < bars < 16:
        bars = 16

    ATTEMPT_WINDOW = 0.3
    SUCCESS_WINDOW = 0.03125

    def analyze_grid_position(targets_per_bar, bar_indices=None, min_attempts=2, use_loose_success=False):
        success_window = 0.0625 if use_loose_success else SUCCESS_WINDOW

        if bar_indices is None:
            bar_indices = list(range(bars))

        all_targets = []
        for bar in bar_indices:
            bar_start = bar * ts_num
            for t in targets_per_bar:
                target_pos = bar_start + t
                if target_pos <= max_beat + ts_num:
                    all_targets.append(target_pos)

        if len(all_targets) == 0:
            return None, None

        all_targets = np.array(all_targets)
        total_positions = len(all_targets)

        attempts = 0
        successes = 0

        for target in all_targets:
            distances = np.abs(beats_arr - target)
            min_dist = np.min(distances)
            if min_dist <= ATTEMPT_WINDOW:
                attempts += 1
                if min_dist <= success_window:
                    successes += 1

        attempt_pct = (attempts / total_positions) * 100.0 if total_positions > 0 else 0.0
        success_pct = (successes / attempts) * 100.0 if attempts > 0 else 0.0

        if attempts < min(min_attempts, total_positions):
            attempt_pct = 0.0

        return round(attempt_pct, 2), round(success_pct, 2)

    odd_bar_indices = [b for b in range(bars) if b % 2 == 0]
    even_bar_indices = [b for b in range(bars) if b % 2 == 1]
    beat3_offset = 2.0
    beats2_4_offsets = [1.0, 3.0]
    offbeat_offsets = [float(beat) + 0.5 for beat in range(ts_num)]

    odd1_attempt, odd1_success = analyze_grid_position([0.0], bar_indices=odd_bar_indices, min_attempts=2)
    even1_attempt, even1_success = analyze_grid_position([0.0], bar_indices=even_bar_indices, min_attempts=2)
    beat3_attempt, beat3_success = analyze_grid_position([beat3_offset], bar_indices=list(range(bars)), min_attempts=2)
    beats2_4_attempt, beats2_4_success = analyze_grid_position(
        beats2_4_offsets, bar_indices=list(range(bars)), min_attempts=3
    )
    offbeat_attempt, offbeat_success = analyze_grid_position(
        offbeat_offsets, bar_indices=list(range(bars + 1)), min_attempts=3, use_loose_success=True
    )

    return {
        "grid_attempt_pct_odd1": odd1_attempt,
        "grid_success_pct_odd1": odd1_success,
        "grid_attempt_pct_even1": even1_attempt,
        "grid_success_pct_even1": even1_success,
        "grid_attempt_pct_beat3": beat3_attempt,
        "grid_success_pct_beat3": beat3_success,
        "grid_attempt_pct_2and4": beats2_4_attempt,
        "grid_success_pct_2and4": beats2_4_success,
        "grid_attempt_pct_offbeat": offbeat_attempt,
        "grid_success_pct_offbeat": offbeat_success,
    }


def calc_swing_shuffle_ratio(beats):
    gaps = np.diff(beats)
    valid_gaps = gaps[gaps > 0.01]
    ratios = []

    for i in range(len(valid_gaps) - 1):
        gap_a = valid_gaps[i]
        gap_b = valid_gaps[i + 1]

        if gap_a > 1.5 or gap_b > 1.5:
            continue

        ratio = max(gap_a, gap_b) / min(gap_a, gap_b)
        if ratio <= 3.0:
            ratios.append(ratio)

    return round(float(np.median(ratios)), 2) if ratios else 1.0


def calc_humanization_jitter(beats):
    if len(beats) == 0:
        return {
            "groove_macro_jitter": None,
            "groove_micro_jitter": None,
        }

    err_16 = []
    err_32 = []

    for b in beats:
        rem_16th = b % 0.25
        dist_to_16th = min(rem_16th, 0.25 - rem_16th)
        err_16.append(dist_to_16th / 0.125)

        rem_32nd = b % 0.125
        dist_to_32nd = min(rem_32nd, 0.125 - rem_32nd)
        err_32.append(dist_to_32nd / 0.0625)

    return {
        "grid_macro_jitter": round(float(np.mean(err_16)), 3),
        "grid_micro_jitter": round(float(np.mean(err_32)), 3),
    }
