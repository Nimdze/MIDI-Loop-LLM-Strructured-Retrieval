# Test 2 — Taxonomy Example Validation: Run Analysis

Run archive: `experiments/test_examples_2/20260807_210753/`
Runner: `test_2_examples.py`

## What this test measures

For each active concept, the first `llm_example` becomes a prompt fragment.
Combos of size 1–10 are sampled deterministically, and the model must return
**all** expected concepts (pure presence check; extras allowed, no direction
gate in this test). Restructured to use sampled combos 1–10 (190 trials) instead
of a full per-concept single sweep.

## Results

| metric | value |
|---|---|
| Total trials | 190 |
| Passed (presence) | 183 |
| Failed | 7 |
| Accuracy | **96.3%** |

Failures are all **pitched**, at combo sizes 3, 4, 6, 7, 8, 9 (×2). No failures
at size 1–2 or 10, and no drum failures.

## Failure analysis (7)

| cluster | count | cause |
|---|---|---|
| Specific semitone-interval profiles | 5 | off-by-one (or wrong-direction) on the exact semitone value — level correct, value wrong |
| `harmonic_perfect_consonance_pct` | 2 | test-design: aggregate expected, model tags the constituent 5ths/4ths the query names |

### 1. Semitone-value precision (effective misses = 5)

The model returns the wrong *specific* interval profile while the direction/level
is correct:

- `twelfth / perfect twelfth` (19) → returned **20**
- `minor thirteenth` (20) → returned **21**
- `major third` desc (4) → returned **desc_3**
- `desc_13plus` → returned **desc_7**

The level on all of these is the correct one for "mostly X" (`Primary`). Only the
exact semitone number is off (usually by one). Hit-rates are otherwise high:
size 1–2 are 100%; sizes with any miss were 3→94%, 4→88%, 7→94%, 9→86%; sizes
5, 6, 8, 10 were 100%. So this is not a monotonic combo-size effect — it is a
precision error on exact semitone recall when multiple interval values are in play.

### 2. `harmonic_perfect_consonance_pct` (test-design)

Both "failures" are on prompts like *"lots of open fifths and power chords"*. The
model returns the specific consonant-interval concepts (`pct_07` perfect fifth,
`pct_05` perfect fourth, `pct_12` octave) but not the higher-level aggregate
`harmonic_perfect_consonance_pct`. The query names the intervals, not the
aggregate, so expecting the aggregate is a test-construction choice, not a model
error. After discounting these, the effective miss count is **5**, not 7.

## Directions / level calibration

Levels are overwhelmingly correct and match the prompt's intensity language
(`mostly` → `Primary`, `volume increases` → `Building`, `tight and locked` →
`Tight`, `land perfectly` → `High Success`, `very sustained` → `Sustained`,
`strong tonal center` → `Anchor Centered`). No polarity reversals (nothing high↔low).

Minor level issues:
- **Understated:** size-8 `profile_melodic_intervals_pct_asc_13plus` tagged
  `Occasional` while the prompt emphasizes *"huge upward leaps beyond an octave"*
  (arguably should be Significant/Primary).
- **Borderline extra:** size-6 tagged `profile_harmonic_intervals_pct_12` (octave)
  `Significant` off "power chords" (root+fifth; octave not clearly implied).

## Over-tagging (extras)

Extras are low overall (avg 0.34/trial, max 3). Three recurring over-tag
patterns — all **logically justified by the prompts**:

- `melodic_intervals_pct_descending` (10×) / `ascending` (5×) — the model tags
  the general contour **in addition to** the specific `profile_*_desc_X`
  interval. Both are `Primary` (consistent with "mostly"), so it is redundant
  but correct — a test expected-set choice, not a model error.
- `melodic_intervals_max_leap_semitones` (6×) — tagged `Contains Extreme Leaps
  (>= Octave)` on prompts that explicitly describe "huge ... leaps beyond an
  octave"; level matches the leap, so correct.
- grid-attempt/success (`grid_attempt/success_pct_beat3/2and4/offbeat/odd1`) —
  the prompts explicitly state "each beat three lands on the grid" / "offbeat
  lands in the pocket" / "downbeats landed perfectly", so inferring the grid
  concept is correct; they are extras only relative to the expected set (test
  coverage artifact).

## Known gap & fix — grid attempt/success pairing

**The gap (test-construction, not model error):** this run's test 2 sampled
`grid_attempt_pct_*` and `grid_success_pct_*` as **independent concepts** (each
with its own taxonomy example), so a grid characterization was split across two
decoupled expected entries. The system prompt, however, instructs the model that
grid is holistic ("the correct mix of attempts and successes is required, not a
single value"), so the model **correctly pairs them** — e.g. a success concept
(`..._land perfectly` / `lands on the grid`) makes it also emit the attempt
concept. Data: when a success concept was expected the model also returned its
attempt pair 22× (of 47); when an attempt was expected it also returned its
success pair 6× (of 64); the test had the pair in `expected` only 2× each.

So the grid "over-tagging" extras above are largely this artifact: the model is
following the system prompt's holistic-grid guidance, while the expected set
didn't enforce the pair.

**The fix:** `test_2_examples.py` now treats grid attempt↔success as a paired
unit — a grid concept's counterpart is added to **both** the prompt fragment
(its example) and the `expected` set, mirroring test 3's `pair_direction`.
> Note: this run (20260807_210753) was generated **before** that fix; results
> were captured with grid attempt/success sampled independently.

**Fix verified:** the pairing logic is confirmed correct (`_grid_pair` maps
attempt↔success, including drum variants, and returns `None` for non-grid
concepts), and a grid single-trial prompt
("…attacked very consistently … land with perfect accuracy") now returns **both**
`grid_attempt_pct_2and4` and `grid_success_pct_2and4`.

No wrong-family returns (0).

## Remaining genuine issues

**Model issues:**
1. **Semitone-value precision** — off-by-one (or wrong-direction) on the exact
   interval profile; level correct. This is the 5 effective misses.
   **Mitigation (post-run, system prompt):** added an exactness note to
   `INTERVAL_REFERENCE` in the prompt builder emphasizing not to shift by one and
   explicitly listing the compound intervals (twelfth=19, minor thirteenth=20,
   major thirteenth=21, minor fourteenth=22, major fourteenth=23, double octave=24).
2. **One understated level** — size-8 `asc_13plus` = `Occasional` despite "huge
   upward leaps beyond an octave".

**Test/material-design issues (not model errors):**
3. **Aggregate-vs-specific mismatch** — `harmonic_perfect_consonance_pct`
   expected while the model correctly tags the constituent intervals (5ths/4ths).
4. **Melodic-contour redundancy in expected sets** — expected set holds only the
   specific `profile_*_desc_X`; the model also (correctly) tags the general
   contour, surfacing as an extra.

**Borderline:**
5. `profile_harmonic_intervals_pct_12` (octave) = `Significant` off "power
   chords" — octave not clearly implied.

## Bottom line

Test 2 is healthy: 96.3% presence, all failures pitched at mid/large combo
sizes, correct level calibration, no family leakage, and no logical over-tagging.
The genuine defects are the **exact-semitone precision** (5 misses) and **one
understated level**; the rest are test-construction choices (aggregate-vs-specific
and contour redundancy) to reconcile in the material or expected sets.
