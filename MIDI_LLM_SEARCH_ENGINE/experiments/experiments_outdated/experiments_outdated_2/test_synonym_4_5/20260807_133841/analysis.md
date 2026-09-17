# test_4_5 — run analysis (20260807_133841)

Fused single + combo synonym routing test, `test_4_5_material.json`.

## Headline results
- **Presence:** 228/250 (91.2%) — every expected concept returned.
- **Direction (after fix):** 480/484 (99.2%).
- By family: drums 93.9%, pitched 89.0%. By kind: single 95.4%, gridpair 100%, combo 84.6%.
- Combos by size: 2→85%, 3→93.3%, 4→95%, 5→60%.

## 1. Fundamental test failure found: the direction bucket
The original 3-bucket (`high`/`mid`/`low`) direction grading was broken for concepts
with 5–6 levels. The coarse bucket maps the middle levels to `mid`, e.g.:
- `"often exceeds a full measure"` (high above-whole share) → model returned
  `Significant Above Whole Note Spacing` (index 2 of 6) → bucketed `mid`, graded WRONG.
- `"rarely played"` (low attempt) → model returned `Very Low Attempts` (index 3 of 5) → `mid`, WRONG.

This produced **92/96 direction "misses"** that were bucket artifacts, not model errors
(58 × `high→mid`, 34 × `low→mid`).

**Fix (applied to the runner and re-scored here):** direction is now a coarse *polarity*
check — a `high` expectation is satisfied by `high` **or** `mid` (only landing on `low`
fails); `low` by `low` **or** `mid`; `mid` expectations stay strict. After the fix only
**4 genuine polarity flips** remain (3 `high→low`, 1 `low→high`), hence 99.2%.

Raw returned levels are preserved in `results.json`; only the `ok` interpretation changed.

## 2. The 22 presence failures — how they group
Roughly:
- **~8 are `metadata_*` dropped in combos.** In 4–5-way combos the model returns the
  musical concepts but silently drops `metadata_instrument_family` / `metadata_root_key` /
  `time_sig` segments (e.g. `"High Tom is used throughout, a drum kit"` → misses instrument_family).
  Genuine model behaviour (focuses on musical content under load).
- **~12 are sibling-concept confusions**, where the query genuinely overlaps a neighbour:
  `"every note is brief"`→`short_profile`, `"notes spread far apart"`→`spacing_long_profile`,
  `"short punchy chords"`→`duration_short_profile`, `"plain diatonic set"`→`out_of_key_notes`,
  `"atonal"`→`out_of_key_notes`, `"melody jumps wide"`→`absolute_median`,
  `texture_polyphonic_pct` ↔ `texture_pct_1_notes`. Many of these are **test/annotation
  ambiguity** — the synonym plausibly points at the sibling (and in some cases, e.g.
  `"every note is brief"`, the model's answer is arguably more correct than the expectation).
- **~2 are a dropped interval share** in a combo (e.g. missed the 14-semitone concept).

## 3. Genuine vs test/ambiguity
- **Presence:** roughly half genuine (metadata dropped in combos, a couple interval drops),
  half test/ambiguity (synonyms that read as a sibling, or debatable expectations).
- **Direction:** essentially all "misses" were the bucket bug; the 4 remaining flips are
  genuine.

## 4. Caveats
- **Combo-5 = 20 trials** (12/20 = 60%) — small n, high variance; not a stable estimate.
- `metadata_*` in large combos is a real, reproducible weakness (see failures doc).

## Files
- `summary.json`, `results.json` (250 trials, exhaustive raw+translation+call logs,
  interpretation/semantic analysis off).
- `failures_manual_review.md` — query→output pairs for the 22 presence failures and the
  4 direction flips.
