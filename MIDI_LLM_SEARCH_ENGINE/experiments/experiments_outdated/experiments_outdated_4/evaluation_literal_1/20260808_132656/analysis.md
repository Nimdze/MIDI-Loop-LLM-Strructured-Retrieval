# Test 1 — Literal Taxonomy Reproduction: Run Analysis

Run archive: `experiments/evaluation_literal_1/20260808_132656/`
Runner: `test1_literal.py`

## What this test measures

Literal reproduction: each prompt is a comma-joined `concept_name: level_name`
list (combos 1–10), and the model must return **all** listed concepts at the
stated levels (presence + exact level). No paraphrasing — the reference baseline
for how accurately the model echoes the exact tags.

## Change in this run

Added a **coverage guarantee** (`_ensure_covered`): a greedy top-up at size 2
ensures every active concept appears in at least one combo (previously concepts
were drawn randomly and not guaranteed to appear). This added a small number of
top-up combos — the run grew from 300 to 303 trials.

## Results

| metric | value |
|---|---|
| Total | 303 |
| Passed | 302 |
| Failed | 1 |
| Accuracy | **99.67%** |
| Coverage | every active concept appears in ≥1 combo (verified: 0 missing) |

## Failure analysis (1)

A single **size-10 drums** combo returned 9 of 10 expected concepts but dropped
`metadata_time_sig_num: 11` — an odd/rare time-signature numerator literal — in
the 10-concept prompt. This is a **recall miss at the largest combo size**, not a
routing or level error, and not related to the coverage change. Everything else
(including the top-up combos) reproduced exactly.

## Bottom line

Literal reproduction remains essentially perfect at ~99.7%. The coverage
guarantee now ensures every concept is exercised at least once (a real
improvement over the previous random sampling) without materially changing
accuracy. The lone miss is a size-10 recall drop of a rare time-signature value.
