import numpy as np

from midi_analyzer_tagger.core import Concept, FeatureExtractor, Level
from midi_analyzer_tagger.extractors.temporal_events_helper import get_bps, group_notes_into_events
from midi_analyzer_tagger.quantizers import TieredQuantizer

AVERAGE_EVENTS_LEVELS = [
    Level("Frantic", 6),
    Level("Busy", 5),
    Level("Moderately (not too) Busy", 4),
    Level("Moderately (not too) Sparse", 3),
    Level("Sparse", 2),
    Level("Minimalist/Drone-like", 1),
]

BURSTINESS_LEVELS = [
    Level("Volatile Density", 4),
    Level("Variable Density", 3),
    Level("Steady Density", 2),
    Level("Uniform Density", 1),
]

EVOLUTION_LEVELS = [
    Level("Volatile Bar Event Density", 4),
    Level("Variable Bar Event Density", 3),
    Level("Lightly Varying Bar Event Density", 2),
    Level("Constant Bar Event Density", 1),
]

TURNAROUND_LEVELS = [
    Level("Turnaround Fill", 3),
    Level("No Turnaround", 2),
    Level("Turnaround Dropout", 1),
]

TREND_LEVELS = [
    Level("Rising Density / Speeding Up", 3),
    Level("Steady Density", 2),
    Level("Falling Density / Slowing Down", 1),
]


RHYTHMIC_DENSITY_DESCRIPTION = "Average attack rate, clustering, and how density changes over time."


def compute_raw_features(midi, notes) -> dict:
    if not notes:
        return empty_raw_features()

    bps = get_bps(midi)
    events = group_notes_into_events(notes, bps)

    return {
        "rhythmic_density_average_events_per_beat": round(calc_event_density(events, bps), 2),
        "rhythmic_density_burstiness": round(calc_density_volatility(events, bps), 2),
        "rhythmic_density_bar_to_bar_evolution": round(calc_macro_variation(events, bps), 2),
        "rhythmic_density_turnaround_shift": round(calc_turnaround_spike(events, bps), 2),
        "rhythmic_density_trend": round(calc_energy_contour(events, bps), 2),
    }


def empty_raw_features() -> dict:
    return {key: 0.0 for key in [
        "rhythmic_density_average_events_per_beat",
        "rhythmic_density_burstiness",
        "rhythmic_density_bar_to_bar_evolution",
        "rhythmic_density_turnaround_shift",
        "rhythmic_density_trend",
    ]}


class RhythmicDensityExtractor(FeatureExtractor):
    def __init__(self):
        concepts = [
            Concept(
                name="rhythmic_density_average_events_per_beat",
                category="rhythm",
                family=["pitched"],
                levels=AVERAGE_EVENTS_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[4.0, 2.0, 1.0, 0.5, 0.25],
                    levels=AVERAGE_EVENTS_LEVELS,
                ),
                description="Average event density (attacks per beat).",
                llm_description="Average number of events (attack groups) per beat.",
                llm_interpretation="Use for queries about overall rhythmic activity or busyness. Choose a level matching how dense and active the rhythm feels — from a relentless, hyper-active stream down to a near-static drone. Avoid referencing note-value speeds here (that belongs to spacing).",
                llm_examples=["very busy frantic rhythm", "sparse minimalist feel", "driving constant rhythm"],
                llm_level_descriptions={
                    "Frantic": "Relentless, hyper-active stream of events. Rapid, bubbling, almost overwhelming.",
                    "Busy": "Dense, driving activity with continuous forward momentum.",
                    "Moderately (not too) Busy": "Steady, moderate activity — clearly active but not crowded.",
                    "Moderately (not too) Sparse": "Light activity — sparse, individual events carry weight.",
                    "Sparse": "Minimal notes with high negative space.",
                    "Minimalist/Drone-like": "Very few events, near-static or droning.",
                },
                llm_subcategory="rhythmic density",
                scope="summary",
            ),
            Concept(
                name="rhythmic_density_burstiness",
                category="rhythm",
                family=["pitched"],
                levels=BURSTINESS_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[1.4, 0.9, 0.5],
                    levels=BURSTINESS_LEVELS,
                ),
                description="How peaky vs even the density is — whether some beats spike well above the overall level.",
                llm_description="How peaky vs even the density is.",
                llm_interpretation="Use for queries about even vs bursty density. Low = beats are fairly even, no part stands out. High = some beats are much denser than the rest — bursts, rolls, or fill peaks that punch above the baseline. This measures how much the busiest part exceeds the overall density, not the average count itself.",
                llm_examples=["steady even density", "a big burst or fill peak", "mostly even with one dense spike"],
                llm_level_descriptions={
                    "Volatile Density": "A burst or fill clearly spikes above the rest of the loop.",
                    "Variable Density": "Noticeable bursts above a steady baseline.",
                    "Steady Density": "Fairly even — mild peaks around a consistent baseline.",
                    "Uniform Density": "Very even — nothing stands out much (locked, metronomic).",
                },
                llm_subcategory="rhythmic density",
                scope="summary",
            ),
            Concept(
                name="rhythmic_density_bar_to_bar_evolution",
                category="rhythm",
                family=["pitched"],
                levels=EVOLUTION_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[0.45, 0.25, 0.05],
                    levels=EVOLUTION_LEVELS,
                ),
                description="Coefficient of variation in event density from bar to bar.",
                llm_description="How much the event density varies across bars.",
                llm_interpretation="Use for queries about variation vs steadiness across the loop. Low = density is consistent from bar to bar (steady, loop-like). High = density varies noticeably across bars — some busier, some sparser — suggesting an evolving, breathing, or fill-heavy part rather than a static loop. This measures how spread out the density is across bars; the direction of change (building vs fading) is the separate 'trend' feature. The final (turnaround) bar is handled separately, not by this metric.",
                llm_examples=["rhythm changes drastically from bar to bar", "steady consistent loop", "pattern evolves over time"],
                llm_level_descriptions={
                    "Volatile Bar Event Density": "Drastically different each bar — unstable, fill-heavy, or chaotic.",
                    "Variable Bar Event Density": "Noticeable changes from bar to bar — an evolving or breathing pattern.",
                    "Lightly Varying Bar Event Density": "Minor, subtle changes bar to bar.",
                    "Constant Bar Event Density": "Very steady, loop-like — locked, consistent repetition.",
                },
                llm_subcategory="rhythmic density",
                scope="summary",
            ),
            Concept(
                name="rhythmic_density_turnaround_shift",
                category="rhythm",
                family=["pitched"],
                levels=TURNAROUND_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[0.4, -0.5],
                    levels=TURNAROUND_LEVELS,
                ),
                description="End-of-loop fill or dropout compared to the preceding bars.",
                llm_description="Directional shift at loop boundaries.",
                llm_interpretation="Positive means a fill/transition/roll into the next bar (energy builds at the turnaround); negative means a dropout or breakdown at the boundary (the part pulls back before looping).",
                llm_examples=["a fill at the end of the phrase", "a dropout at the loop ending", "a turnaround at the bar line"],
                llm_level_descriptions={
                    "Turnaround Fill": "Activity increases at the end — a fill or roll leads into the next bar.",
                    "No Turnaround": "Consistent through the boundary — an even, continuous loop.",
                    "Turnaround Dropout": "Activity decreases at the end — a break or pull-back at the boundary.",
                },
                llm_subcategory="rhythmic density",
                scope="summary",
            ),
            Concept(
                name="rhythmic_density_trend",
                category="rhythm",
                family=["pitched"],
                levels=TREND_LEVELS,
                quantizer=TieredQuantizer(
                    thresholds=[0.5, -0.5],
                    levels=TREND_LEVELS,
                ),
                description="Overall density trend from start to end of the loop.",
                llm_description="Direction of density change over time.",
                llm_interpretation="Use for whether density rises or falls across the loop. Higher rhythmic density means a faster-feeling, busier activity (for any tempo); lower means sparser, slower. Positive = density trends upward toward the end (busier / speeding up). Negative = density trends downward toward the end (sparser / slowing down). Near zero = density stays roughly stable throughout.",
                llm_examples=["density rises toward the end", "activity fades towards the end", "getting busier over time"],
                llm_level_descriptions={
                    "Rising Density / Speeding Up": "Density trends upward — the part gets busier toward the end.",
                    "Steady Density": "No clear trend — density stays roughly even throughout.",
                    "Falling Density / Slowing Down": "Density trends downward — the part gets sparser toward the end.",
                },
                llm_subcategory="rhythmic density",
                scope="summary",
            ),
        ]
        super().__init__(
            "rhythmic_density",
            concepts,
            llm_description=RHYTHMIC_DENSITY_DESCRIPTION,
            llm_subcategory="rhythmic density",
        )

    def extract(self, midi_data) -> dict:
        return compute_raw_features(midi_data.midi, midi_data.notes)

    def _empty_profile(self) -> dict:
        return empty_raw_features()


def _get_binned_densities(events, bps, bin_size_beats=4.0, span="start"):
    if not events:
        return []

    event_start_beats = [g[0]["start"] * bps for g in events]
    if span == "end":
        # Base the bar grid on the last note END so a trailing bar that has no
        # onsets (only a ringing note, or the loop's final bar) is still counted
        # (as 0). Otherwise the "last bar" collapses to the last populated bar.
        last_beat = max(n["end"] for g in events for n in g) * bps
    else:
        last_beat = max(event_start_beats)
    total_bins = int(np.ceil(last_beat / bin_size_beats))
    if total_bins <= 0:
        return [0]

    counts = [0] * total_bins
    for start_beat in event_start_beats:
        b_idx = int(start_beat // bin_size_beats)
        if b_idx < total_bins:
            counts[b_idx] += 1

    return counts


def calc_event_density(events, bps):
    if not events:
        return 0.0

    last_end_beat = max(
        max(note["end"] for note in group) for group in events
    ) * bps
    return len(events) / max(last_end_beat, 1.0)


def calc_density_volatility(events, bps):
    counts = _get_binned_densities(events, bps, 1.0)
    if not counts:
        return 0.0

    max_density = np.max(counts)
    mean_density = np.mean(counts)
    burst_magnitude = max_density - mean_density

    return round(float(burst_magnitude), 3)


def calc_macro_variation(events, bps):
    bar_counts = _get_binned_densities(events, bps, 4.0, span="end")

    if len(bar_counts) > 2:
        bar_counts = bar_counts[:-1]

    num_bars = len(bar_counts)
    total_events = sum(bar_counts)

    if num_bars < 2 or total_events == 0:
        return 0.0

    if total_events <= num_bars:
        return 0.0

    variation = np.std(bar_counts) / (np.mean(bar_counts) + 1e-6)

    return round(float(variation), 3)


def calc_turnaround_spike(events, bps):
    bar_counts = _get_binned_densities(events, bps, 4.0, span="end")
    if len(bar_counts) < 2:
        return 0.0

    last_bar = bar_counts[-1]
    avg_prev = np.mean(bar_counts[:-1])

    if avg_prev == 0:
        return 1.0 if last_bar > 0 else 0.0

    diff = last_bar - avg_prev
    max_val = max(last_bar, avg_prev)

    return float(diff / max_val) if max_val > 0 else 0.0


def calc_energy_contour(events, bps):
    beat_counts = _get_binned_densities(events, bps, 1.0)
    if len(beat_counts) < 3 or sum(beat_counts) == 0:
        return 0.0

    x = np.arange(len(beat_counts))
    y = np.array(beat_counts)

    if np.std(y) == 0:
        return 0.0

    corr = np.corrcoef(x, y)[0, 1]

    return round(float(np.nan_to_num(corr, nan=0.0)), 3)
