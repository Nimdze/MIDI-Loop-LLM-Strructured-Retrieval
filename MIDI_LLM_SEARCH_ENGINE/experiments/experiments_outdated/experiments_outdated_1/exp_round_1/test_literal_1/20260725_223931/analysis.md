# Test 1 — Literal Tag Reproduction

**Date:** 2026-07-25  
**Result:** 289/300 (96.3%)  
**Archive:** `experiments/test_literal_1/20260725_223931/`

## Summary

| Family | Combo 1 | Combo 2 | Combo 3 | Combo 4 | Combo 5 | Combo 6 | Combo 7 | Combo 8 | Combo 9 | Combo 10 | Total |
|--------|---------|---------|---------|---------|---------|---------|---------|---------|---------|----------|-------|
| Drums | 19/20 | 20/20 | 20/20 | 20/20 | 18/20 | 9/10 | 10/10 | 9/10 | 9/10 | 10/10 | 144/150 (96.0%) |
| Pitched | 20/20 | 20/20 | 20/20 | 19/20 | 19/20 | 10/10 | 10/10 | 9/10 | 10/10 | 8/10 | 145/150 (96.7%) |
| Combined | 39/40 | 40/40 | 40/40 | 39/40 | 37/40 | 19/20 | 20/20 | 18/20 | 19/20 | 18/20 | **289/300 (96.3%)** |

## Failure Analysis

All 11 failures break down into 3 patterns:

### Pattern 1: Level Name Shift (8/11 failures)

The prompt contains `concept_name: LevelName` but the LLM returns `concept_name: AdjacentLevelName`. The conpect name is correct but the level is off by one notch in either direction.

| Prompt | Returned | Shift |
|--------|----------|-------|
| `Occasional 8th Note Spacing` | `Present 8th Note Spacing` | +1 (less extreme) |
| `Significant Half Note Spacing` | `Primary Half Note Spacing` | +2 (less extreme) |
| `Low Success` | `Very Low Success` | +1 (more extreme) |
| `Defining Medium Duration` | `Primary Medium Duration` | -1 (less extreme) |
| `Present Short Spacing` | `Primary Short Spacing` | -1 (more extreme) |

**Root cause:** The LLM does not treat the level name as an opaque identifier to be copied. It reads the semantic meaning of the level name (e.g. "Occasional" = light presence) and independently selects what it considers the appropriate level. The semantic content of level names is interpreted, not reproduced.

### Pattern 2: Concept Name Swap (2/11 failures)

The prompt correctly includes `grid_success_pct_X: level_name` but the LLM returns `grid_attempt_pct_X` with the correct level instead. The concept name is swapped to the paired variant.

**Root cause:** The `pair_with` mechanism from the prompt builder (which renders grid_success and grid_attempt as a paired concept) causes the LLM to treat them as interchangeable. Even a literal prompt can't override this structural coupling.

### Pattern 3: Cross-Concept Level Name (1/11 failure)

`harmonic_density_pct_3_notes: Defining 3 Notes` → returned `Defining 1 Note`. The LLM returned a level name belonging to `pct_1_note` for the `pct_3_notes` concept. Sibling concepts with similar level structures (`Defining X Notes` for X=1..6+) are cross-confused.

**Root cause:** Near-identical level structures across sibling concepts cause the LLM to mix up which level name belongs to which concept.

## Conclusion

Test 1 establishes a **96.3% baseline for literal reproduction**. Even with the exact concept and level name in the prompt, the LLM does not copy mechanically — it interprets and occasionally adjusts. This is an important finding for the thesis: the LLM treats concept/level pairs as semantic descriptions, not opaque identifiers.

The 3.7% gap is not noise — it reveals the LLM's inherent behavior pattern: level names are interpreted, not copied, and sibling concept structures are interchangeable in the model's representation space.
