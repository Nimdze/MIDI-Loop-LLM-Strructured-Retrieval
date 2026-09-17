# Pairing Corrections — Post-Fix Validation

**Date:** 2026-07-30
**Experiment:** `exp_corrections_round_1/pairing_corrections/20260730_121146`
**Test script:** `tests/fix_tests/pairing_test.py`
**Model:** deepseek-v4-flash

## Changes Applied

1. **`prompt_builder.py` line 152** — Removed the skip that blocked `"success"` and `"denominator"` paired concepts from being rendered. Previously, only the "attempt" (or "num") concept appeared as a standalone entry; the "success" (or "den") concept was invisible as a returnable target.

2. **`prompt_builder.py` `_format_concept`** — Replaced the nested paired-dimensions rendering. Previously, when a concept had `paired_dimensions`, the other concept's levels were rendered as a sub-section under the primary concept. Now each concept in a pair renders fully independently with its own description, levels, and a cross-reference line:
   ```
   Paired with: drum_kick_grid_success_pct_odd1
   NOTE: drum_kick_grid_attempt_pct_odd1 and drum_kick_grid_success_pct_odd1 are a pair — both must always be returned together.
   ```

3. **`metadata.py`** — Added `pair_with="metadata_time_sig_den"` / `pair_role="num"` and `pair_with="metadata_time_sig_num"` / `pair_role="den"` to the time signature concepts so they use the same pairing mechanism.

## Results

| Metric | Value |
|--------|-------|
| Total trials | 14 |
| Grid pair pass | 7/7 (100%) |
| Time sig pair pass | 4/4 (100%) |
| Mixed pair pass | 1/1 (100%) |
| **Overall pair pass** | **12/12 (100%)** |
| Negative controls (no spurious) | 2/2 (100%) |

### Detailed per-trial results

| # | Trial type | Prompt | Pairs checked | Result |
|---|-----------|--------|---------------|--------|
| 1 | Grid | kick nails the downbeats with perfect accuracy | odd1 attempt + success, even1 attempt + success | ✅ both pairs complete |
| 2 | Grid | snare hits two+four with tight placement | 2and4 attempt + success | ✅ complete |
| 3 | Grid | hi-hats consistently land offbeats with precision | offbeat attempt + success | ✅ complete |
| 4 | Grid | ghost notes that always land perfectly | offbeat attempt + success | ✅ complete |
| 5 | Grid | beat three snare crack is super consistent | beat3 attempt + success | ✅ complete |
| 6 | Grid | backbeats hit very consistently across instruments | 2and4 attempt + success (pitched) | ✅ complete |
| 7 | Grid | kick occasionally hits but often misses | odd1 attempt + success (both low) | ✅ complete |
| 8 | Time sig | 3/4 waltz feel | num + den | ✅ complete |
| 9 | Time sig | in 6/8 time with a driving groove | num + den | ✅ complete |
| 10 | Time sig | time signature of 7/8, odd meter | num + den | ✅ complete |
| 11 | Time sig | 4/4 drum groove with swing | num + den (drums context) | ✅ complete |
| 12 | Mixed | snare nails two+four in a 6/8 swing pattern | 2and4 pair + num+den pair | ✅ both pairs complete |
| 13 | Control | very fast dense drum break with high velocity | — | ✅ no spurious pairs |
| 14 | Control | slow dreamy pad with lots of reverb | — | ✅ no spurious pairs |

## Comparison With Pre-Fix Baseline

The old test 6 analysis documented **7 grid-success-missing failures** — the LLM returned `grid_attempt` but not `grid_success` even when the prompt implied success ("lands perfectly"). The root cause was structural: `grid_success_pct_*` was never rendered as an independently returnable concept.

After the fix, **100% of paired trials returned both concepts.** The single trial most comparable to the old failure pattern — trial #2 "snare hits the two and four with really tight placement every time" — returned both `drum_snare_clap_grid_attempt_pct_2and4` and `drum_snare_clap_grid_success_pct_2and4`. The old failure pattern is eliminated.

Trial #12 tested the hardest scenario — a grid pair AND a time sig pair simultaneously under musical load ("snare nails two+four in 6/8 swing pattern"). All four concepts were returned. The pairs coexist without conflict.

## Edge Cases

- **Trial #7** — "kick occasionally hits the downbeat but often misses the mark" — the LLM returned both attempt and success at low levels. The pair instruction works bidirectionally (low signals require both too), not just for high-confidence signals.
- **Negative controls** — No spurious paired concepts appeared in prompts that didn't mention them. The pairing instruction is context-dependent, not blanket.

## Conclusions

1. **The skip was the bug.** Removing the `"success"` / `"denominator"` skip from the grouping loop and rendering both concepts independently was sufficient. The old approach of nesting success under attempt was actively harmful.

2. **The cross-reference instruction works.** The `Paired with:` / `NOTE:` lines reliably communicate that both concepts must be returned together. The LLM respected this across all 12 paired trials.

3. **Grid and time sig pairs coexist without interference.** Trial #12 proved that multiple pair types in the same query don't conflict.

4. **Time sig num/den are now treated as a unit.** Previously `time_sig_num` and `time_sig_den` were independent concepts with no visible relationship. Now they're explicitly paired, matching user expectations ("3/4" means both concepts).

## Possible Refinements

- The `NOTE` text could be parameterized per pair type ("grid" vs "time signature") for more natural phrasing, but the generic version works.
- If prompt length is a concern, paired concepts add ~80 extra lines to the taxonomy (~10 positions × 4 kit pieces × 2 concepts each). This is negligible.
