# Test 9 — Stripped Synonym Combos (Sentences)

**Ported from test7b** (2026-07-25)  
**Result:** 22/33 (66.7%) — ported, not re-run  
**Archive:** `test_synonym_9/2026-07-25_genuine_failures/`

## Summary

Natural interleaved sentences with stripped synonyms (no lexical overlap with
the taxonomy). 33 hand-written prompts targeting the 6 genuine failure patterns
identified in test 6.

After all fixes (temperature 0.01, naming correction, direction instruction,
prevalence instruction): **23/33 (69.7%)**.

## Failure Patterns in Ported Data (10 failures)

| Type | Count | Details |
|------|-------|---------|
| Omission of specific concepts | 4 | spacing_8th, snare prevalence, spacing_32nd, spacing_8th (again) |
| Direction calibration | 2 | Crash at "Present" not "Defining", above_whole at mid-level |
| Interval specifics vs broader concepts | 3 | Perfect_consonance instead of specific 07/12, etc. |
| Sibling confusion | 1 | Sloppy → high attempt (actually correct — test was wrong) |

## Effective Accuracy After Human Audit

23 passes + 5 acceptable (broader concept substitution) + 1 test issue = 
**29/33 (87.9%)** effective accuracy for natural stripped prompts.
