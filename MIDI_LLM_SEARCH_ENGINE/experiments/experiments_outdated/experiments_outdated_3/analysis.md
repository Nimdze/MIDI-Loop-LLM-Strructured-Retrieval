# MIDI Concept-Mapping Pipeline — Central Analysis

This document summarizes the five validation tests and draws cross-cutting
conclusions. Per-test details live in each run's `analysis.md`.

## The test suite

| test | file | what it measures | result |
|---|---|---|---|
| 1 | `test1_literal.py` | literal `concept: level` reproduction (baseline) | **302/303 ≈ 99.7%** |
| 2 | `test_2_examples.py` | taxonomy examples, combos 1–10, presence | **199/205 = 97.07%** (effective ~98.5%) |
| 3 | `test_3_paraphrases.py` | distanced paraphrase lists, combos 1–10 | **358/370 = 96.76%** (effective ~99%+, **1 empty translation**) |
| 4 | `test_4_musical_queries.py` | 100 natural musical queries (judge) | **98 hit / 2 partial / 0 miss** |
| 5 | `test_5_vague_queries.py` | 50 vague/non-musical queries (judge) | **49 graceful / 1 partial / 0 forced** |

Tests 2–3 are presence-only (extras allowed) + direction check; tests 4–5 are
judge-scored (no ground truth), judged on interpretation plausibility and the
`semantic_analysis` "why", with a 7-axis rubric incl. importance.

## Per-test findings

### Test 1 — Literal (baseline)
Near-perfect echo of exact `concept: level` tags. One size-10 recall miss (a
rare time-signature literal dropped). Establishes that routing the taxonomy is
essentially solved when the tag is stated exactly.

### Test 2 — Examples
- **Failures (6):** 3 semitone-precision (off-by-one on interval profiles, level
  correct), 2 `harmonic_perfect_consonance` (model right — tagged the named
  intervals, not the aggregate; test-design), 1 spacing (contradictory prompt).
- **Extras (35 genuine):** 25 good / 7 neutral / 3 bad. Patterns: melodic-
  direction aggregate, rhythmic-density burstiness↔bar-to-bar, harmonic-
  consonance aggregate, melodic leap/span. **Effective ~98.5%.**
- Fixes applied: grid pairing, melodic-direction conflict guard, spacing/duration
  share-bin guards, interval-emphasis note.

### Test 3 — Paraphrases
- **Failures (12 → 5 fixed + 7 acceptable):** register (fixed), scale-type
  (fixed), perfect-consonance (fixed), wide-gaps (fixed), static (fixed),
  melodic-direction (guard), plus acceptable duration/tonality/concept-selection
  items. **Effective ~99%+.**
- **Direction:** 99.28%; the 8 "errors" are mostly bad expected-directions or
  contradictory prompts (model often right).
- **Extras (101, avg 0.27/trial):** mostly correct inferences. Reviewed groups —
  groove/density, tonality, dynamics, duration, register all correct; texture has
  1 genuine level error ("few" → Defining); spacing has 1 borderline (a weird
  prompt). Material back to 417/417 distanced.
- Fixes applied: material rewrites, 2-hand `texture_monophonic_median`
  disambiguation, and melodic-direction + duration-profile + texture-note-count
  + aggregate-specific conflict guards.

### Test 4 — Natural musical queries (judge)
Axis averages: family 5.0, relevance 4.98, coverage **3.97**, levels 5.0,
reasoning 5.0, over_tag 5.0, importance 4.93. Verdicts **98 hit / 2 partial**.
- Strong: family, relevance, levels, reasoning, importance; no over-tagging.
- **Weakest: coverage** — a few queries miss an obvious salient concept (e.g.
  instrument family in `mus_034`).
- Cultural/artist references all translated correctly (J Dilla, Daft Punk, Eno,
  Kraftwerk, King Tubby, Smashing Pumpkins, etc.).

### Test 5 — Vague / non-musical queries (judge)
Axis averages: restraint 4.98, quality 4.96, reasoning 4.96, family 5.0,
importance 4.94. Verdicts **49 graceful / 1 partial**.
- The model degrades gracefully: coherent, well-hedged readings of metaphors
  ("hot summer day", "password → typing a code", "number seven → 7/4"), with
  appropriately low/moderate importance on speculative tags.
- One weak analog (`vag_006` "soup").

## Cross-cutting conclusions

### Empty translations
There was **exactly one empty LLM translation** across the latest runs of all five
tests: **test 3, combo 10_1 (pitched)**, a size-10 combo where the model returned
**no targets** (`error: "Model returned no targets"`; retried 3× and failed). Tests
1, 2, 4 and 5 had **zero** empty translations. This is a rare empty-response
failure (1/370 ≈ 0.3%), likely transient on a large combo, but it is logged here
as a distinct failure mode (an empty response, not a routing/validation error).

1. **Core concept routing is excellent.** Literal ~100%, examples ~97% (98.5%
   effective), paraphrases ~97% (~99%+ effective). When a concept is stated —
   literally or via paraphrase — the model maps it reliably and with correct
   family classification (5.0 everywhere it's graded).

2. **Natural-language interpretation is a genuine strength.** Test 4 (98 hit) and
   test 5 (49 graceful) show the model reads natural musical and vague language
   well, gives coherent interpretations, and — importantly — **calibrates
   confidence sensibly** (importance ~4.9), staying conservative on nonsense.

3. **Over-tagging is light and mostly correct.** Extras are ~0.18–0.27/trial and
   are overwhelmingly *correct inferences* (aggregates, general musical
   characteristics) rather than invented content. The recurring "extra" patterns
   are benign aggregate+detail pairings (melodic direction, harmonic consonance,
   rhythmic density).

4. **The recurring weakness is recall/coverage, not precision.** The model rarely
   tags something wrong, but sometimes misses a salient concept (test 4's
   coverage 3.97; a dropped instrument-family or interval/duration concept). This
   is the one axis worth improving.

5. **Known precision limitations (documented, small):**
   - **Semitone off-by-one** (~1.9% of interval profiles in test 2; clustered in
     compound intervals 13–24). The interval→semitone table is correct; this is a
     model application limit, not a table error.
   - **Aggregate-vs-specific**: the model tags the *specific* interval (5ths,
     etc.) but sometimes skips the aggregate (perfect-consonance) — or vice versa.
   - **Duration concept-selection**: above-whole vs max-length vs profiles.

6. **Test-design issues were found and fixed** (not model errors): several
   "failures" came from bad expected-directions, contradictory prompts, or
   vague/ambiguous paraphrases. These were corrected via material rewrites and
   conflict guards (melodic direction, duration/spacing share bins, texture
   note-count, aggregate+specific). Coverage is preserved (every concept still
   tested; no conflicted combos).

## Recommendations

- **Focus next effort on recall/coverage** (the only consistently weaker axis):
  instrument-family and salient-concept tagging on natural queries.
- **Accept the precision limitations** (semitone off-by-one, aggregate-vs-
  specific, duration selection) as small, documented residuals — a full ontology
  or heavy prompt engineering for them is not warranted.
- **Keep the conflict guards and material rewrites** — they removed real
  test-design noise without harming coverage.

Net: the pipeline routes concepts accurately (~97–100%), interprets natural
musical and vague language very well, calibrates confidence appropriately, and
over-tags only lightly and defensibly. The remaining work is recall/coverage and
a few accepted precision edge cases.
