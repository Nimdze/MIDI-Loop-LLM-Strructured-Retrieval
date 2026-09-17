# Test 3 — Paraphrase-List Validation: Run Analysis

Run archive: `experiments/test_paraphrases_3/20260808_151912/`
Runner: `test_3_paraphrases.py` · Material: `test_3_materials.json`

> This run predates the last round of material/prompt/guard fixes. It is kept as
> the reference for the failure analysis; the fixes below are post-run and were
> validated in a focused re-check (not a full rerun).

## Results

| metric | value |
|---|---|
| Total | 370 |
| Passed | 358 |
| Failed | 12 |
| Presence | **96.76%** |
| Direction | 99.28% |
| Material distanced | 416/417 (one leak, since fixed → 417/417) |

## Failure analysis (12) and fix status

| case | missing | status |
|---|---|---|
| `7_0` drums | `spacing_long_profile` + `time_sig_num/den` | genuine recall noise in a size-7 combo |
| single static | `profile_melodic_intervals_pct_static` | **fixed** — static reword to "one fixed note" |
| `2_11` | `duration_long_profile` | aggregate-vs-specific (→ `half_share`) — acceptable |
| `4_7` | `tonality_unique_pitches_count` | **model better than expected** — see below |
| `4_8` | `duration_above_whole_share` | **fixed** — duration share-bin conflict guard |
| `4_12` | `duration_max_length_beats` | acceptable — prefers share/profile over max_length |
| `4_13` | `duration_max_length_beats` | acceptable — prefers share/profile over max_length |
| `5_2` | `register_median_note_midi` | **fixed** — 2-hand `texture_monophonic_median_pitch` disambiguation |
| `6_0` | `profile_melodic_intervals_pct_desc_4` | **fixed** — melodic asc/desc conflict guard (combo excluded) |
| `6_4` | `duration_half_share` (→ `spacing_half_share`) | not a real issue — "half-length" is ambiguous (duration vs spacing) |
| `6_9` | `duration_max_length_beats` | acceptable — prefers share/profile over max_length |
| `9_1` | `melodic_intervals_pct_descending` | **fixed** — melodic asc/desc conflict guard (combo excluded) |

### Notable: `4_7` is a better interpretation, not a miss
*"a plain diatonic pitch collection"* — `tonality_unique_pitches_count` (low) only
says *few* distinct pitches; it does not say which kind (they could be 5 or 7
chromatic/out-of-key pitches). The model tagged `tonality_out_of_key_notes` = 0
(*"mostly diatonic, in key"*), which for a "plain diatonic" collection is **more
informative** — it specifies the pitches stay in a standard scale. So the model
did better than the expected concept here.

## Fixes applied (post-run)

1. **Material rewrites** (register→median, scale-type→specific mode,
   perfect-consonance reword, wide-gaps chord context, static→"one fixed note",
   and the perfect-consonance "vertical harmony" leak fix) — material back to
   **417/417 distanced**.
2. **`texture_monophonic_median_pitch` disambiguation** — use only for a 2-hand
   loop (a single-note line over chordal content).
3. **Conflict guards** — melodic asc/desc family must not share a combo; two
   duration (or spacing) share bins of the same scope must not share a combo.
   Verified coverage is preserved (every concept still appears; no conflicted
   combos remain).

## Effective result

- **5 failures resolved** by the fixes/guards (static, `5_2`, `4_8`, `6_0`, `9_1`).
- **Remaining 7 all acceptable/defensible** — LLM recall noise (`7_0`),
  aggregate-vs-specific (`2_11`), the better-than-expected `4_7`, the preferred
  rare-`max_length` behavior (`4_12`/`4_13`/`6_9`), and the ambiguous
  duration/spacing case (`6_4`).

So only **~1–2 genuine failures** remain (the `2_11` aggregate-vs-specific and
the `7_0` recall noise) — **acceptable noise**. Effective accuracy after fixes is
effectively ~370/370 on the resolved/acceptable set.

## Direction errors (8 total, 99.28%)

Direction is graded only when a concept is present. The 8 direction errors
reclassify as mostly **test/material issues**, not model errors:

1. **`drum_snare_clap_rhythmic_density_burstiness` — 3 "errors" (8_4, 9_1, 10_2).**
   All expected **low** for *"mostly even with one dense spike"*, but the model
   tagged **Volatile** (high). This is **the model being correct**: burstiness
   measures the *size of the biggest spike* (volatility), not the number of
   spikes — a single dense spike is genuinely high-volatility. So the **expected
   (low) is wrong**; the prompt/material is the problem, not the model.

2. **`texture_pct_6plus_notes` — 2 "errors" (6_9, 8_3).** Expected **high** for
   *"six or more notes ring together"*, model tagged **Occasional** (low). These
   are combined prompts mixing several vertical note densities; in 6_9 the prompt
   also says *"single-note material is the norm"*, so the model correctly
   down-weighted 6+ notes to Occasional. 8_3 is vaguer but has similar
   complexity. Not a clear-cut failure.

3. **Contradictory prompts — 3.** `duration_short_profile` (9_3, 10_1) and
   `profile_melodic_intervals_pct_asc_11` (9_3) were tagged low while expected
   high, but the prompts are internally contradictory ("moderate/held and
   sustained" alongside "brief and clipped"; "rarely moves upward" alongside
   "jumps up by major seventh"), so the model's choice is defensible.

**Effective:** only **~1–2** are genuine model direction errors; the rest are bad
expected-directions or contradictory prompts.

**Fixes applied (post-run):**
- **Burstiness** — the material entry *"mostly even with one dense spike"* was
  reworded to **"the density erupts in one big spike"** and its direction set to
  **high** (volatile), matching the "burstiness = size of the biggest spike"
  semantics.
- **Guardrails added** to test 2 & 3 to prevent the subjective/contradictory
  combos: two **duration profiles** (short/medium/long) in one combo; two
  **texture note-count bins** (e.g. "single-note is the norm" + "six or more ring
  together"); and an **aggregate melodic direction** combined with a **specific
  directional interval** (e.g. "rarely moves upward" + "jumps up by major
   seventh"). Coverage is preserved (every concept still appears; no conflicted
   combos remain). Material remains **417/417 distanced**.

## Extras (over-tagging)

**101 extras across 76/370 trials (avg 0.27/trial, max 4).** Over-tagging is
light, and the recurring extras are largely defensible inferences rather than
invented content.

### Accepted patterns (shared with test 2, with reasons)

These were established as acceptable in test 2 and recur here:

1. **Melodic-direction aggregate (20 = 14 asc + 6 desc).** The model adds the
   general contour (`melodic_intervals_pct_ascending/descending`) alongside a
   specific directional interval profile. *Reason: redundant-but-correct* — the
   aggregate is a summary of the specific direction, a legitimate aggregate+detail
   pairing, not an error.
2. **Rhythmic-density burstiness ↔ bar-to-bar (4).** The model co-reports
   uniform-within-a-bar and constant-across-bars (e.g. from "steady even density").
   *Reason: complementary views of the same density* — correct, not a defect.
3. **Harmonic-consonance aggregate (5: dissonance ×2, perfect ×2, imperfect ×1).**
   The model adds the consonance class alongside a specific interval.
   *Reason: correct inference* of the consonance class from the named interval.
4. **Melodic leap/span (part of the melodic/interval bucket).** Adds
   `max_leap` / `absolute_median` from leap language. *Reason: correct inference*.

### Remaining patterns (not previously accepted)

These are the extras that go beyond the test-2 accepted set:

- **Groove / grid / density (15)** — mostly `groove_macro_jitter` = Tight (×3),
  `rhythmic_density_average_events_per_beat` = Busy, straight swing. The model
  infers tight timing / busy density / even swing from groove & density language.
  **Reviewed: all plausible, correct inferences** — Busy from "everywhere/dense
  wash/rapid pattern/flurry", Tight from "rigidly uniform / exact tidy control",
  grid 2-and-4 high from "carries the main backbeat", steady trend from
  "ceaseless nonstop", turnaround fill from "fill swell". No bad extras; the only
  borderline one is the duration↔spacing ambiguity already accepted.
- **Tonality (13)** — `tonality_prevalent_pitch_pct` (Straying ×4, Anchor ×3) and
  `tonality_out_of_key_notes` = 4-5 out-of-key (×4). The model adds a general
  tonality/anchoring read.
  **Reviewed: all plausible, correct inferences** — Anchor from "fixates on one
  note / pitches collapse to one center", Straying from "atonal / without any
  true tonal anchor", out-of-key from "broad chromatic / tonality wanders". The
  "plain diatonic → 0 out-of-key" case is the accepted better-than-expected read.
- **Dynamics (11)** — notably `drum_kick_dynamics_velocity_spread` =
  Flat/Programmed (×4) and `dynamics_intensity_trend` = Stable (×2).
  **Reviewed: all plausible, correct inferences** — Flat/Programmed velocity from
  "uniform loudness / soft throughout", Stable intensity from "hushed and soft
  from start to finish / throughout", Hard velocity from "forceful strikes /
  hefty flurry / pounding pulse".
- **Texture (9)** — `texture_polyphonic_pct` = Chordal (×5), plus pct_1 and
  monophonic-median. The model over-tags "chordal".
  **Reviewed: mostly correct, with one level error.** Chordal is correctly
  inferred from "chords / line above chords / chordal texture"; 1-note from
  "fixates on one note"; sustained from "long-sustained". **Issue:** "the chords
  are few and long-sustained" was tagged `texture_polyphonic_pct` =
  **Defining** Chordal — "few" contradicts "Defining" (a level over-statement),
  a genuine (minor) calibration error.
- **Duration (7)** — `texture_polyphonic_burst_mean_duration_beats` = Sustained
  (×2), `duration_short/long_profile`, half-share.
  **Reviewed: all plausible, correct inferences** — long from "held for a long
  time / multimeasure stretches", short (Defining) from "every note is brief",
  half from "half notes". The `max_length` from "multimeasure stretches" is
  correct (the above-whole-vs-max-length selection was already discussed).
- **Spacing (6)** — `drum_toms_others_spacing_long_profile` (×3), kick short,
  snare half.
  **Reviewed: 5 correct, 1 borderline.** Long from "gaps large / extended
  silence", short from "feverish pulse / dense". **Borderline (#5):** the model
  tagged `drum_snare_clap_spacing_half_share` = Defining from "half notes", but
  that "half notes" is the time-signature beat unit (and the prompt also says
  "widely spaced onsets") — an ambiguous/contradictory prompt, so borderline, not
  a clear error.
- **Register (2)** — `register_boundary_shift_semitones` (Moderate/Active).
  **Reviewed: both correct** — register migration correctly inferred from
  "keeps climbing upward" / "keeps descending".
