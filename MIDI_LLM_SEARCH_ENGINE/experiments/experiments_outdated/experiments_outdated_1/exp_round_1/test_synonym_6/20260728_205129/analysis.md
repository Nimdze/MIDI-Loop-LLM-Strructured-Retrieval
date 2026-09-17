# Test 6 — Natural Interleaved Sentences (Large Sample)

**Result:** 104/158 (65.8%)  
**Archive:** `test_synonym_6/20260728_205129/`
**Prompts:** 158 (85 drums + 73 pitched), 100% concept coverage

## Summary

Natural interleaved sentences where concepts are embedded in flowing prose
(not comma-separated lists). Each prompt contains 2-5 concepts across a mix
of instrument pieces and musical dimensions. This is the closest format to
actual user queries.

| Family | Passed | Total | Accuracy |
|--------|--------|-------|----------|
| Drums | 55 | 85 | 64.7% |
| Pitched | 49 | 73 | 67.1% |
| Combined | 104 | 158 | **65.8%** |

## Failure Patterns

54 failures total, with no dominant pattern — misses are scattered across
individual concepts (1-3 occurrences each). This is consistent with random
omission under natural language load rather than systematic errors.

The most frequently missed concepts:
- `drum_kick_duration_short_profile` (3) — sporadic
- `drum_kick_grid_success_pct_odd1` (2) — sporadic
- All others: 1 occurrence each

## Comparison With Earlier Results

| Test | Structure | Samples | Accuracy |
|------|-----------|---------|----------|
| Test 4 (single synonyms) | Single concept | 302 | 97.7% |
| Test 5 (synonym lists) | Comma lists | 275 | 83.6% |
| **Test 6 (sentences)** | **Natural prose** | **158** | **65.8%** |

The drop from lists (83.6%) to sentences (65.8%) is ~18 points. This gap
represents the cost of interleaved natural language: the LLM must parse
sentence structure to extract concepts rather than splitting on commas.

## Conclusion

Sentence structure degrades accuracy ~18% compared to structured lists.
However, the 65.8% baseline is more representative of real user input.
This is the accuracy to expect when users type natural queries into the
search interface.
