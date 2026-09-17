# Test 1 — Literal Tag Reproduction — 05/08/2026

**Result: 298 / 300 (99.33%)**

Provider: DeepSeek (`deepseek-v4-flash`), concurrency 50, on the current (post-rename) taxonomy.
Source run: `experiments_outdated/test_literal_1/20260805_111836`.

| | total | passed | accuracy |
|---|---|---|---|
| drums | 150 | 149 | 99.3% |
| pitched | 150 | 149 | 99.3% |

Combo sizes 1–10 all at ≥ 95%, most at 100%.

## Pipeline fixes applied before this run

- **Prefer `level_index` over `level_name`** in `_resolve_targets`: when the model emits both a `level_index` and a (possibly slightly-wrong) `level_name`, the index now wins. This was the main correctness fix (was silently dropping targets / retrying into empty).
- **Reject empty `targets`** in `translate()`: an empty target set is treated as a failed translation and retried, not accepted.
- **Prompt:** OUTPUT SCHEMA now marks `level_index` as the preferred field, and the instructions state "never return an empty targets list".

## Failures (2 / 300)

Both remaining failures are in `drums` combos and involve a `metadata` concept:

### 1. `metadata_instrument_family` — TEST FAIRNESS ISSUE (not a system defect)

- Combo 4 (drums), prompt included `metadata_instrument_family: Choir/Voice`.
- `metadata_instrument_family` is correctly flagged `['pitched','drums']`, but its **levels are mostly pitched instruments** (Piano, Guitar, Bass, Strings, Synth Lead, Choir/Voice…); the only valid level for a drum loop is `Drum Kit`.
- The sampler drew a pitched-only level (`Choir/Voice`) into a drums combo. The model **correctly declined** to tag a drum loop as `Choir/Voice`, so the concept was counted missing.
- This is a **test-sampling artifact**, not a model or pipeline failure: a pitched instrument-family level can never legitimately apply to a drums query.
- **Fix applied to `test1_literal.py`:** `metadata_instrument_family` now samples only `Drum Kit` for drums combos, and excludes `Drum Kit` for pitched combos. (Not rerun; the archived results above are from the pre-fix sampler.)

### 2. `metadata_time_sig_num` — MODEL RECALL MISS (not a pipeline problem)

- Combo 8 (drums), prompt included `metadata_time_sig_num: 13`; the model returned the other 7 pairs and omitted this one (`returned` had 7 targets, `missing=[metadata_time_sig_num]`, no extras).
- Checked and ruled out a pipeline cause:
  - `metadata_time_sig_num` is correctly flagged `['pitched','drums']` (applies to drums).
  - Level `13` is a valid level (levels are `1`–`16` + `Other`).
  - No `_strip_ordinal` interference (level is a bare integer).
  - No `_is_paired_extra` interference (the model returned neither `time_sig_num` nor its pair `time_sig_den`).
  - `translate()` succeeded with 7 valid targets (no empty, no validation error), so the model simply did not emit the `time_sig_num` pair.
- Conclusion: this is the known **recall limitation at high combo sizes** (echoing 8 literal pairs, the model dropped one), not a pipeline bug.

**Supporting evidence (recall, not failure):** `metadata_time_sig_num` appeared in 7 of the 300 queries in this test and the model reproduced it correctly in **6 of 7 (85.7%)**. The only genuine miss is this single 8-combo drums case (where it omitted the concept entirely — neither `num` nor its pair `den`). So the concept itself is handled reliably; the one failure is a high-combo recall drop, i.e. exactly **1 genuine failure at 8-combo across 300 queries**.

## Notes

- At 99.3%, test1's mechanism (exact name/level reproduction) is validated; the residual failures are either a fixed test-sampling artifact or a high-combo recall miss.
- Real natural-language queries map to a handful of concepts, so the high-combo literal-echo recall limit is largely a test-only artifact.
