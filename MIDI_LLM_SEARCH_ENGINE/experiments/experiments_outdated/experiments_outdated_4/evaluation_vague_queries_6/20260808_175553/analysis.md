# Test 5 — Vague / Non-musical / Random Queries: Run Analysis & Scoring

Run archive: `experiments/evaluation_vague_queries_6/20260808_175553/`
Runner: `test_5_vague_queries.py` · Bank: `test_5_vague_queries.json`

## What this test measures

50 vague, non-musical, or random queries, **no expected targets**. The test
measures **graceful degradation**: the model should not confidently tag a pile of
specific concepts onto nonsense. A conservative response is good, but for queries
that *do* have a plausible musical analog, a rich interpretation is a *feature*,
not over-tagging.

## Scoring grounds

Since there is no ground truth, scoring is a **judgment of interpretation
quality**, driven mainly by the **semantic analysis (the "why")**: are the tags a
musically plausible, coherent reading of the query, with honest reasoning and
appropriate confidence (importance)? **Tag count is not a criterion** — a
metaphor with a rich analog ("hot summer day", "old photographs") can legitimately
map to many concepts. Per-query scores in `scores.json`.

## Scoring result

| verdict | count |
|---|---|
| **graceful** | 49 |
| **partial** | 1 |
| **forced** | 0 |
| **miss** | 0 |

**Axis averages (1–5):**

| axis | avg |
|---|---|
| restraint | 4.98 |
| quality | 4.96 |
| reasoning | 4.96 |
| family | 5.0 |
| importance | 4.94 |

**Interpretation:** the model degrades gracefully in **49/50** queries. Across the
board the `semantic_analysis` "why" is specific, musically plausible, and honest —
each metaphor is given a coherent reading with appropriately hedged importance.
Family classification is always sensible.

## Notable findings

**Rich, well-reasoned interpretations** (many tags, all justified by the "why"):
- `vag_018` "hot summer day" → lazy/hazy→sparse, warm→sustaining, cozy→mid
  register, sunny→major … every tag has a specific rationale.
- `vag_027` "lost in a big city" → wandering→straying anchor, vast→wide spread,
  tension→dissonance, disorientation→angular motion.
- `vag_039` "old photographs" → nostalgic→soft/warm/minor/chordal.
- `vag_003` "elevator" → soft, easy-listening chordal, mid register, stepwise.

**Clever / correct mappings:** `vag_046` "the number seven" → 7/4 time; `vag_009`
"cat walking on keyboard" → chaotic/out-of-key; `vag_017` "a bit of nothing" →
minimal/silence; `vag_019` "metallic" → cymbal; `vag_026` "square" → straight;
`vag_034` "broken machine" → stuttery; `vag_045` "static on an old radio" →
Sound Effects; `vag_042` "password" → a coherent "typing a code" reading
(staccato, tight, flat dynamics).

**The one partial — `vag_006` "add some soup":** the weakest analog; the top
importance tag (chordal = 5, from "soup → dense/filling") is a stretch. Still a
defensible loose reading, but the most speculative of the set.

**Importance (7th axis):** appropriately low/moderate on speculative readings
across the board (avg 4.94), so the model generally does **not** over-commit
confidence on invented specifics.

## Bottom line

Test 5 is excellent: **49/50 graceful, 0 forced, 0 miss**. Judged on musical
plausibility and reasoning quality (the "why") rather than tag count, the model
handles vague and non-musical queries with coherent, well-hedged interpretations
and only one weak analog (`soup`). Judge input is `to_evaluate.json`; scores in
`scores.json`.
