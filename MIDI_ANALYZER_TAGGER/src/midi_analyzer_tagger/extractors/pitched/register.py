import numpy as np
from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps
from midi_analyzer_tagger.quantizers import TieredQuantizer

PITCH_LEVELS = [
    Level("Register: Air", 7),
    Level("Register: High", 6),
    Level("Register: Upper-Mid", 5),
    Level("Register: Mid", 4),
    Level("Register: Low-Mid", 3),
    Level("Register: Bass", 2),
    Level("Register: Sub-Bass", 1),
]

PITCH_THRESHOLDS = [84.0, 72.0, 60.0, 50.0, 40.0, 28.0]

PITCH_LEVEL_DESCRIPTIONS = {
    "Register: Air": "Very high, shimmering register — MIDI 84+ (C6 and above).",
    "Register: High": "High register — MIDI 72–83 (C5–B5).",
    "Register: Upper-Mid": "Upper mid register — MIDI 60–71 (C4–B4).",
    "Register: Mid": "Mid register — MIDI 50–59 (D3–B3).",
    "Register: Low-Mid": "Low mid register — MIDI 40–49 (E2–C#3).",
    "Register: Bass": "Bass register — MIDI 28–39 (E1–D#2).",
    "Register: Sub-Bass": "Deep sub-bass register — MIDI < 28 (below E1).",
}

SPREAD_LEVELS = [
    Level("Wide Pitch Spread (3+ Octaves)", 3),
    Level("Medium Pitch Spread (1-3 Octaves)", 2),
    Level("Compact Pitch Range (< 1 Octave)", 1),
]

SPREAD_THRESHOLDS = [36.0, 12.0]

SHIFT_LEVELS = [
    Level("Active Register Migration", 3),
    Level("Moderate Register Migration", 2),
    Level("Stable", 1),
]

SHIFT_THRESHOLDS = [12.0, 5.0]


class RegisterExtractor(FeatureExtractor):
    def __init__(self):
        concepts = [
            Concept(
                name="register_lowest_note_midi",
                category="voicing",
                family=["pitched"],
                levels=PITCH_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=PITCH_THRESHOLDS,
                    levels=PITCH_LEVELS,
                ),
                description="Lowest MIDI pitch in the loop.",
                llm_description="Register band of the lowest note in the loop.",
                llm_interpretation="Use this with 'register_median_note_midi' and 'register_highest_note_midi' to map the vertical placement and bottom of the material. A very low floor anchors the part in deep or sub-bass territory.",
                llm_examples=["dropping to deep bass notes", "sinking into the sub-bass", "anchored low in the range"],
                llm_level_descriptions=PITCH_LEVEL_DESCRIPTIONS,
                llm_subcategory="register",
                scope="summary",
                llm_bin_family="register_band",
                llm_bin_label="lowest",
            ),
            Concept(
                name="register_highest_note_midi",
                category="voicing",
                family=["pitched"],
                levels=PITCH_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=PITCH_THRESHOLDS,
                    levels=PITCH_LEVELS,
                ),
                description="Highest MIDI pitch in the loop.",
                llm_description="Register band of the highest note in the loop.",
                llm_interpretation="Use this with 'register_lowest_note_midi' and 'register_median_note_midi' to map the vertical placement and ceiling of the material. A very high ceiling peaks into bright, airy treble.",
                llm_examples=["reaching the soprano range", "peaking into the high treble", "touching the airy top register"],
                llm_level_descriptions=PITCH_LEVEL_DESCRIPTIONS,
                llm_subcategory="register",
                scope="summary",
                llm_bin_family="register_band",
                llm_bin_label="highest",
            ),
            Concept(
                name="register_median_note_midi",
                category="voicing",
                family=["pitched"],
                levels=PITCH_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=PITCH_THRESHOLDS,
                    levels=PITCH_LEVELS,
                ),
                description="Median MIDI pitch in the loop.",
                llm_description="Register band of the median pitch in the loop (the central frequency anchor of the material).",
                llm_interpretation="Use this for queries about where the material 'lives' — whether the part sits low, in the middle, or high. This is the most useful single register descriptor for the central placement.",
                llm_examples=["sits in the mid register", "mostly lives in the bass register", "centered in the upper-mid register"],
                llm_level_descriptions=PITCH_LEVEL_DESCRIPTIONS,
                llm_subcategory="register",
                scope="summary",
                llm_bin_family="register_band",
                llm_bin_label="median",
            ),
            Concept(
                name="register_spread_semitones",
                category="voicing",
                family=["pitched"],
                levels=SPREAD_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=SPREAD_THRESHOLDS,
                    levels=SPREAD_LEVELS,
                ),
                description="Total pitch span from the lowest to highest note.",
                llm_description="Total pitch range from lowest to highest note.",
                llm_interpretation="Use this for 'focused range' (compact) vs 'wide range' or 'orchestral'. This is the absolute span from the lowest to highest note — driven by the extremes, so a single outlier can widen it. A compact range is a tight motif; a wide range sweeps across many octaves.",
                llm_examples=["very narrow focused range", "wide spread across many octaves", "compact limited register"],
                llm_level_descriptions={
                    "Wide Pitch Spread (3+ Octaves)": "Very wide — spans 3 octaves or more (sweeping, technical).",
                    "Medium Pitch Spread (1-3 Octaves)": "Standard width — spans 1 to just under 3 octaves (vocal-like, natural).",
                    "Compact Pitch Range (< 1 Octave)": "Tight — spans less than 1 octave (constrained motif).",
                },
                llm_subcategory="register",
                scope="summary",
            ),
            Concept(
                name="register_boundary_shift_semitones",
                category="voicing",
                family=["pitched"],
                levels=SHIFT_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=SHIFT_THRESHOLDS,
                    levels=SHIFT_LEVELS,
                ),
                description="How far the central register moves between the first and second halves of the loop.",
                llm_description="How far the central register shifts between the first and second halves of the loop.",
                llm_interpretation="Use this for 'register shift' or 'moving range'. Migration means the part's central register moves up or down between the first and second halves of the loop.",
                llm_examples=["register shifts dramatically", "pitch range moves upward", "expanding range over time"],
                llm_level_descriptions={
                    "Active Register Migration": "The central register shifts by an octave or more — the part clearly migrates up or down.",
                    "Moderate Register Migration": "The central register shifts noticeably (a perfect fourth to just under an octave).",
                    "Stable": "The central register stays put — a consistent register throughout.",
                },
                llm_subcategory="register",
                scope="summary",
            ),
        ]
        super().__init__(
            "register",
            concepts,
            llm_description="Register describes the frequency range of the material: the central register, the total span, and how it moves over time.",
            llm_subcategory="register",
        )

    def extract(self, midi_data) -> dict:
        notes = midi_data.notes
        pitches = [n["pitch"] for n in notes]

        if not pitches:
            return {
                "register_lowest_note_midi": 0,
                "register_highest_note_midi": 0,
                "register_median_note_midi": 0,
                "register_spread_semitones": 0.0,
                "register_boundary_shift_semitones": 0.0,
            }

        low = int(min(pitches))
        high = int(max(pitches))
        median = int(np.round(np.median(pitches)))
        spread = int(high - low)
        shift = calc_range_stability(notes, midi_data.midi)

        return {
            "register_lowest_note_midi": low,
            "register_highest_note_midi": high,
            "register_median_note_midi": median,
            "register_spread_semitones": spread,
            "register_boundary_shift_semitones": shift,
        }


def calc_range_stability(notes, midi) -> float:
    if len(notes) < 2:
        return 0.0

    bps = get_bps(midi)
    start_beat = min(n["start"] for n in notes) * bps
    end_beat = max(n["end"] for n in notes) * bps
    midpoint_beat = start_beat + (end_beat - start_beat) / 2.0

    first_half = [n["pitch"] for n in notes if n["start"] * bps < midpoint_beat]
    second_half = [n["pitch"] for n in notes if n["start"] * bps >= midpoint_beat]

    if not first_half or not second_half:
        return 0.0

    # Central-register migration: how far the median pitch moves between the two
    # halves. Median is robust to single outlier notes (unlike floor/ceiling).
    return float(abs(float(np.median(first_half)) - float(np.median(second_half))))
