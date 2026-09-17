import numpy as np

from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps, group_notes_into_events
from midi_analyzer_tagger.quantizers import ContinuousQuantizer, TieredQuantizer

VELOCITY_LEVELS = [
    Level("Hard/Aggressive Velocity", 4),
    Level("Balanced / Mixed Velocity", 3),
    Level("Soft Velocity", 2),
    Level("Ghost/Whisper Velocity", 1),
]

ACCENT_LEVELS = [
    Level("Contains Dynamic Accents", 2),
    Level("No Dynamic Accents", 1),
]

VARIANCE_LEVELS = [
    Level("Wide Dynamic Range", 3),
    Level("Natural Dynamic Variance", 2),
    Level("Flat/Programmed Dynamics", 1),
]

TREND_LEVELS = [
    Level("Building Intensity", 3),
    Level("Stable Intensity", 2),
    Level("Fading Intensity", 1),
]

MAX_VELOCITY_LEVEL = Level("Maximum Velocity", 1)


def compute_raw_features(midi, notes) -> dict:
    if not notes:
        return empty_raw_features()

    bps = get_bps(midi)
    events = group_notes_into_events(notes, bps)
    velocities = [n["velocity"] for n in notes]

    avg_velocity = round(float(np.mean(velocities)), 2)
    max_velocity = int(np.max(velocities))
    velocity_spread = round(float(np.std(velocities)), 2) if len(velocities) > 1 else 0.0
    intensity_trend = round(_calc_intensity_trend(events, bps), 2)

    return {
        "dynamics_average_velocity": avg_velocity,
        "dynamics_accents_presence": max_velocity - avg_velocity,
        "dynamics_velocity_spread": velocity_spread,
        "dynamics_intensity_trend": intensity_trend,
        "dynamics_max_velocity": max_velocity,
    }


def empty_raw_features() -> dict:
    # No notes -> no velocity: None so no dynamics tag is assigned (a no-note
    # file must NOT be tagged as "Ghost/Whisper Velocity", which a 0.0 average
    # would map to).
    return {
        "dynamics_average_velocity": None,
        "dynamics_accents_presence": None,
        "dynamics_velocity_spread": None,
        "dynamics_intensity_trend": None,
        "dynamics_max_velocity": None,
    }


class DynamicsExtractor(FeatureExtractor):
    def __init__(self):
        concepts = [
            Concept(
                name="dynamics_average_velocity",
                category="dynamics",
                family=["pitched"],
                levels=VELOCITY_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[95.0, 60.0, 30.0],
                    levels=VELOCITY_LEVELS,
                ),
                description="Average MIDI velocity mapped to intensity tiers.",
                llm_description="Overall loudness/effort from average MIDI velocity.",
                llm_interpretation="Use this for the baseline loudness of the performance — 'loud', 'soft', 'aggressive', or 'gentle'. Velocity is a proxy for loudness in MIDI. This is the overall effort level, distinct from accents or dynamic variation.",
                llm_examples=["the whole performance is very loud and aggressive", "very quiet and gentle throughout", "medium-level consistent volume"],
                llm_level_descriptions={
                    "Hard/Aggressive Velocity": "Consistently loud and aggressive.",
                    "Balanced / Mixed Velocity": "Moderate, balanced loudness.",
                    "Soft Velocity": "Consistently soft/quiet.",
                    "Ghost/Whisper Velocity": "Very soft, whisper-quiet.",
                },
                llm_subcategory="dynamics",
                scope="summary",
            ),
            Concept(
                name="dynamics_accents_presence",
                category="dynamics",
                family=["pitched"],
                levels=ACCENT_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[25.0],
                    levels=ACCENT_LEVELS,
                ),
                description="Whether a note stands out clearly louder than the overall average (loudest note vs average).",
                llm_description="Whether there are accent peaks — notes clearly louder than the overall average.",
                llm_interpretation="Use for 'accented' or 'emphasized'. Detects whether any notes are notably louder than the overall average — pronounced peaks that stand out. It reflects the presence of such peaks, not how many (could be one or several); a file with accent peaks and a file with many accents both read as containing accents.",
                llm_examples=["there are strong accent hits that stand out", "some notes pop much louder than the rest", "no real accents, even loudness"],
                llm_level_descriptions={
                    "Contains Dynamic Accents": "There are notes much louder than the overall average — loud peaks stand out.",
                    "No Dynamic Accents": "No note is much louder than the overall average — velocity is relatively even.",
                },
                llm_subcategory="dynamics",
                scope="summary",
            ),
            Concept(
                name="dynamics_velocity_spread",
                category="dynamics",
                family=["pitched"],
                levels=VARIANCE_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[25.0, 8.0],
                    levels=VARIANCE_LEVELS,
                ),
                description="Velocity standard deviation mapped to variance tiers.",
                llm_description="Dynamic range/variation in velocity.",
                llm_interpretation="Use this for the dynamic range or expressiveness — 'expressive', 'dynamic', or 'flat/consistent'. Wide range = the notes vary a lot in loudness (expressive); flat = very consistent (steady or programmed).",
                llm_examples=["the dynamics have a very wide range", "very expressive with big loud-soft contrasts", "flat consistent loudness throughout"],
                llm_level_descriptions={
                    "Wide Dynamic Range": "Highly varied loudness — very expressive, wide dynamic contrast.",
                    "Natural Dynamic Variance": "Natural, moderate variation in loudness.",
                    "Flat/Programmed Dynamics": "Very consistent loudness — flat or programmed.",
                },
                llm_subcategory="dynamics",
                scope="summary",
            ),
            Concept(
                name="dynamics_intensity_trend",
                category="dynamics",
                family=["pitched"],
                levels=TREND_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[45.0, -45.0],
                    levels=TREND_LEVELS,
                ),
                description="Difference between average impact of the second and first half of the loop.",
                llm_description="Whether overall intensity (loudness × how many notes sound together) rises or falls across the loop.",
                llm_interpretation="Use for 'building' or 'fading'. Compares the average event impact (total velocity of notes sounding together) between the second and first halves of the loop. Positive = the second half is louder/more impactful (a build-up); negative = quieter/sparser (a fade-out); near zero = similar. For a 4- or 8-bar loop, the two halves give a good sense of the overall trend. It reflects both loudness and how many notes sound together.",
                llm_examples=["the volume increases gradually through the track", "gets quieter toward the end", "intensity stays steady"],
                llm_level_descriptions={
                    "Building Intensity": "The second half is notably louder/more impactful than the first half — a build-up.",
                    "Stable Intensity": "Loudness and impact stay similar between the halves — steady.",
                    "Fading Intensity": "The second half is quieter/sparser than the first half — a fade-out.",
                },
                llm_subcategory="dynamics",
                scope="summary",
            ),
            Concept(
                name="dynamics_max_velocity",
                category="dynamics",
                family=["pitched"],
                levels=[MAX_VELOCITY_LEVEL],
                quantizer=ContinuousQuantizer([(float("inf"), MAX_VELOCITY_LEVEL)]),
                description="Highest MIDI velocity in the loop (raw detail stat).",
                llm_description="Highest single velocity value in the loop.",
                llm_examples=["the single loudest peaks at maximum velocity"],
                llm_subcategory="dynamics",
                scope="detail",
                default_weight=0.0,
            ),
        ]
        super().__init__(
            "dynamics",
            concepts,
            llm_description="Dynamics measure loudness, accents, dynamic range, and velocity trends over time.",
            llm_subcategory="dynamics",
        )

    def extract(self, midi_data) -> dict:
        return compute_raw_features(midi_data.midi, midi_data.notes)

    def _empty_profile(self) -> dict:
        return empty_raw_features()


def _calc_intensity_trend(events, bps: float) -> float:
    if len(events) < 4:
        return 0.0

    event_times = []
    event_impacts = []
    for group in events:
        start = min(n["start"] for n in group)
        event_times.append(start * bps)
        event_impacts.append(sum(n["velocity"] for n in group))

    midpoint = (event_times[-1] + event_times[0]) / 2.0
    first = [v for t, v in zip(event_times, event_impacts) if t <= midpoint]
    second = [v for t, v in zip(event_times, event_impacts) if t > midpoint]
    if not first or not second:
        return 0.0

    return float(np.mean(second) - np.mean(first))
