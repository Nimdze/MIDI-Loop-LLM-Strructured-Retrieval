import numpy as np
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps
from midi_analyzer_tagger.quantizers import ShareholderQuantizer, TieredQuantizer

STEPS_PER_BAR = 128

SHAREHOLDER_THRESHOLDS = [75.0, 50.0, 30.0, 20.0, 5.0, 0.0]

HISTOGRAM_LABELS = {
    "1_notes": "1 Notes",
    "2_notes": "2 Notes",
    "3_notes": "3 Notes",
    "4_notes": "4 Notes",
    "5_notes": "5 Notes",
    "6plus_notes": "6+ Notes",
}

SUMMARY_LABELS = {
    "texture_monophonic_pct": "Monophonic",
    "texture_dyads_pct": "Dyads",
    "texture_polyphonic_pct": "Chordal (3+ Notes)",
}

BURST_RATE_LEVELS = [
    Level("Dense Chordal Hits", 3),
    Level("Moderate Chordal Hits", 2),
    Level("Sparse Chordal Hits", 1),
]

BURST_RATE_THRESHOLDS = [2.0, 0.5]

# Relative position of the single-note (monophonic) line vs the chordal (2+ note)
# content. offset = mono_median_pitch - chord_median_pitch (semitones; positive =
# the mono line is above the chords). Levels run from far-above to far-below.
MONO_VS_CHORDS_LEVELS = [
    Level("Far Above Chords", 5),
    Level("Above Chords", 4),
    Level("Within Chords", 3),
    Level("Below Chords", 2),
    Level("Far Below Chords", 1),
]

MONO_VS_CHORDS_THRESHOLDS = [12.0, 4.0, -4.0, -12.0]

CHORD_DURATION_LEVELS = [
    Level("Sustained Chordal Accents", 3),
    Level("Medium / Mixed Chordal Duration", 2),
    Level("Short/Staccato Chordal Stabs", 1),
]

CHORD_DURATION_THRESHOLDS = [2.0, 0.5]

VOICING_SPREAD_LEVELS = [
    Level("Big Chordal Spread", 3),
    Level("Medium Chordal Spread", 2),
    Level("Small Chordal Spread", 1),
]

VOICING_SPREAD_THRESHOLDS = [1.0, 0.5]

HISTOGRAM_EXAMPLES = {
    "1_notes": "texture is mostly single notes",
    "2_notes": "texture is mostly dyads two notes",
    "3_notes": "chords tend to have three notes",
    "4_notes": "most chords have four notes",
    "5_notes": "five note voicings are common",
    "6plus_notes": "chords with six plus notes",
}

HISTOGRAM_DESCRIPTIONS = {
    "1_notes": "Percentage of active playing timesteps containing strictly one note (Monophonic).",
    "2_notes": "Percentage of active playing timesteps containing exactly two simultaneous notes (Dyads).",
    "3_notes": "Percentage of active playing timesteps containing exactly three simultaneous notes (e.g., Triads).",
    "4_notes": "Percentage of active playing timesteps containing exactly four simultaneous notes (e.g., 7th Chords).",
    "5_notes": "Percentage of active playing timesteps containing exactly five simultaneous notes.",
    "6plus_notes": "Percentage of active playing timesteps containing six or more simultaneous notes (Dense/Clusters).",
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


class TextureExtractor(FeatureExtractor):
    def __init__(self):
        histogram_concepts = [
            Concept(
                name=f"texture_pct_{label}",
                category="voicing",
                family=["pitched"],
                levels=_shareholder_levels(HISTOGRAM_LABELS[label]),
                quantizer=ShareholderQuantizer(
                    levels=_shareholder_levels(HISTOGRAM_LABELS[label]),
                    thresholds=SHAREHOLDER_THRESHOLDS,
                ),
                description=HISTOGRAM_DESCRIPTIONS[label],
                llm_description=(
                    "Percentage of active timesteps containing exactly 1 note."
                    if label == "1_notes"
                    else f"Percentage of active timesteps containing exactly {HISTOGRAM_LABELS[label].lower()}."
                ),
                llm_interpretation="Use this for precise texture queries about how many notes sound at once. 'Mostly triads' = a high share of 3-note voicings; '4-voice chords' = high share of 4-note. Note these are voicings by note count, not implied harmonic function (a 3-note voicing is not necessarily a triad).",
                llm_examples=[HISTOGRAM_EXAMPLES.get(label, f"mostly {HISTOGRAM_LABELS[label].lower()}")],
                llm_level_descriptions={
                    f"Defining {HISTOGRAM_LABELS[label]}": ">= 75% of active timesteps.",
                    f"Primary {HISTOGRAM_LABELS[label]}": ">= 50% of active timesteps.",
                    f"Significant {HISTOGRAM_LABELS[label]}": ">= 30% of active timesteps.",
                    f"Present {HISTOGRAM_LABELS[label]}": ">= 20% of active timesteps.",
                    f"Occasional {HISTOGRAM_LABELS[label]}": ">= 5% of active timesteps.",
                    f"Negligible {HISTOGRAM_LABELS[label]}": "Negligible active timesteps have this many notes.",
                },
                llm_subcategory="texture",
                scope="summary",
                default_weight=1.0,
            )
            for label in HISTOGRAM_LABELS
        ]
        # Adjust scope: 1 and 2 notes = summary, 3+ notes = detail
        for c in histogram_concepts:
            if c.name in ("texture_pct_1_notes", "texture_pct_2_notes"):
                c.scope = "summary"
            else:
                c.scope = "detail"

        profile_summary_concepts = [
            Concept(
                name="texture_polyphonic_pct",
                category="voicing",
                family=["pitched"],
                levels=_shareholder_levels(SUMMARY_LABELS["texture_polyphonic_pct"]),
                quantizer=ShareholderQuantizer(
                    levels=_shareholder_levels(SUMMARY_LABELS["texture_polyphonic_pct"]),
                    thresholds=SHAREHOLDER_THRESHOLDS,
                ),
                description="Percentage of active playing timesteps containing chordal (3+ notes) material.",
                llm_description="Aggregate texture share: Chordal (3+ notes).",
                llm_interpretation="Use for broad texture queries about how much of the material is chordal/polyphonic (3+ notes) vs single-line. A high chordal share means the loop is mostly block chords; a low share means it is mostly monophonic.",
                llm_examples=["chords", "harmonies", "polyphonic"],
                llm_level_descriptions={
                    "Defining Chordal (3+ Notes)": "Chordal material dominates the texture (>= 75%).",
                    "Primary Chordal (3+ Notes)": "Most common texture (>= 50%).",
                    "Significant Chordal (3+ Notes)": "Clearly present (>= 30%).",
                    "Present Chordal (3+ Notes)": "Some presence (>= 20%).",
                    "Occasional Chordal (3+ Notes)": "Light presence (>= 5%).",
                    "Negligible Chordal (3+ Notes)": "No chordal material — the texture is purely single-line or dyads.",
                },
                llm_subcategory="texture",
                scope="summary",
                default_weight=1.0,
            )
        ]

        complementary_concepts = [
            Concept(
                name="texture_polyphonic_burst_rate",
                category="voicing",
                family=["pitched"],
                levels=BURST_RATE_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=BURST_RATE_THRESHOLDS,
                    levels=BURST_RATE_LEVELS,
                ),
                description="Rate of intentional chordal attacks per bar, ignoring release slop.",
                llm_description="How dense the chordal accompaniment is — chord attacks per bar.",
                llm_interpretation="Measures how densely the chordal accompaniment is played. In 2-hand parts (one instrument playing bass+chords or chords+melody), a high rate means busy, rhythmic comping with frequent chord stabs; a low rate means sparse, long-held chordal pads.",
                llm_subcategory="texture",
                scope="detail",
                default_weight=1.0,
                llm_examples=["busy rhythmic chord comping", "chords hit on every beat", "sparse sustained chords"],
                llm_level_descriptions={
                    "Dense Chordal Hits": "Chords struck frequently (>= 2 attacks per bar) — busy, rhythmic accompaniment.",
                    "Moderate Chordal Hits": "Chords struck occasionally (0.5-2 attacks per bar).",
                    "Sparse Chordal Hits": "Chords struck rarely (< 0.5 attacks per bar) — mostly long-held voicings.",
                },
            ),
            Concept(
                name="texture_polyphonic_burst_mean_duration_beats",
                category="voicing",
                family=["pitched"],
                levels=CHORD_DURATION_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=CHORD_DURATION_THRESHOLDS,
                    levels=CHORD_DURATION_LEVELS,
                ),
                description="Average sustain time of polyphonic bursts in beats.",
                llm_description="How long chordal clusters are held on average.",
                llm_interpretation="Tells you whether the chordal accompaniment is held as sustained pads or played as short, rhythmic stabs. In 2-hand parts, long = a sustained chordal backdrop; short = punchy, staccato chord stabs.",
                llm_examples=["very sustained chordal accents", "short stabby chords", "long held pads"],
                llm_level_descriptions={
                    "Sustained Chordal Accents": "Average chord duration >= 2.0 beats (long pads/sustained chords).",
                    "Medium / Mixed Chordal Duration": "Average chord duration 0.5-2.0 beats.",
                    "Short/Staccato Chordal Stabs": "Average chord duration <= 0.5 beats (quick chord hits).",
                },
                llm_subcategory="texture",
                scope="detail",
                default_weight=1.0,
            ),
            
            Concept(
                name="texture_mono_vs_chords_register",
                category="voicing",
                family=["pitched"],
                levels=MONO_VS_CHORDS_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=MONO_VS_CHORDS_THRESHOLDS,
                    levels=MONO_VS_CHORDS_LEVELS,
                ),
                description="Where the single-note line sits relative to the chordal content: above, within, or below the chords, and how far.",
                llm_description="Register of the single-note line relative to the chords.",
                llm_interpretation="Use to identify the 2-hand texture: whether the single-note line sits above, within, or below the chordal (2+ note) accompaniment, and how far. A line clearly above the chords = melody + chords (right-hand lead); a line clearly below = bass + chords (left-hand line); a line overlapping the chords = a line woven within the texture. Only meaningful in 2-hand loops where both a single-note line and chords exist; do not use for purely monophonic or purely chordal loops.",
                llm_subcategory="texture",
                scope="detail",
                default_weight=1.0,
                llm_examples=["a melody line clearly above the chords", "a bass line under the chords", "a line woven within the chords", "a line an octave above the accompaniment"],
                llm_level_descriptions={
                    "Far Above Chords": "Single-note line is an octave or more above the chords' median pitch.",
                    "Above Chords": "Single-note line sits above the chords' median pitch (within about an octave).",
                    "Within Chords": "Single-note line overlaps the chords' pitch range.",
                    "Below Chords": "Single-note line sits below the chords' median pitch (within about an octave).",
                    "Far Below Chords": "Single-note line is an octave or more below the chords' median pitch.",
                },
            ),
            Concept(
                name="texture_avg_wide_gaps_per_burst",
                category="voicing",
                family=["pitched"],
                levels=VOICING_SPREAD_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=VOICING_SPREAD_THRESHOLDS,
                    levels=VOICING_SPREAD_LEVELS,
                ),
                description="Average number of wide intervals (>= 7 semitones) between adjacent notes within each polyphonic burst, averaged across all bursts.",
                llm_description="How spread out the notes in chords are.",
                llm_interpretation="Use for 'open voicings' (wide, airy chord spread) vs 'close voicings' (tight, clustered chords). In 2-hand parts this shows whether the chordal accompaniment is voiced open or close. This is the orchestrational width of the voicings, distinct from how many notes they contain.",
                llm_examples=["wide open chord voicings", "tight close-position chords", "big spread between notes"],
                llm_level_descriptions={
                    "Big Chordal Spread": "Open, wide voicings — a large gap between chord voices (expansive, orchestral).",
                    "Medium Chordal Spread": "Moderately open voicings.",
                    "Small Chordal Spread": "Tight, close-position voicings — voices clustered together.",
                },
                llm_subcategory="texture",
                scope="summary",
                default_weight=1.0,
            ),
        ]

        super().__init__(
            "texture",
            histogram_concepts + profile_summary_concepts + complementary_concepts,
            llm_description="Texture describes the vertical stacking of notes: single-note lines, dyads, chordal voicings, and how spread out the voicings are. The note-count and voicing-spread features cover all loops; the chord-burst (rate/duration), gap-width, and single-note-register features are added specifically to accurately characterize two-handed loops — a single instrument playing bass+chords or chords+melody (common in piano/keys).",
            llm_subcategory="texture",
        )

    def extract(self, midi_data) -> dict:
        return _get_texture(midi_data.notes, midi_data.midi)


def _get_texture(notes, midi):
    if not notes:
        return {
            **_get_density_histogram([]),
            **_get_density_summary([]),
            "texture_mono_vs_chords_register": None,
            "texture_avg_wide_gaps_per_burst": 0.0,
            "texture_polyphonic_burst_rate": 0.0,
            "texture_polyphonic_burst_mean_duration_beats": 0.0,
        }

    bps = get_bps(midi)
    last_end_time = max(note["end"] for note in notes)
    total_bars = (last_end_time * bps) / 4.0

    active_steps = _get_active_grid_steps(notes, bps, STEPS_PER_BAR)

    results = {}
    results.update(_get_density_histogram(active_steps))
    results.update(_get_density_summary(active_steps))
    results.update(_get_mono_vs_chords_register(active_steps))

    poly_bursts, burst_durations, burst_pitches = _get_polyphonic_burst_metrics(active_steps, STEPS_PER_BAR)
    results.update(_get_open_voicing_stats(burst_pitches))

    rate = poly_bursts / total_bars if total_bars > 0 else 0.0
    results["texture_polyphonic_burst_rate"] = round(rate, 2)
    results.update(_get_polyphonic_burst_mean_duration(burst_durations))

    return results


def _get_active_grid_steps(notes, bps, steps_per_bar=128):
    if not notes:
        return []

    steps_per_beat = steps_per_bar / 4.0
    sec_per_step = 1.0 / (bps * steps_per_beat)
    last_end_time = max(note["end"] for note in notes)
    total_steps = int(np.ceil(last_end_time / sec_per_step))

    active_steps = []
    for step in range(total_steps):
        t_center = step * sec_per_step + (sec_per_step / 2.0)
        pitches = [note["pitch"] for note in notes if note["start"] <= t_center and note["end"] > t_center]
        if pitches:
            active_steps.append({
                "step_index": step,
                "pitches": pitches,
                "count": len(pitches),
            })

    return active_steps


def _get_polyphonic_burst_metrics(active_steps, steps_per_bar=128):
    poly_bursts = 0
    burst_durations_beats = []
    burst_pitches = []

    is_poly_active = False
    last_step_index = -2
    current_burst_start = None

    for s in active_steps:
        current_step = s["step_index"]

        if current_step > last_step_index + 1:
            if is_poly_active:
                burst_durations_beats.append(last_step_index - current_burst_start + 1)
            is_poly_active = False

        if s["count"] >= 3:
            if not is_poly_active:
                poly_bursts += 1
                is_poly_active = True
                current_burst_start = current_step
                burst_pitches.append(s["pitches"])
        else:
            if is_poly_active:
                burst_durations_beats.append(last_step_index - current_burst_start + 1)
                is_poly_active = False

        last_step_index = current_step

    if is_poly_active:
        burst_durations_beats.append(last_step_index - current_burst_start + 1)

    steps_per_beat = steps_per_bar / 4.0
    durations_in_beats = [d / steps_per_beat for d in burst_durations_beats]

    return poly_bursts, durations_in_beats, burst_pitches


def _get_density_histogram(active_steps):
    stats = {
        "texture_pct_1_notes": 0.0,
        "texture_pct_2_notes": 0.0,
        "texture_pct_3_notes": 0.0,
        "texture_pct_4_notes": 0.0,
        "texture_pct_5_notes": 0.0,
        "texture_pct_6plus_notes": 0.0,
    }

    total_active = len(active_steps)
    if total_active == 0:
        return stats

    tally = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, "6+": 0}
    for s in active_steps:
        c = s["count"]
        bin_key = c if c <= 5 else "6+"
        tally[bin_key] += 1

    stats["texture_pct_1_notes"] = round((tally[1] / total_active) * 100, 2)
    stats["texture_pct_2_notes"] = round((tally[2] / total_active) * 100, 2)
    stats["texture_pct_3_notes"] = round((tally[3] / total_active) * 100, 2)
    stats["texture_pct_4_notes"] = round((tally[4] / total_active) * 100, 2)
    stats["texture_pct_5_notes"] = round((tally[5] / total_active) * 100, 2)
    stats["texture_pct_6plus_notes"] = round((tally["6+"] / total_active) * 100, 2)

    return stats


def _get_density_summary(active_steps):
    stats = {
        "texture_monophonic_pct": 0.0,
        "texture_dyads_pct": 0.0,
        "texture_polyphonic_pct": 0.0,
    }

    total_active = len(active_steps)
    if total_active == 0:
        return stats

    tally = {"mono": 0, "dyads": 0, "poly": 0}
    for s in active_steps:
        c = s["count"]
        if c == 1:
            tally["mono"] += 1
        elif c == 2:
            tally["dyads"] += 1
        else:
            tally["poly"] += 1

    stats["texture_monophonic_pct"] = round((tally["mono"] / total_active) * 100, 2)
    stats["texture_dyads_pct"] = round((tally["dyads"] / total_active) * 100, 2)
    stats["texture_polyphonic_pct"] = round((tally["poly"] / total_active) * 100, 2)

    return stats


def _get_polyphonic_burst_mean_duration(burst_durations_beats):
    if not burst_durations_beats:
        return {"texture_polyphonic_burst_mean_duration_beats": 0.0}
    return {"texture_polyphonic_burst_mean_duration_beats": round(float(np.mean(burst_durations_beats)), 3)}


def _get_mono_vs_chords_register(active_steps):
    mono_pitches = []
    chord_pitches = []
    for s in active_steps:
        if s["count"] == 1:
            mono_pitches.append(s["pitches"][0])
        elif s["count"] >= 2:
            chord_pitches.extend(s["pitches"])

    if not mono_pitches or not chord_pitches:
        # No mono line, or no chords -> the relative register is undefined.
        return {"texture_mono_vs_chords_register": None}

    mono_median = float(np.median(mono_pitches))
    chord_median = float(np.median(chord_pitches))
    return {"texture_mono_vs_chords_register": round(mono_median - chord_median, 1)}


def _get_open_voicing_stats(burst_pitches):
    if not burst_pitches:
        return {"texture_avg_wide_gaps_per_burst": 0.0}

    total_smart_gaps = 0
    total_bursts = len(burst_pitches)

    for pitches in burst_pitches:
        if len(pitches) < 3:
            continue
        sorted_p = sorted(pitches)
        total_span = max(sorted_p[-1] - sorted_p[0], 1)
        gaps = [sorted_p[i + 1] - sorted_p[i] for i in range(len(sorted_p) - 1)]
        wide_gaps = [g for g in gaps if g >= 7]

        if len(wide_gaps) == 1:
            if (wide_gaps[0] / total_span) < 0.70:
                total_smart_gaps += 1
        else:
            total_smart_gaps += len(wide_gaps)

    return {"texture_avg_wide_gaps_per_burst": round(total_smart_gaps / total_bursts, 2)}
