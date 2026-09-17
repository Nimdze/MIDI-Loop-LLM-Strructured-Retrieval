"""Custom plain-language feature explanations for the validation UI.

These override the taxonomy's ``llm.interpretation``/``description`` (which are
written for the LLM, not for human evaluators). Keyed by the *base* feature name
(pitched concept). Drum concepts (``drum_<family>_<base>``) reuse the base text
with a kit-piece prefix. Any concept without a custom entry falls back to the
taxonomy text.
"""

from __future__ import annotations

from typing import Any

DRUM_FAMILIES = {
    "drum_kick_": "the kick",
    "drum_snare_clap_": "the snare/clap",
    "drum_hats_cymbals_": "the hats/cymbals",
    "drum_toms_others_": "the toms/others",
}

CUSTOM: dict[str, str] = {
    # rhythmic density
    "rhythmic_density_average_events_per_beat": (
        "The average amount of events per bar, where an event is one or more notes "
        "played at roughly the same time. Denser = faster (given a fixed tempo). "
        "Because it is an average, a fast burst (e.g. 16ths) in the last bar after "
        "slower bars (e.g. whole notes) can score roughly the same as a more evenly "
        "distributed file (e.g. quarters throughout)."
    ),
    "rhythmic_density_burstiness": (
        "Low = beats are fairly even, no part stands out. High = at least one beat "
        "is much denser than the rest — bursts, rolls, or fill peaks that punch above "
        "the baseline. This measures how much the busiest part exceeds the overall "
        "density, not the average count itself. It doesn't distinguish between one "
        "or more bursts — it just indicates some exist."
    ),
    "rhythmic_density_bar_to_bar_evolution": (
        "How much the density (the number of events per bar, where an event is one or "
        "more notes played at roughly the same time) varies across the bars of the "
        "loop — excluding the last bar. Low = density is consistent from bar to bar "
        "(steady, loop-like). High = density varies noticeably across bars — some "
        "busier, some sparser — suggesting an evolving, breathing, or fill-heavy part "
        "rather than a static loop. This feature covers all bars except the last; the "
        "final (turnaround) bar is handled separately by the 'turnaround' feature, and "
        "the direction of change (building vs fading) is the separate 'trend' feature."
    ),
    "rhythmic_density_turnaround_shift": (
        "The density (number of events) of the final bar compared with the rest of "
        "the loop — how much it speeds up or slows down at the turnaround. Positive "
        "= a fill/transition/roll into the next bar (energy builds at the turnaround; "
        "the last bar speeds up with more events). Negative = a dropout or breakdown "
        "at the boundary (the part pulls back before looping; the last bar slows down "
        "with fewer events). This looks at the last bar only — the earlier bars are "
        "covered by the 'bar-to-bar evolution' feature."
    ),
    # spacing / duration (shares)
    "spacing_quarter_share": (
        "Percentage of event onset gaps that are roughly Quarter note spacing."
    ),
    "duration_half_share": (
        "Percentage of note sustain lengths that are roughly Half note durations."
    ),
    # dynamics
    "dynamics_average_velocity": (
        "Use this for the baseline loudness of the performance — 'loud', 'soft', "
        "'aggressive', or 'gentle'. Velocity is a proxy for loudness in MIDI. This is "
        "the overall effort level, distinct from accents or dynamic variation. Because "
        "it is an average, it does not tell how the velocity is distributed around the "
        "average — a uniformly loud file and one with loud peaks but quiet dips could "
        "share the same average."
    ),
    # tonality
    "tonality_prevalent_pitch_pct": (
        "Use this for how stable and focused the tonal center is. Strongly "
        "anchor-centered = a clear, drone-like tonal center; loosely following = some "
        "center but not dominant; straying = ambiguous or wandering tonality. "
        "Concretely, it measures the percentage of notes that belong to the most "
        "prevalent pitch class in the file."
    ),
    # melodic intervals (percentages are out of the total melodic interval count)
    "profile_melodic_intervals_pct_asc_7_semitones": (
        "The percentage of ascending perfect 5ths (7-semitone) intervals out of the "
        "file's total melodic interval count."
    ),
    "profile_melodic_intervals_pct_desc_1_semitones": (
        "The percentage of descending minor 2nds (1-semitone) intervals out of the "
        "file's total melodic interval count."
    ),
    "profile_melodic_intervals_pct_asc_13plus_semitones": (
        "The percentage of ascending intervals beyond an octave (13+ semitones) out "
        "of the file's total melodic interval count."
    ),
    "profile_melodic_intervals_pct_static": (
        "The percentage of static (same-note, 0-semitone) intervals out of the file's "
        "total melodic interval count."
    ),
    "melodic_intervals_pct_descending": (
        "The percentage of descending melodic intervals out of the file's total "
        "melodic interval count."
    ),
    "melodic_interval_vocabulary_count": (
        "The number of different unique interval sizes used in the melody — a "
        "narrow/focused palette vs. a diverse one."
    ),
    "melodic_intervals_absolute_median_semitones": (
        "The median interval size of melodic motion (the 'middle' interval, so rare "
        "extreme leaps don't skew it the way a plain average would) — stepwise/small "
        "vs. leaping/large."
    ),
    # register
    "register_lowest_note_midi": (
        "The lowest note in the file. Note: where the lowest note sits doesn't "
        "necessarily say anything about the other notes — a file can dip down once "
        "and otherwise sit much higher."
    ),
    # harmonic intervals
    "profile_harmonic_intervals_pct_15_semitones": (
        "The percentage of vertical (chord-tone) intervals that are a minor tenth "
        "(15 semitones, an octave plus a minor third) out of the file's total "
        "vertical interval count."
    ),
    "harmonic_dissonance_pct": (
        "How much the harmony uses dissonant intervals — an aggregate of the "
        "dissonant interval shares (tritones, sevenths, seconds, etc.)."
    ),
    # texture
    "texture_pct_1_notes": (
        "The percentage of active timesteps containing exactly one note — the share "
        "of the file that is monophonic (only one note playing at a time)."
    ),
    "texture_pct_2_notes": (
        "The percentage of active timesteps containing exactly two notes — the share "
        "that is dyadic (two notes at a time)."
    ),
    "texture_pct_6plus_notes": (
        "The percentage of active timesteps containing six or more notes — the share "
        "that has 6+ notes at a time."
    ),
    "texture_polyphonic_pct": (
        "The percentage of the file that is polyphonic (3+ notes at a time) — an "
        "aggregate of the 3-, 4-, 5-, and 6+-note shares."
    ),
    "texture_mono_vs_chords_register": (
        "Where the single-note line sits relative to the chords: above, within, or "
        "below, and how far. Far Above/Below = an octave or more off the chords' "
        "median pitch. This is the 2-hand signature — a line clearly above the "
        "chords is a right-hand melody, clearly below is a left-hand/bass line, and "
        "overlapping is a line woven into the texture. Only meaningful when both a "
        "single-note line and chords are present."
    ),
    # drum prevalence (percentage of that piece's note onsets out of the whole kit)
    "drum_prevalence_kick_kick_2": (
        "How prominent the Kick 2 is — the percentage of all drum onsets that are Kick 2."
    ),
    "drum_prevalence_snare_clap_snare_1": (
        "How prominent the Snare 1 is — the percentage of all drum onsets that are Snare 1."
    ),
    "drum_prevalence_hats_cymbals_open_hat": (
        "How prominent the Open Hat is — the percentage of all drum onsets that are Open Hat."
    ),
    "drum_prevalence_toms_others_hi_mid_tom": (
        "How prominent the Hi-Mid Tom is — the percentage of all drum onsets that are Hi-Mid Tom."
    ),
}

# Metric-type note appended to all features in a family (validation UI only).
METRIC_NOTES = {
    "duration": "time-based — therefore longer durations last more time, so the metric is biased toward them",
    "spacing": "count-based — therefore shorter spacings are counted more times, so the metric is biased toward them",
}

# Family-level caveats applied by concept prefix (validation UI only).
MELODIC_CAVEAT = (
    "To see their effect clearly, combine with a high texture_1_notes share or a low "
    "texture_polyphonic_pct — they are much easier to observe on monophonic lines."
)
HARMONIC_CAVEAT = (
    "For a clearer view, combine with a high texture_polyphonic_pct."
)

# Per-feature caveats appended to the explanation (validation UI only).
CAVEATS: dict[str, str] = {
    "groove_macro_jitter": (
        "Caution: quantization in many datasets may crush this metric — making all "
        "(or the overwhelming majority of) files land on approximately the same level."
    ),
    "groove_micro_jitter": (
        "Caution: quantization in many datasets may crush this metric — making all "
        "(or the overwhelming majority of) files land on approximately the same level."
    ),
    "texture_polyphonic_burst_rate": (
        "Best observed at a mid texture_polyphonic_pct level."
    ),
    "texture_polyphonic_burst_mean_duration_beats": (
        "Best observed at a mid texture_polyphonic_pct level."
    ),
    "texture_mono_vs_chords_register": (
        "Best observed at a mid texture_polyphonic_pct level (2-hand cases)."
    ),
    "texture_polyphonic_pct": (
        "The polyphonic burst features are best observed at a mid level of this feature."
    ),
}


def feature_explanation(taxonomy: dict[str, Any], concept: str) -> str | None:
    """Return a custom explanation if available, else the taxonomy text."""
    base, prefix = concept, None
    for fam, family in DRUM_FAMILIES.items():
        if concept.startswith(fam):
            base, prefix = concept[len(fam):], family
            break
    text = CUSTOM.get(base)
    if text is None:
        # For drum concepts, base IS the pitched concept name (family prefix
        # stripped), so this routes exactly to the pitched feature's explanation.
        data = (taxonomy.get(base, {}) or {}).get("llm", {}) or {}
        text = data.get("interpretation") or data.get("description")
    if prefix and text:
        text = f"For {prefix}: {text}"

    note = None
    if base.startswith("duration_"):
        note = METRIC_NOTES["duration"]
    elif base.startswith("spacing_"):
        note = METRIC_NOTES["spacing"]
    if note:
        text = (f"{text} " if text else "") + f"*(Metric: {note}.)*"

    caveats: list[str] = []
    if base.startswith("melodic_") or base.startswith("profile_melodic_intervals_pct_"):
        caveats.append(MELODIC_CAVEAT)
    elif base.startswith("harmonic_") or base.startswith("profile_harmonic_intervals_pct_"):
        caveats.append(HARMONIC_CAVEAT)
    specific = CAVEATS.get(base)
    if specific:
        caveats.append(specific)
    for cav in caveats:
        text = (f"{text} " if text else "") + f"_{cav}_"
    return text
