# Test 3 — Example Combos 2-10 — 06/08/2026

**Result: 240 / 260 (92.3%)** — drums 96.2%, pitched 88.5%.

Provider: DeepSeek (`deepseek-v4-flash`), concurrency 20, no semantic analysis.
Run: `experiments/test_examples_3/20260806_215552/` (the only run kept in `test_examples_3/`).

Test 3 validates that each concept's first `llm_example` routes to that concept when combined N-at-a-time (presence-only check; extras allowed). All 260 trials ran (no early stopping).

## Changes applied before this run

- **Drum examples propagated + family-prefixed** (`drum_router.py` + `registry.py`): drum rhythmic/dynamic concepts now carry piece-localized examples (e.g. `drum_kick_spacing_8th_share → "the kick attacks land on every eighth note"`). Previously the registry emitted a minimal `base_concept` reference with no examples, so the drum tier only tested prevalence. Now drums covers the real schema (157 concepts).
- **Prevalence examples de-verbatim'd**: `"the Ride 2 is prominent"` etc. instead of `"a lot of X"`.
- **`max_tokens` 4000 → 8000** (`llm_client.py`): 4000 caused outputs to collapse to `{}` (43 empties) and truncation (7 `json_delim`). A/B confirmed the fix.
- **Cache warm-up** before the parallel batch.
- **No semantic analysis.**

## Failure breakdown (20)

- **19 model_miss** — valid translation, missed one concept (all "missing 1/N").
- **1 no_targets** — the model returned a complete JSON with an interpretation but **empty `targets: []`** (a model choice, not truncation; not fixed by a larger `max_tokens`).
- 0 connection errors, 0 `json_delim`.

## The 19 model_miss — classification

### Totally legitimate (2)
The model's answer was correct, so these aren't failures:
- **`harmonic_perfect_consonance_pct` (2×)** — `"lots of open fifths and power chords"` → the model returned the specific **perfect-fifth interval (07)** instead of the perfect-consonance aggregate. This is correct: "power chords are fifths." Totally legitimate.

### Taxonomy-bug interval errors — corrected & verified (7)
These were **not model mistakes** — the taxonomy mislabeled harmonic compound intervals. `HARMONIC_INTERVAL_NAMES` had bins 19–23 off by one (e.g. bin 20 labeled "twelfth/perfect twelfth" but a twelfth = 19 semitones; bin 22 labeled "major thirteenth" but a major thirteenth = 21). The model computed the *correct* semitone and returned the right bin; the test expected the mislabeled one.

**Fix:** corrected `HARMONIC_INTERVAL_NAMES` for bins 19–23 (19 = twelfth/perfect twelfth, 20 = minor thirteenth, 21 = major thirteenth, 22 = minor fourteenth, 23 = major fourteenth). Also added a **"SEMITONE ↔ INTERVAL REFERENCE"** block to the prompt (right before ACTIVE SCHEMA, explicitly stated to apply to BOTH melodic and harmonic intervals) so the model can convert interval names to semitones exactly.

**Verification:** a dedicated interval-routing test (the 8 previously-affected interval concepts) all passed — including `pct_19`, `pct_20`, `pct_22`, `pct_23`, and the melodic `desc_4`/`desc_7`. The off-by-ones are resolved.

### Real model mistakes (10)

**A. Interpretation mistakes (5)** — the model chose a plausible but wrong reading of an ambiguous phrase:
1. `duration_above_whole_share` (c3) — "notes sustain longer than a measure, …" → returned `duration_max_length_beats` instead of the above-whole share.
2. `duration_above_whole_share` (c5) — same phrase → `duration_max_length_beats`.
3. `duration_above_whole_share` (c5) — same phrase → `duration_max_length_beats`.
4. `duration_above_whole_share` (c7) — same phrase → `duration_max_length_beats`.
5. `texture_polyphonic_pct` (c2) — "…vertical intervals are mostly minor twelfth, chords" → returned the harmonic interval (minor twelfth / 19) instead of the texture/chordal-share aggregate.

**B. Genuine recall misses (5)** — the model dropped a concept and returned unrelated ones:
6. `drum_kick_spacing_16th_share` (drums c2) — "…the kick steady 16th note spacing…" → returned half-note spacing, dropped 16th.
7. `drum_kick_spacing_quarter_share` (drums c5) — "…the kick notes are spaced a quarter note apart…" → returned kick 8th + hats quarter, dropped kick quarter.
8. `drum_snare_clap_rhythmic_density_burstiness` (drums c8) — "…the snare/clap steady even density…" → returned bar-to-bar evolution, dropped snare burstiness.
9. `drum_hats_cymbals_spacing_medium_profile` (drums c10) — "…the hats/cymbals the gaps between attacks are moderate…" → returned hats whole share, dropped hats medium profile.
10. `duration_32nd_share` (pitched c9) — "notes are very short 32nd note bursts, …" → returned `spacing_32nd` instead of `duration_32nd`.

## Takeaway

- 2 of the "failures" are correct answers (not failures).
- 7 were a taxonomy bug in the harmonic compound-interval labels — corrected and verified.
- **10 genuine model mistakes remain**: 5 are interpretation differences on ambiguous phrases (mostly `duration_above_whole_share` ↔ `duration_max_length_beats`), and 5 are combo recall misses (mostly drums).

## Post-run prompt clarifications (not yet re-tested)

Two prompt clarifications were added after this run to target the two largest genuine-mistake clusters. They are **discussed here but not re-verified** — a re-run would be needed to confirm their effect.

**1. Duration disambiguation (`duration_above_whole_share` vs `max_length_beats` vs `long_profile`).** The 4 `duration_above_whole_share` interpretation misses all came from the model routing *"notes sustain longer than a measure"* to `duration_max_length_beats` instead of the above-whole share. The `duration` subcategory previously had no disambiguation (unlike `spacing`, which distinguishes `above_whole_share` / `long_profile` / `max_silence_beats`). Added a `duration` disambiguation mirroring that pattern:
> *"sustained"/"pads"/"long" (non-extreme) → `duration_long_profile`; notes sustained beyond a whole measure → the `duration_above_whole_share` bin (the proportion exceeding a whole note); `duration_max_length_beats` is complementary — the single longest note (a ceiling) and says nothing about the share of the other notes.*

**2. Follow explicit per-piece/per-value instructions (drums).** The drum spacing misses included cases where two pieces shared the same value (e.g. kick quarter + hats quarter) or a specific profile was dropped. The model may have been "thinking holistically" and assuming pieces shouldn't share values. Added a note to the drums section:
> *"Follow explicit per-piece and per-value instructions exactly — if the query specifies a particular kit piece or value, tag it. For example, if the query states both the kick and the hi-hats use the same spacing value, emit the specified concept for each piece rather than assuming the pieces share or differ in a value."*

**Considered but deferred:**
- **Spacing profile vs share disambiguation** (the `medium_profile` → `whole share` confusion) — not added for now.
- **Rhythmic-density concept disambiguation** (burstiness / bar-to-bar / trend overlap) — not added for now; the concepts genuinely overlap and a clarification may be low-yield.

These changes are expected to reduce the `duration_above_whole_share` interpretation misses and some drum spacing recall misses, but have **not yet been validated** by a re-run.

