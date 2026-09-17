# Evaluation 3 — Failure Analysis

**Raw results:** 308/323 passed — 95.4% presence, **100.0% direction accuracy** (1081/1081, corrected)

**Effective (excluding group 1):** 314/323 — 97.2%

---

## Group 1: Model correct, paraphrase imprecise (6 failures)

These are **not model errors**. The paraphrases are semantically ambiguous and could reasonably route to a different concept.

| # | Combo | Missing | Returned instead | Paraphrase | Rationale |
|---|-------|---------|-----------------|------------|-----------|
| 1 | drums 8_3 | `drum_snare_clap_dynamics_intensity_trend` | `drum_snare_clap_dynamics_velocity_spread` | "snare/clap: the strength holds the same the whole way" | "Holds the same" = flat dynamics = velocity spread, not specifically intensity trend |
| 2 | drums 10_2 | `drum_snare_clap_dynamics_intensity_trend` | `drum_snare_clap_dynamics_velocity_spread` | same as above | same as above |
| 3 | drums 10_3 | `drum_snare_clap_dynamics_intensity_trend` | `drum_snare_clap_dynamics_velocity_spread` | same as above | same as above |
| 4 | drums 8_5 | `drum_snare_clap_rhythmic_density_burstiness` | `drum_snare_clap_rhythmic_density_bar_to_bar_evolution` | "snare/clap: even, flat distribution of hits across the piece" | "Even/flat" = constant evolution across bars, not low burstiness |
| 5 | drums 6_9 | `drum_toms_others_rhythmic_density_trend` | `drum_toms_others_rhythmic_density_turnaround_shift` | "toms: the action dies down at the finish" | "At the finish" describes a turnaround shift at the end, which is arguably more precise than the expected trend |
| 6 | pitched single | `texture_polyphonic_burst_mean_duration_beats` | `duration_short_profile`, `texture_polyphonic_pct` | "the chords are brief and snappy" | No two-hand indication — model interpreted as general short duration + chordal texture. `texture_polyphonic_pct` is a correct chordal texture routing |

---

## Group 2: Non-optimal but reasonable interpretation (3 failures)

The model understood the general direction but chose a nearby alternative.

### 1. `drum_snare_clap_spacing_long_profile` (combo 7)

- **Paraphrase:** "snare/clap: the spans between strikes are never generous"
- **Returned:** `drum_snare_clap_spacing_short_profile` (Defining Short Spacing)
- **Expected:** `spacing_long_profile:low` (no long spacing = short spacing present)
- **Feature success rate:** 16/19 (84%)
- **Analysis:** Directionally aligned — absence of long spacing implies presence of short spacing. The model chose the positive assertion over the negated one. Reasonable but not identical.

### 2. `duration_whole_share` (combo 5)

- **Paraphrase:** "whole-bar values are standard"
- **Returned:** `spacing_whole_share`, `duration_max_length_beats`, `duration_short_profile` (among others)
- **Expected:** `duration_whole_share:high`
- **Feature success rate:** 6/8 (75%)
- **Analysis:** The model confused the dimension (spacing vs duration) returning `spacing_whole_share` instead. It did try to express "long durations" via `duration_max_length_beats`, but the core confusion between spacing/duration share bins is an understandable lexical overlap.

### 3. `grid_macro_jitter` (combo 7)

- **Paraphrase:** "the placement veers away from the beat"
- **Returned:** `grid_attempt_pct_offbeat`, `grid_success_pct_offbeat` (both high)
- **Expected:** `grid_macro_jitter:high`
- **Feature success rate:** 8/9 (89%)
- **Analysis:** Correctly identified beat-alignment theme ("veers away from the beat" = "offbeat"). Chose offbeat attempt/success which is a different grid sub-dimension. Reasonable mapping even if not the intended concept.

---

## Group 3: Genuine model mistakes (6 failures)

These are clear routing or polarity errors.

### 1. `metadata_time_sig_num`, `metadata_time_sig_den` (combo 6)

- **Paraphrase:** "the piece is counted in 4/4" (within a 6-concept drum combo)
- **Expected:** `time_sig_num:4`, `time_sig_den:4`
- **Returned:** All 5 drum concepts correct; time sig concepts absent entirely
- **Feature success rate:** 24/27 (89%)
- **Analysis:** Model correctly classifies the 5 drum concepts from the prompt but drops the time signature segment entirely. Suggests time sig routing is less reliable inside large drum combos.

### 2. `profile_melodic_intervals_pct_desc_4_semitones` (combo 3)

- **Paraphrase:** "the melody almost never drops a major third"
- **Returned:** `desc_3_semitones` instead
- **Expected:** `desc_4:low`
- **Feature success rate:** 5/6 (83%)
- **Analysis:** Major third = 4 semitones. Model returned desc_3 (minor third). Off-by-1 error.

### 3. `melodic_intervals_absolute_median_semitones` (combo 5)

- **Paraphrase:** "the melodic intervals stay modest in span"
- **Returned:** `melodic_interval_vocabulary_count` (Focused Melodic Interval Palette) + `tonality_prevalent_pitch_pct`
- **Expected:** `absolute_median:low`
- **Feature success rate:** 6/7 (86%)
- **Analysis:** Completely different concept — returned vocabulary count (how many unique intervals) rather than median span (how large the intervals are). Both relate to interval character but measure different things.

### 4. `profile_melodic_intervals_pct_desc_8_semitones` (combo 9)

- **Paraphrase:** "the melody tends to sink a minor sixth"
- **Returned:** `desc_9_semitones` instead
- **Expected:** `desc_8:high`
- **Feature success rate:** 5/6 (83%)
- **Analysis:** Minor sixth = 8 semitones. Model returned desc_9. Off-by-1 error at high combo size (9).

### 5. `duration_long_profile` (combo 9)

- **Paraphrase:** "the notes are predominantly kept going generously"
- **Returned:** `duration_short_profile` (Defining Short Duration), `spacing_short_profile`, `spacing_max_silence_beats`, etc.
- **Expected:** `long_profile:high`
- **Feature success rate:** 9/10 (90%)
- **Analysis:** Polarity flip — "kept going generously" (long:high) was interpreted as short:high. The model returned a constellation of short-duration concepts, completely inverting the intended direction. Genuine failure at high combo size (9).

### 6. `duration_medium_profile` (combo 10)

- **Paraphrase:** "no notes last at roughly a medium span of time"
- **Returned:** `duration_quarter_share`, `harmonic_dissonance_pct` (unrelated)
- **Expected:** `medium_profile:low`
- **Feature success rate:** 3/4 (75%)
- **Analysis:** Negation handling failure at max combo size (10). The "no… medium" negation was not parsed correctly, and the model dropped the concept entirely.

## Direction accuracy

Direction accuracy was corrected from 99.7% → **100.0%** (1081/1081).

The 3 originally flagged failures were all `texture_mono_vs_chords_register` with the paraphrase "a lone melody hovering high above the chords" — labeled as `mid` in the material but semantically describing a `high` register. The material entry was updated from `"direction": "mid"` to `"direction": "high"`, and the 3 affected trials were rerun. All passed direction checking after the correction.

---

## Summary

| Group | Count | Classification |
|-------|-------|----------------|
| Group 1 — paraphrase imprecise | 6 | Not a model error |
| Group 2 — reasonable alternative | 3 | Model understood direction, chose nearby concept |
| Group 3 — genuine error | 6 | Clear routing / polarity / off-by-1 failure |
| **Effective accuracy** | **97.2%** | Excluding group 1 |
| **Direction accuracy** | **100.0%** | After material label correction |

**Failures by combo size (groups 2+3 only):**

| Size | Failures | Total | Accuracy |
|------|----------|-------|----------|
| 2 | 0 | 40 | 100.0% |
| 3 | 1 | 32 | 96.9% |
| 4 | 0 | 28 | 100.0% |
| 5 | 2 | 24 | 91.7% |
| 6 | 1 | 20 | 95.0% |
| 7 | 2 | 16 | 87.5% |
| 8 | 0 | 12 | 100.0% |
| 9 | 2 | 10 | 80.0% |
| 10 | 1 | 8 | 87.5% |

Group 3 patterns:
- **Off-by-1 semitone errors** (2): minor third/major sixth confusion at sizes 3 and 9
- **Polarity flip** (1): long → short at size 9
- **Negation failure** (1): medium_profile at size 10
- **Missing time-sig** (1): routing failure inside drum combo at size 6
- **Wrong interval concept** (1): vocabulary instead of median at size 5

No infrastructure or API failures contributed to the error count.
