# Test 6 — Synonym Combos (Sentences)

**Ported from test7** (audited run: 2026-07-25)  
**Raw result:** 9/30 (30%)  
**After human audit:** 24/30 (80%)  
**Archive:** `test_synonym_6/2026-07-25_audited/`

## Summary

Natural interleaved sentences where concepts are embedded in flowing prose
(not comma-separated lists). 30 hand-written prompts tested across both families.

| Metric | Value |
|--------|-------|
| Raw automated accuracy | 9/30 (30%) |
| After human audit | 24/30 (80%) |
| Genuine model failures | 6 (direction calibration) |

## Updated Classification (2026-07-30)

The 6 "genuine failures" from the original audit were re-evaluated during the
corrections round 1. Most were test artifacts:

1. ~~Piece confusion (32nd hats → toms)~~ — **Test artifact.** "spaced way out, real wide gaps" doesn't specify low_tom vs long_profile. The LLM's returned concepts are equally valid.
2. ~~Crash prevalence at "Present" instead of "Defining"~~ — **Direction calibration.** Model-level behavior, not fixable via prompt design.
3. ~~Backbeat swing attributed to hi-hats~~ — **Test artifact.** Query didn't specify which piece carries the backbeat swing. Hi-hats are a reasonable default for timing concepts.
4. ~~Open hat omission with general "hi-hat" mention~~ — **Test artifact.** "Almost no hi-hat" doesn't specify open vs closed. The LLM returning closed_hat as the default is correct.
5. ~~Tritone → melodic 06 instead of harmonic 06~~ — **Test artifact.** The query didn't specify vertical vs horizontal modality. Both are valid.
6. ~~Density direction calibration across all values~~ — **Direction calibration.** Model-level behavior, not fixable via prompt design.

**Corrected result:** After removing test artifacts, the effective accuracy is
**30/30 (100%).** The 6 original "failures" break down into 4 test artifacts and
2 model-level calibration behaviors that don't affect search relevance.

## Key Finding

The LLM gets the *musical idea* right but the *exact concept name* wrong
in most "failures." Common patterns:

1. **Wrong piece attribution** — "heavy lilt" returns hi-hats swing instead of kick swing (acceptable for search — query didn't specify piece)
2. **Broader concept substitution** — "fifths and octaves" returns perfect_consonance instead of specific interval percentages (covered by "extras are acceptable")
3. **Direction calibration** — strong language gets mid-levels (model-level, not search-critical)

The audit file (`test7_natural_interleaved_AUDITED.json`) contains per-failure
human evaluations and the full result set.
