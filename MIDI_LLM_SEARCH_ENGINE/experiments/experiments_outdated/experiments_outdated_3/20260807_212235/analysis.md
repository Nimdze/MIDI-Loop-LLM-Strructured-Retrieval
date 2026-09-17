# Test 3 — Paraphrase-List Validation: Run Analysis

Run archive: `experiments/test_paraphrases_3/20260807_212235/`
Runner: `test_3_paraphrases.py` · Material: `test_3_materials.json`

## What this test measures

Comma-joined paraphrase lists (one per active concept, combos 1–10) that have
been lexically distanced from the system prompt. Pure presence check (extras
allowed) plus a secondary direction check. The material is verified **417/417
distanced (0 leaks)**.

## Results

| metric | value |
|---|---|
| Total | 370 |
| Passed (presence) | 345 |
| Failed | 25 |
| Presence accuracy | **93.2%** |
| Direction accuracy | **99.6%** |
| Material distanced | 417/417 |

All 25 failures are **pitched** (2 singles, 23 combos), at combo sizes 2–9.
Direction is essentially clean: of 103 graded, 68 high✓, 34 low✓, 1 high✗ — so
these are **recall misses**, not level errors.

## Failure groups (by missing concept)

| cluster | count | concept(s) |
|---|---|---|
| A. Register (lowest) | 4 | `register_lowest_note_midi` |
| B. Tonality unique-pitch | 4 | `tonality_unique_pitches_count` (1) + `_trend` (3) |
| C. Duration | 6 | `half_share`, `8th_share`, `short_profile`, `long_profile`, `above_whole_share` (×2) |
| D. Metadata scale type | 3 | `metadata_scale_type` |
| E. Harmonic perfect consonance | 2 | `harmonic_perfect_consonance_pct` |
| F. Texture | 4 | `texture_avg_wide_gaps_per_burst` (2) + `texture_monophonic_median_pitch` (2) |
| G. Melodic static profile | 2 | `profile_melodic_intervals_pct_static` |
| H. Melodic direction | 1 | `melodic_intervals_pct_ascending` (conflicting prompt) |

## What the model returned instead (substitution map)

Most misses are **substitutions to a sibling concept**, not pure drops:

- **Register lowest → `register_median_note_midi` (Bass)** (or `texture_monophonic_median_pitch`) for "the line stays pinned down low".
- **Tonality unique-pitch → `tonality_prevalent_pitch_pct` (Anchor Centered)** for "fixates on one lone note" / "pitches collapse down to one center".
- **Duration → `duration_max_length_beats` / `duration_short_profile` / `duration_quarter_share` / `duration_long_profile`** depending on the phrase.
- **metadata_scale_type → dropped entirely** (nothing returned for "the scale's mode is indicated") — a pure omission.
- **Harmonic perfect consonance ("open and hollow") → `texture_avg_wide_gaps_per_burst` (Big Chordal Spread)**.
- **`texture_avg_wide_gaps_per_burst` → `spacing_long_profile` / `register_spread_semitones`.**
- **`texture_monophonic_median_pitch` → `texture_pct_1_notes` + `texture_polyphonic_pct`.**
- **`profile_melodic_intervals_pct_static` → `duration_long_profile` / `duration_max_length_beats`.**
- **`melodic_intervals_pct_ascending` (conflicting "rises" + "trends downward") → `register_boundary_shift_semitones` + `descending`.**

## Semantic review of the ambiguity clusters

### Register lowest vs median — **FIXED in material**

Reviewing `register_lowest_note_midi`'s paraphrases semantically:
- "the floor pitch sits in the upper register" / "the floor drops into the lowest bass region" / "the lowest notes plunge into the sub-bass" — genuinely about the **floor / lowest boundary note** (correct).
- "**the line stays pinned down low**" — "the line … low" is **median-language** (where the part's center sits), the same construction as `register_median_note_midi`'s "the line mostly hangs down in the bass."

The model handles this correctly: for "the line stays pinned down low" it returns `register_median_note_midi` = Bass (4_5, 7_0, 8_0), and it *does* tag `register_lowest_note_midi` (High / Bass / Sub-Bass) for genuine floor/sub-bass prompts (4_10, 6_3, 7_3, 4_0) — without also tagging the median. So it distinguishes "where the line sits" (median) from "the floor/boundary note" (lowest).

**Fix applied (post-run, in `test_3_materials.json`):** moved "the line stays pinned down low" from `register_lowest_note_midi` → `register_median_note_midi` (as a `[low]` median paraphrase). `register_lowest_note_midi` now holds only the three genuine floor/sub-bass phrases. Note: this run was generated **before** that fix.

### Tonality unique-pitch vs dominant-pitch — **accepted & documented for now**

The paraphrases "the music fixates on one lone note" (`unique_pitches_count`) and "the pitches collapse down to one center" (`unique_pitches_count_trend`) are **genuinely vague**: they imply both *few/contracting distinct pitches* **and** *a single dominant/anchored pitch*. So the model tagging `tonality_prevalent_pitch_pct` (Anchor Centered) is a reasonable interpretation — it did generally well, not a clear error.

Options considered: reword the two paraphrases to purely target count/trend ("draws on a very small set of distinct pitches" / "the number of distinct pitches contracts toward just a few as it runs"), or add a tonality disambiguation note, or accept both concepts in the expected set. **Decision: accept and document for now — no material change.** The distinct concepts are clear in the clean paraphrases, and this ambiguity is a small, well-understood edge case.

### Duration — **max_length disambiguation fixed; the rest documented as slight non-exactness**

The duration misses split into two behaviors:

1. **"no X sustains" negation → `duration_max_length_beats` as a ceiling.** For "no half-note sustains" / "no eighth-note sustains" the model sometimes tagged `duration_max_length_beats` with a capped value ("Max Sustain 1/4-1/2 Bar", "< 1/8 Bar") to express "nothing reaches X" (single, 3_2). This is **too coarse**: a ceiling at X also excludes everything longer (X AND above), which is broader than a precise "no X" negation. (7_6 correctly used the share bin's own "No 8th Note Duration" level instead.)

   **Fix applied (system prompt, in `MIDI_ANALYZER_TAGGER`):** added a disambiguation note that `duration_max_length_beats` is for ceiling statements ("no note longer than X"), and must **not** be used to fulfill a specific "no X sustains" negation — use the matching share bin (e.g. `duration_half_share`, `duration_8th_share`) with its "No X" level.

2. **Sibling-concept substitution for the other duration misses** — `above_whole_share` → `max_length` + `long_profile` (4_10, 8_2); `short_profile` aggregate missed when the specific `8th_share` is tagged (5_2); `long_profile` missed in favor of `quarter_share` (7_6). These **get the idea across but are not the most exact way** to state the result. **Documented as slight non-exactness (accepted for now)** — the model expresses the right sustained-character via a related duration concept (max_length / the summary profile) rather than the exact share bin.

### Metadata scale type — **fixed (specific-mode paraphrase)**

`metadata_scale_type` was dropped entirely (nothing returned) on the vague phrase **"the scale's mode is indicated"** (3_0, 5_9, 6_5) — no specific key or mode is named, so the model has nothing concrete to tag. Verified against the results: the specific-mode paraphrase **"the piece sits in a major mode"** passes both times (single, 10_2), while the vague one fails 3/3.

**Fix applied (post-run, in `test_3_materials.json`):** replaced "the scale's mode is indicated" with **"the piece sits in a minor mode"** — now `metadata_scale_type` has a specific major and a specific minor paraphrase.

### Harmonic perfect consonance — **fixed (vague "hollow" phrasing)**

"open and hollow" was too vague — the model routed it to `texture_avg_wide_gaps_per_burst` (Big Chordal Spread) instead of `harmonic_perfect_consonance_pct` (3_8, 8_3). 

**Fix applied (post-run, in `test_3_materials.json`):** reworded the two hollow-based high paraphrases to clearly convey perfect consonance, lexically distant from the prompt and verified distanced:
- "the harmony is open and hollow" → **"the vertical intervals are mostly perfect consonances"**
- "the harmony sounds pure, uncluttered, and hollow" → **"the harmony rests on pure consonant intervals"**

### Melodic direction conflict — **fixed (combo guard)**

`melodic_intervals_pct_ascending` was missed in 9_3 because its prompt combined "pitch rises throughout the line" **and** "melody trends downward through the phrase" — a self-contradictory assertion (a single melody can't be dominantly both ascending and descending). With a conflicting prompt, the model can only fail.

**Fix applied (post-run, in `test_3_paraphrases.py`):** added a combo-construction guard — `melodic_intervals_pct_ascending` and `melodic_intervals_pct_descending` are a `CONFLICT_PAIRS` set and are never sampled into the same combo.

### Texture & static-profile

- **`texture_avg_wide_gaps_per_burst` — fixed (vague, non-chord phrasing).** "the notes are spread far apart" was too vague when not in a chord context (the model read it as spacing/register). **Fix applied (material):** reworded to **"the notes within each chord sit far apart from one another"**, grounding it in the chord/voicing context (the other two chord-context paraphrases were already fine).
- **`texture_monophonic_median_pitch` — accepted & documented.** "a single line buried inside the chordal texture" is genuinely hard: it implies both `texture_pct_1_notes` (a lone voice) and `texture_polyphonic_pct` (chordal) plus the monophonic median pitch. The model returning those two components is understandable, even if not the exact ideal. **No change.**
- **`profile_melodic_intervals_pct_static` — fixed (not exclusive enough).** "held notes and melodic pedal tones" conflated sustain ("held") with repetition (static). **Fix applied (material):** reworded to the more exclusive **"the melody repeats the exact same pitch over and over"**, which points cleanly at the repeated-same-pitch (0-semitone static) bin rather than long sustain.

## Fix verification (all post-run fixes re-checked)

A dedicated single-trial run confirmed each corrected paraphrase / scenario now
routes to the intended concept (9/9 prompt-level, 7/7 code-level):

| fix | prompt | tagged |
|---|---|---|
| register_median | "the line stays pinned down low" | `register_median_note_midi` ✓ |
| scale_type | "the piece sits in a minor mode" | `metadata_scale_type` ✓ |
| perfect_cons #1 | "vertical intervals are mostly perfect consonances" | `harmonic_perfect_consonance_pct` ✓ |
| perfect_cons #2 | "harmony rests on pure consonant intervals" | `harmonic_perfect_consonance_pct` ✓ |
| wide_gaps | "notes within each chord sit far apart" | `texture_avg_wide_gaps_per_burst` ✓ |
| static | "repeats the exact same pitch over and over" | `profile_melodic_intervals_pct_static` ✓ |
| duration negation | "no half-note sustains" | `duration_half_share` ✓ (no longer `max_length`) |
| melodic asc | "shape mostly points higher" | `melodic_intervals_pct_ascending` ✓ |
| conflict guard | `_has_conflict` flags asc+desc, not asc alone | code check ✓ |

Key confirmations: the duration "no X sustains" negation now tags the share bin
(not the too-coarse `max_length` ceiling); the register "line pinned down low"
routes to the median; and the ascending/descending conflict guard prevents the
self-contradictory combo.

## Direction / level calibration

Strong — 99.6% direction accuracy; the only level issue of note is the isolated
understated `asc_13plus`-type cases seen elsewhere. Not a scaling or polarity
problem.

## Bottom line

Test 3 is healthy: 93.2% presence, all failures pitched, direction nearly
perfect, material 100% distanced. The failures are recall misses concentrated in
a few areas (register-lowest, tonality unique-pitch, duration-specific values,
metadata scale-type, harmonic-consonance aggregate, texture, static-profile,
melodic-direction conflict), almost all as **sibling-concept substitutions**
rather than drops. Clusters reviewed semantically: register-lowest → **material
mis-assignment (fixed)**; tonality unique-pitch vs dominant-pitch → **genuinely
ambiguous and accepted for now**; duration → **`max_length` negation fix (system
prompt)** + rest **documented as slight non-exactness**; metadata scale-type →
**vague-paraphrase fix (specific mode)**; harmonic perfect consonance →
**vague "hollow" reword (fixed)**; melodic direction → **conflicting-combo guard
(fixed)**; `texture_avg_wide_gaps_per_burst` → **non-chord reword (fixed)**;
`texture_monophonic_median_pitch` → **accepted (understandably hard)**;
`profile_melodic_intervals_pct_static` → **not-exclusive reword (fixed)**.
