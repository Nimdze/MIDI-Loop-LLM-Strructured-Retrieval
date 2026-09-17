# Test 5 — Synonym Combos (Lists)

**Ported from Phase 4D** (final validated run: 2026-07-24)  
**Result:** 230/275 (83.6%) — ported, not re-run  
**Archive:** `test_synonym_5/2026-07-24_14-25/`

| Combo | Drums | Pitched | Combined |
|-------|-------|---------|----------|
| 2 | 88% | 80% | 84% |
| 3 | 84% | 70% | 77% |
| 4 | 72% | 64% | 68% |
| 5 | 52% | — | 52% |

## Context

The original Phase 4D run tested comma-separated synonym phrases at combos 2-5.
After iterative fixes (grid coupling, ordinal markers, category reasoning, 
pre-enumerate in reasoning, max_tokens=4000), accuracy reached 83.6%.

## Fixes Applied Before This Run

- Grid attempt+success structural coupling
- Ordinal level markers [0]..[N]
- level_index resolution
- Category reasoning (rhythm, harmony)
- Spacing above_whole↔max_silence synonym rewrites
- Melodic static↔harmonic unisons fix
- Harmonic density restructure (mono/dyads removed)
- Dynamics↔rhythm decoupling

## Key Patterns

- Degradation is clear: 84% → 77% → 68% → 52%
- Direction failures (wrong level) dominated at ~70% of all failures
- Semantic substitution between sibling concepts was the second largest group

## Modern Context

Since this run, the test criteria have been relaxed (extras are acceptable),
and the prompt builder has been significantly improved. A re-run with current
infrastructure would likely show higher accuracy. Early stopping at 70% was
triggered at combo=5 for drums and combo=4 for pitched.
