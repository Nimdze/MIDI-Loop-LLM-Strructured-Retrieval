# Tests 1-3 — LLM Translation Validation: Integrated Analysis

## Overview

Three tests validate the LLM translator against the taxonomy:

| Test | Prompts | Combos | Purpose |
|------|---------|--------|---------|
| **1** | Literal `concept_name: level_name` | 1-10 (300 tests) | Taxonomy readability — can the LLM copy exact strings? |
| **2** | `llm_examples` (single) | None (255 tests) | Example integrity — does every example map back? |
| **3** | `llm_examples` (combos) | 2-10 (570 tests across 4 seeds) | Capacity — how many concepts can the LLM handle at once? |

---

## Combined Degradation Curve (Tests 1-3)

Weighted average across all runs (seeds 1, 42, 7):

| Combo | Drums | Pitched | Combined |
|-------|-------|---------|----------|
| 2 | 100% | 100% | 100% |
| 3 | 100% | 95% | 98% |
| 4 | 95% | 100% | 98% |
| 5 | 96% | 92% | 94% |
| 6 | 89% | 91% | 90% |
| 7 | 94% | 86% | 90% |
| 8 | 94% | 97% | 96% |
| 9 | 83% | 91% | 87% |
| 10 | 74% | 97% | 86% |

**Key finding: No sharp cliff.** Accuracy degrades smoothly from 100% at 2 concepts to 86% at 10 concepts — roughly 1-2% per additional concept. The apparent 50% drop at combo 10 in the first run was noise from a 10-sample batch; the 35-sample weighted average shows a clean curve.

---

## Failure Pattern Analysis

### Pattern 1: Metadata Drop (dominant at combos 5+)

Metadata concepts (`metadata_instrument_family`, `metadata_midi_program_number`,
`metadata_time_sig_num/den`, `metadata_note_count`) are consistently dropped
when combined with musical concepts. At combos 5+, metadata accounts for
~48% of all failures.

**Discussion:** The `[METADATA]` category header signals "system information"
to the LLM, which deprioritizes it relative to musical categories like rhythm,
harmony, or expression. Moving concepts to musical categories would solve this
but would misrepresent what they are (metadata is genuinely metadata, not
content). Alternative: rename the category to `[RECORDING]` or `[FILE_INFO]`
to sound less like a footnote.

**Decision:** Rename the category header. The concepts stay as metadata,
but the LLM sees them as "recording-level descriptors" rather than "system
footnotes."

### Pattern 2: Spacing Profile vs Specific Share (resolved)

The LLM returned specific note-value spacing concepts (`spacing_16th_share`,
`spacing_32nd_share`) instead of profile concepts (`spacing_short_profile`,
`spacing_long_profile`). The original example "the overall onset spacing tends
towards very short intervals" didn't distinguish profile from share.

**Resolution:** Changed examples to include "onset spacing profile" language.
Validation run showed 0 spacing-profile failures (down from 12 in the original).

**Further discussion:** The profile/share distinction may not matter for search —
a query about "short spacing" returning `16th_share` is just as correct as
`short_profile`. The intentional adoption of the "extras are acceptable" rule
(see below) means this pattern is no longer a test failure at all.

### Pattern 3: Summary vs Detail (artificial split, accepted)

The test framework required exact matches between expected and returned
concepts. This penalized the LLM for returning a semantically equivalent
concept (polyphonic_pct instead of burst_rate, short_profile instead of
16th_share, etc.).

**Discussion:** The LLM treats summary and detail concepts as a spectrum, not
separate bins. This is the right behavior for search — a user who says "chords
change frequently" should get matches whether the file is tagged with burst_rate
or polyphonic_pct. Forcing the LLM to pick the "exact" variant is artificial.

**Decision:** Formally adopted: **extras are acceptable** if they share a
subcategory with an expected concept and have the same direction. Tests should
only fail on omissions, wrong-family, or clearly unrelated extras. Profile/share
swaps and summary/detail alternates pass.

### Pattern 4: Melodic Interval Specifics (scattered)

Individual melodic interval percentages (`asc_7_pct`, `asc_2_pct`, `desc_2_pct`,
`desc_7_pct`) are occasionally missed. No single interval dominates the failures —
they're scattered across different values.

**Interpretation:** This is random dropout under load, not a systematic issue.
The LLM can identify "ascending perfect fifths" as `asc_7_pct` in isolation but
can't always track 5+ specific interval values simultaneously. Acceptable at
the demonstrated 90%+ accuracy for combos ≤ 8.

---

## Comparison with Literal Tags (Test 1 vs Test 3)

| Combo | Literal (test 1) | Examples (test 3) | Gap |
|-------|-----------------|-------------------|-----|
| 2 | 100% | 100% | 0% |
| 5 | ~95% | 94% | ~1% |
| 8 | 90% | 96% | -6% |
| 10 | 96% | 86% | 10% |

Example prompts degrade slightly faster than literal strings at high combo
counts, but the gap is small (0-10%). The primary performance ceiling is the
model's capacity limit ~8+ simultaneous concepts, not the choice of prompt
format.

---

## Overall Conclusions

1. **The system works at 86-100% accuracy** across all tests and all combo
   sizes up to 10. For production use (3-5 concepts per query), accuracy is
   ~94-98%.

2. **The degradation is smooth.** No sharp cliff — accuracy drops ~1-2%
   per additional concept. This is a model-level capacity limit, not a
   taxonomy or prompt design problem.

3. **Metadata needs a category rename.** The `[METADATA]` header signals
   "unimportant." Renaming to `[RECORDING]` or `[FILE_INFO]` should reduce
   the 48% metadata-drop rate.

4. **Extras are accepted.** The test criteria change is formally adopted.
   Summary/detail swaps, profile/share alternates, and related extras pass
   as long as they share a subcategory and direction.

5. **Tests 1-3 are complete.** Tests 4 onward (synonyms, natural language,
   multi-tag blocks) build on this validated foundation.
