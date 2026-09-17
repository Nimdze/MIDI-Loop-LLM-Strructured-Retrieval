# Test 2 — Taxonomy Example Validation

**Date:** 2026-07-27  
**Result:** 246/255 (96.5%), then **255/255 (100%)** after fixes  
**Archive:** `experiments/test_examples_2/20260727_122106/`

## Summary

Each active concept was tested individually with its first `llm_example` as the
prompt. The LLM was expected to return a target matching the concept name.
No combinations — single-concept health check only.

| Result | Count |
|--------|-------|
| Passed (initial run) | 246/255 (96.5%) |
| Failed (initial) | 9/255 |
| Passed (after fix) | 9/9 re-tested ✅ |
| **Final** | **255/255 (100%)** |

## Failure Analysis (Initial Run)

All 9 failures fall into 3 root causes related to the example phrasing and the
drum_router's stem-prepending logic.

### Pattern 1: Vague Base Examples — 3 failures

The base concept `spacing_medium_profile` had the example `"medium"`. The
drum_router prepends the stem name, producing `"kick medium"`, `"snare medium"`,
`"hi-hats medium"`. The word "medium" alone does not convey spacing — the LLM
interpreted it as "moderate density" and returned
`rhythmic_density_average_events_per_beat: Moderately (not too) Busy`.

**Fix:** Changed the base example to `"the gaps between attacks are moderate in
length"` and added drum-prefixed overrides in `llm_examples.json`.

### Pattern 2: Contradictory Stem + Example — 3 failures

The base concept `groove_micro_jitter` had the example `"tight hi-hats"` which
references hi-hats generically. The drum_router prepends the stem, producing
`"kick tight hi-hats"`, `"snare tight hi-hats"`, `"toms tight hi-hats"` — these
are contradictory (mentioning hi-hats while referring to other pieces).

**Fix:** Changed the base example to `"the micro-timing precision is very tight"`
and added drum-prefixed overrides using the correct piece name (e.g.
`"the snare micro-timing is very tight"`).

### Pattern 3: Drum-Oriented Examples for General Concepts — 2 failures

`grid_attempt_pct_2and4` and `grid_success_pct_2and4` are general pitched
concepts, but their examples used `"backbeat"` language which is drum-specific.
The LLM returned drum-prefixed versions (`drum_snare_clap_*`) instead of the
general concepts.

**Fix:** Changed examples to
`"the two and four positions are attacked consistently across all instruments"`
and
`"the two and four positions land with perfect accuracy across all instruments"`.

### Pattern 4: Metadata Drop — 1 failure

`metadata_midi_program_number` with example `"patch zero acoustic grand piano"`
returned the instrument family concept instead of the program number concept.

**Fix:** Changed the example to
`"the exact program number from the midi standard is specified"`.

## Conclusion

Test 2 validates that every active concept's `llm_example` correctly maps back
to its concept. After fixing 9 poorly-phrased examples, the test passes at
**100% (255/255)**.

Key architectural findings:
- The drum_router's stem-prepending works well when the base example doesn't
  reference a specific piece
- Concepts that sound like a different domain ("backbeat" for a pitched concept)
  cause the LLM to return the wrong concept
- Single-word examples ("medium") are too vague for the LLM to resolve correctly
- The `llm_examples.json` override mechanism in `compile_taxonomy()` allows
  fixing these issues without modifying extractor source code
