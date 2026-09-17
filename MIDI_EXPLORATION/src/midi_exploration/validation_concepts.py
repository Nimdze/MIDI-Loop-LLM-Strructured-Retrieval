"""Target-concept selection for feature validation.

The taxonomy repeats a small set of features across kit-piece families and
histogram bins. We validate a hand-curated representative subset.

Curated selection (confirmed with the user):
  - pitched: all features, but grid reduced to ONE position (2&4, attempt+success)
  - drum:    5 concepts (1 prevalence + 4 features, one per subcategory on a
             distinct kit-piece family; no grid)
Metadata concepts are excluded (standard, not our features).

Total 53 concepts; each validated at its two intensity extremes.
"""

from __future__ import annotations

from typing import Any

PITCHED = [
    # rhythmic density: all 5
    "rhythmic_density_average_events_per_beat",
    "rhythmic_density_burstiness",
    "rhythmic_density_bar_to_bar_evolution",
    "rhythmic_density_turnaround_shift",
    "rhythmic_density_trend",
    # spacing: quarter share, short aggregate, max silence
    "spacing_quarter_share",
    "spacing_short_profile",
    "spacing_max_silence_beats",
    # duration: half share, long aggregate, max length
    "duration_half_share",
    "duration_long_profile",
    "duration_max_length_beats",
    # groove: swing, macro jitter, micro jitter (no note count)
    "groove_swing_shuffle_ratio",
    "groove_macro_jitter",
    "groove_micro_jitter",
    # grid: ONE position (2&4 backbeat); success paired automatically
    "grid_attempt_pct_2and4",
    # dynamics: avg, accents, spread, intensity trend (no max velocity)
    "dynamics_average_velocity",
    "dynamics_accents_presence",
    "dynamics_velocity_spread",
    "dynamics_intensity_trend",
    # tonality: all 4
    "tonality_unique_pitches_count",
    "tonality_out_of_key_notes",
    "tonality_prevalent_pitch_pct",
    "tonality_unique_pitches_count_trend",
    # melodic: asc 7st, desc 1st, 13+ asc, static, total desc, seq rep,
    # voc count, abs median, max leap
    "profile_melodic_intervals_pct_asc_7_semitones",
    "profile_melodic_intervals_pct_desc_1_semitones",
    "profile_melodic_intervals_pct_asc_13plus_semitones",
    "profile_melodic_intervals_pct_static",
    "melodic_intervals_pct_descending",
    "melodic_intervals_sequence_repetition_pct",
    "melodic_interval_vocabulary_count",
    "melodic_intervals_absolute_median_semitones",
    "melodic_intervals_max_leap_semitones",
    # register: lowest + median + spread + boundary shift
    "register_lowest_note_midi",
    "register_median_note_midi",
    "register_spread_semitones",
    "register_boundary_shift_semitones",
    # harmonic: P5 (below octave), minor tenth 15st (above octave), dissonance
    "profile_harmonic_intervals_pct_07_semitones",
    "profile_harmonic_intervals_pct_15_semitones",
    "harmonic_dissonance_pct",
    # texture: 1n, 2n, 6+n, polyphonic, wide gaps, burst rate, burst dur, mono-vs-chords
    "texture_pct_1_notes",
    "texture_pct_2_notes",
    "texture_pct_6plus_notes",
    "texture_polyphonic_pct",
    "texture_avg_wide_gaps_per_burst",
    "texture_polyphonic_burst_rate",
    "texture_polyphonic_burst_mean_duration_beats",
    "texture_mono_vs_chords_register",
]

# Drum: one prevalence + 4 features, one per subcategory, each on a distinct
# kit-piece family. The drum-routing methodology is judged once in the write-up;
# the per-feature spot-checks confirm each family's analysis is sane. No grid.
DRUM = [
    "drum_prevalence_kick_kick_2",
    # rhythmic density (average events/beat) on kick
    "drum_kick_rhythmic_density_average_events_per_beat",
    # groove (macro jitter) on snare/clap
    "drum_snare_clap_groove_macro_jitter",
    # spacing (short profile) on hats/cymbals
    "drum_hats_cymbals_spacing_short_profile",
    # dynamics (average velocity) on toms/others
    "drum_toms_others_dynamics_average_velocity",
]

TARGET = PITCHED + DRUM


def build_target_concepts(taxonomy: dict[str, Any]) -> list[str]:
    """Return the validated subset of concepts to check (in order)."""
    known = set(taxonomy.keys())
    out = []
    for c in TARGET:
        if c in known:
            out.append(c)
    # Guarantee grid pairing: any grid_attempt_pct_X also has its grid_success_pct_X
    # (and vice versa).
    seen = set(out)
    for c in list(out):
        if "grid_attempt_pct_" in c:
            partner = c.replace("grid_attempt_pct_", "grid_success_pct_")
        elif "grid_success_pct_" in c:
            partner = c.replace("grid_success_pct_", "grid_attempt_pct_")
        else:
            continue
        if partner in known and partner not in seen:
            out.append(partner)
            seen.add(partner)
    return out
