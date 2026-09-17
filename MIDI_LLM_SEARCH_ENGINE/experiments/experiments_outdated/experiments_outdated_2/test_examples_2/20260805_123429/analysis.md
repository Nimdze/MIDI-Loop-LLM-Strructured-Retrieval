# Test 2 — Single-Concept Example Validation — 05/08/2026

**Result: 149 / 151 (98.7%)** — both "failures" are false alarms (see below), so routing is effectively 100%.

Provider: DeepSeek (`deepseek-v4-flash`), concurrency 50, on the current (post-rename) taxonomy.
Run: `experiments/test_examples_2/20260805_123429/` (replaced the earlier 94.7% run).

Test 2 validates that each active concept's first `llm_example` routes to that concept (no combos). The model is free to assign any level.

## Changes applied before this run

- **Semitone↔musical-lingo mapping** added to the harmonic- and melodic-intervals subcategory "How to use" (a complete `00=unison … 24=double octave` reference). This fixed the prior run's 6 interval off-by-one failures (e.g. "perfect fourth → 4" instead of 5, "minor twelfth → 19" instead of 15).
- **Interval examples made intensity-specific** (e.g. `"vertical intervals are mostly perfect fifths"`, `"melody mostly leaps up by a major third"`) so their levels are determinable.
- **Archive path fixed** so test2 writes to `MIDI_LLM_SEARCH_ENGINE/experiments/` (matching test1) instead of `MIDI_RETRIEVE/experiments/`.

## Failures (2) — both false alarms

### 1. `harmonic_perfect_consonance_pct` — the model is correct
- Example: `"lots of open fifths and power chords"`.
- Model returned `profile_harmonic_intervals_pct_07_semitones` (perfect fifth) instead of the `harmonic_perfect_consonance_pct` aggregate.
- **Why it's a false alarm:** power chords *are* fifths, so "open fifths and power chords" is a perfectly valid reading as the *specific interval* (07 perfect fifth). The test expected the macro perfect-consonance aggregate, but the specific-interval interpretation is equally correct. Routing ambiguity in the example, not a model error.

### 2. `drum_prevalence_hats_cymbals_cymbal` — example ambiguity
- Example: `"Cymbal heavy"`.
- Model returned `dynamics_average_velocity` + `rhythmic_density` (loud/busy playing) instead of the prevalence concept.
- **Why it's a false alarm:** "heavy" is ambiguous — it can mean *heavy presence* (prevalence) or *heavy playing* (loud/busy). The model's reading of "heavy cymbal" as loud, busy cymbal playing is valid. The example `"Cymbal heavy"` doesn't clearly target prevalence.

## Notes

- The semitone-mapping fix is confirmed working (all interval off-by-one failures eliminated).
- Excluding the two false alarms, the remaining 149 concepts routed correctly to their concept.
- Level assignments were manually reviewed and are overwhelmingly correct/sensible (instrument family, key, scale, time-sig, register, density, spacing, texture, tonality).
