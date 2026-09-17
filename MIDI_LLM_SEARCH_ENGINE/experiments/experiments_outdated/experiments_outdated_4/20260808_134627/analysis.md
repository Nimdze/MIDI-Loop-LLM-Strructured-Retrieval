# Test 2 — Taxonomy Example Validation: Run Analysis

Run archive: `experiments/evaluation_examples_2/20260808_134627/`
Runner: `test_2_examples.py`

## What this test measures

Each active concept contributes its first `llm_example` as a prompt fragment;
combos 1–10 are sampled, and the model must return **all** expected concepts
(presence-only; extras allowed). This run adds two improvements over the prior
run:
- **Coverage guarantee** (`_ensure_covered`): every active concept is now
  guaranteed to appear in at least one combo (top-up at size 2).
- **Grid attempt/success pairing** and the **melodic-direction conflict guard**.

Semantic analysis is **off** for this test.

## Results

| metric | value |
|---|---|
| Total | 205 |
| Passed | 199 |
| Failed | 6 |
| Raw accuracy | **97.07%** |
| Coverage | every active concept appears in ≥1 combo (verified) |

Sizes 1, 2, 5, 7, 9, 10 = 100%; the 6 failures are at sizes 3 (1), 4 (2), 6 (1), 8 (2).

## Failure analysis (6)

| cluster | count | cause |
|---|---|---|
| Semitone-value precision | 3 | off-by-one on exact semitone interval profile (level correct) |
| `harmonic_perfect_consonance_pct` | 2 | aggregate-vs-specific — **model is right**; the example prompts it to tag the specific 5ths/4ths, not the aggregate |
| `spacing_8th_share` | 1 | recall miss on a **contradictory prompt** ("steady 16th note spacing" + "attacks on every eighth note") |

### 1. Semitone-value precision (3 — genuine model errors)

All off-by-one, always at the correct level:
- size3: "minor thirteenth" → `pct_21` (should be `20`)
- size4: "twelfth" → `pct_20` (should be `19`)
- size8: "major third" desc → `desc_3` (should be `desc_4`)

**Rate & clustering** (this run): 3/161 semitone-profile concepts missed = **1.9%**.
Clusters in **compound intervals (13–24 semitones): 2/46 = 4.3%**, vs simple
(1–12): **1/115 = 0.9%** — roughly 7× more likely on compound intervals (twelfth,
minor thirteenth), as expected (they need octave+interval arithmetic). Test 3
(paraphrases) has **0** such misses. The interval-emphasis system-prompt note did
**not** eliminate these 3 example-driven misses. (Small sample: 3 misses total,
so the percentages are noisy; the compound-vs-simple ratio is the signal.)

### 2. `harmonic_perfect_consonance_pct` (2 — model is right, test-design)

Both prompted by the taxonomy example *"lots of open fifths and power chords"*.
The model correctly tags the specific consonant intervals (`pct_07` 5ths,
`pct_05` 4ths, `pct_12` octave) but not the aggregate `harmonic_perfect_consonance_pct`
the query never names. This is the same aggregate-vs-specific mismatch as before.

**Fix applied (post-run, in the analyzer taxonomy):** changed the concept's
example to **"the vertical harmony is mostly perfect consonances"** so test 2
now prompts for the aggregate instead of the intervals.

### 3. `spacing_8th_share` (1 — contradictory prompt)

The size-4 prompt combined *"steady **16th** note spacing"* and *"attacks land on
every **eighth** note"* — two mutually-exclusive dominant-spacing claims. The
model returned the 16th and dropped the 8th (reasonable behavior).

**Fix applied (post-run, in tests 2 & 3):** added a **spacing-bin conflict guard**
— two spacing-share bins of the same scope (pitched, or the same drum kit piece)
can no longer share a combo (verified: 16th+8th, 8th+quarter, and same-kit-piece
pairs are flagged; different kit pieces and spacing-vs-duration are not).

## Effective success percentage

The 6 raw failures include **3 false positives** (2 `harmonic_perfect_consonance`
where the model was correct, and 1 `spacing_8th_share` on a contradictory prompt
now prevented by the conflict guard). Excluding those, the genuine model errors
are the **3 semitone-precision** misses.

**Effective success: 202/205 = 98.54%** (raw 97.07%; the remaining genuine
errors are the 3 off-by-one semitone misses, ~1.9% of semitone-profile concepts).

## Extras (over-tagging)

**35 genuine extras** across 33 trials (**avg 0.17/trial, max 2**) — light
over-tagging. Two additional "extras" were **excluded as test issues** (see
below); they are not genuine over-tags. By quality (see `extras_review.md` for
full prompt + returned logging of all cases):

- **GOOD — 25 (71%)**: sensible, prompt-supported inference. The recurring ones are
  the general melodic-contour tag (`melodic_intervals_pct_descending/ascending`)
  alongside the specific interval profile (redundant but correct), plus
  `harmonic_dissonance_pct` from tritone/compound-seventh language,
  `rhythmic_density_*_bar_to_bar` = Constant from "steady even density",
  `dynamics_accents_presence` from "accented regularly", and `max_leap` from
  "huge leaps beyond an octave".
- **NEUTRAL — 7 (20%)**: plausible but not clearly stated — e.g.
  `melodic_intervals_absolute_median` = Angular from "leaps up by tritone",
  `texture_polyphonic_pct` from vertical-interval language, a couple of
  inferred `bar_to_bar`/octave extras.

**Borderline in "Other":** `drum_snare_clap_rhythmic_density_burstiness` =
`Volatile Density` from *"the snare/clap drum fill at the end of the phrase"` —
the fill is explicitly **at the end**, so tagging overall "volatile density"
(bursts distributed through the part) would water it down with bursts *before*
the end. The fill is really a localized end-of-phrase turnaround, not
whole-part volatility, so this extra is questionable (borderline), not clearly
good.
- **BAD — 3 (9%)**: all **off-by-one semitone over-tags** — the model tagged a
  wrong interval value (`pct_21` for "minor thirteenth", `pct_20` for "twelfth",
  `desc_3` for "major third"). These are the same semitone-precision errors as
  the 3 presence misses (see above), surfacing as wrong extras.

**Excluded (test issues, not genuine extras):** 2× `profile_harmonic_intervals_pct_07`
(perfect fifth) tagged from prompts that explicitly said *"lots of open fifths
and power chords"*. The interval was literally named; the expected set simply
chose the aggregate (`harmonic_perfect_consonance_pct`) instead. These are not
over-tags. The remaining `profile_harmonic_intervals_pct_12` (octave, from
"power chords") is the borderline case already discussed.

**Notable pattern (not a defect):** in several cases the model treats the
`rhythmic_density_*` concepts as a **pair** — e.g. when
`drum_toms_others_rhythmic_density_burstiness` = `Uniform Density` is expected,
it also emits `drum_toms_others_rhythmic_density_bar_to_bar_evolution` =
`Constant Bar Event Density` as an extra. It co-reports the burstiness
(distribution within a bar) and the bar-to-bar evolution (distribution across
bars) as complementary views of the same density, so one appears as an "extra"
relative to the expected set. Reasonable, not bad — just worth knowing that these
two density concepts tend to travel together.

**Second notable pattern:** the model also adds the **general interval
direction** when asked to provide a specific interval with that direction — e.g.
when `profile_melodic_intervals_pct_asc_8_semitones` is expected it also emits
`melodic_intervals_pct_ascending` (Primary Ascending Motion) as an extra. It
reports the summary contour alongside the specific semitone bin, treating them as
an aggregate + detail pair. Again reasonable (redundant, not wrong), but worth
noting that a specific directional interval profile usually comes with its
general direction tag.

**Third notable pattern:** the model sometimes also emits the **aggregated
harmonic interval type** alongside the specific interval the query names — e.g.
when `profile_harmonic_intervals_pct_06_semitones` (tritone) is expected it also
tags `harmonic_dissonance_pct` (Primary Dissonance) as an extra. Same
aggregate-vs-specific pairing as the melodic direction case, here for the
harmonic consonance class (perfect / imperfect / dissonant) alongside the exact
semitone interval. Reasonable, not wrong.

### Rhythmic-density burstiness ↔ bar-to-bar pair

**What it is:** when the prompt says "steady even density", the model reads it
two complementary ways at once — *uniform within a bar* (`*_burstiness` =
`Uniform Density`) and *constant across bars* (`*_bar_to_bar` = `Constant Bar
Event Density`) — so it co-emits both even when only one is expected. This is a
**pair**, not an error: the two concepts describe the same density from two
perspectives. All 5 occurrences in this run are triggered by "steady even
density" and are correct and consistent (uniform + constant).

**Frequency:** when either member is expected, the complementary member co-occurs
**22.7%** of the time (5/22). Two additional `rhythmic_density_burstiness` extras
come from *different* triggers — "steady spacing" (#2 → Steady) and "drum fill"
(#3 → Volatile) — which are reasonable single inferences, not the pair, and are
grouped under "Other".

### Melodic-direction specific + aggregate

**What it is:** when the query asks for a *specific* directional interval
(`profile_melodic_intervals_pct_asc/desc_<N>`), the model usually returns it but
sometimes *also* adds the general contour (`melodic_intervals_pct_ascending/
descending`). It reports the summary direction as an aggregate alongside the
detail semitone bin.

**Correctness & consistency:** all 14 melodic-direction extras in this run are
**directionally correct** (the aggregate matches the prompt's "falls/leaps").
13 of 14 are identical — the aggregate at `Primary … Motion` from "melody mostly
falls/leaps". **One exception (#13):** `melodic_intervals_pct_ascending` =
**"Defining"** Ascending Motion for *"melody mostly leaps up by octave"* — the
direction is right, but "Defining" is over-strong for "mostly" (Defining is
reserved for absolute language; "mostly" should be Primary). So one melodic-
direction extra has a slightly mis-calibrated (over-stated) level.

**Frequency:** when a specific directional interval is expected, the general
direction is *also* returned **23.1%** of the time (18/78) — **descending
34.4%** (11/32) vs **ascending 15.2%** (7/46). So the pairing is occasional,
not systematic, and notably more common on the descending side.

### Melodic leap / span aggregate (max_leap / absolute_median)

**What it is:** when the query describes a melodic leap — a specific directional
interval, a `13plus` jump, or a large leap — the model sometimes *also* adds a
leap/span aggregate: `melodic_intervals_max_leap_semitones` ("Contains Extreme
Leaps (>= Octave)") or `melodic_intervals_absolute_median_semitones`
("Angular / Leaping Melodic Motion").

**Correctness:** all 3 melodic leap/span extras in this run are correct —
`max_leap` from "huge upward leaps beyond an octave", and `absolute_median` =
Angular from "leaps up by minor sixth / tritone".

**Frequency:** when a directional/leap interval is expected, a leap/span
aggregate is added as an extra **5.0%** of the time (3/60 trials) — notably rarer
than the melodic-direction pairing.

### Harmonic consonance aggregate (dissonance / perfect / imperfect)

**What it is:** when the query names a *specific* harmonic interval
(`profile_harmonic_intervals_pct_<N>`), the model sometimes *also* adds the
**consonance-class aggregate** — `harmonic_dissonance_pct`,
`harmonic_perfect_consonance_pct`, or `harmonic_imperfect_consonance_pct`.

**Correctness:** all 3 harmonic-aggregate extras in this run are correct: tritone
and compound-seventh (major fourteenth) → `harmonic_dissonance_pct`, and perfect
fifth → `harmonic_perfect_consonance_pct`. The model correctly infers the
consonance class from the specific interval.

**Frequency:** when a specific harmonic interval is expected, the consonance
aggregate is added as an extra **3.6%** of the time (3/83) — the rarest of the
aggregate-pairing patterns.

## Level calibration

- **No negation-level returns** — zero "No X" levels, so no concept contradicts
  its presence.
- Level distribution is healthy and tracks the example intensity: `Primary` 290,
  `High` 225, `Defining` 89, `Significant` 60, plus `Building/Constant/Frantic/
  Volatile/Organic/Tight`, etc.
- Levels broadly match the prompt language ("mostly"→Primary, "very"→High,
  "steady"→Constant, "lots of"→Primary/Significant). One minor nuance: an extra
  `melodic_intervals_pct_ascending` was tagged **"Defining"** for a "mostly leaps
  up" prompt (slightly strong — "mostly" would be Primary).

## Bottom line

Test 2 is strong at ~97% raw / **98.5% effective**. Coverage is now guaranteed
for every concept, grid pairing and the melodic-direction guard are in place,
and the two remaining issue types are: (a) a small, compound-clustered
semitone-precision limitation (off-by-one, genuine model error) and (b) the
perfect-consonance aggregate mismatch, now fixed at the taxonomy-example level.
The `harmonic_perfect_consonance` and `spacing` fixes take effect on a re-run.
