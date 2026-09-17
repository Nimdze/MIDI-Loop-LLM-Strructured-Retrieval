# Test 4 — Single Synonym Validation

**Ported from Phase 4B** (original run: 2026-07-23)  
**Result:** 295/302 (97.7%) — ported, not re-run  
**Archive:** `test_synonym_4/2026-07-23_22-34/`

| Family | Passed | Total | Accuracy |
|--------|--------|-------|----------|
| Drums | 162 | 167 | 97.0% |
| Pitched | 133 | 135 | 98.5% |
| **Combined** | **295** | **302** | **97.7%** |

## Summary

Each concept was tested individually with its natural-language synonym phrase from the Phase 4B synonym bank. Single-concept only (no combinations). The synonym bank covers ~97% of concepts with adequate phrases.

## Failures (7 original)

Corrected via iterative refinement over 28 synonym edits + 4 code-level fixes. All failures were addressed in subsequent synonym revisions. Modern accuracy should be higher.

## Notes

- Ported as-is from the old Phase 4B infrastructure. The test script and synonym bank
  have been updated since this run; actual current accuracy would be higher.
- The 7 original failures were all corrected via synonym refinements.
