# Corrections Plan — Remaining Issues After 1st Round

Priority ranking from the 1st-round synthesis. P0-P2 are actionable; P3-P5 are refinements. Bottom two are model-level behaviors accepted for now — to discuss after P0-P5 are closed.

---

## P0 — Metadata Category Interpretation (DONE)

Rewrote `[METADATA]` interpretation in `llm_categories.py` from *"Most musical queries should focus on other dimensions instead"* to neutral guidance. Fixed `time_sig_num`/`den` to carry actual values. Hid `note_count` and `midi_program_number` from LLM surface (weight=0.0) after giving them real levels for storage.

**Status:** ✅ Verified — 96.7% metadata accuracy in post-fix test. No header rename needed.

---

## P1 — Grid Success / Attempt Coupling

The `pair_with` mechanism renders `grid_success` / `grid_attempt` as a unit. The LLM treats them as interchangeable and drops `grid_success` when under load. 7 failures in test 6 alone. Also manifests in literal mode (test 1) and audited runs.

**Specific concepts affected:** All `grid_success_pct_*` variants — `drum_kick_grid_success_pct_odd1`, `drum_snare_clap_grid_success_pct_beat3`, `drum_hats_cymbals_grid_success_pct_odd1/even1`, `drum_toms_others_grid_success_pct_odd1/even1`, `grid_success_pct_2and4`, etc.

**Possible approaches:**
- Prompt design: add explicit instruction that success and attempt are distinct required outputs
- Unpair the concepts: render `grid_success` separately from `grid_attempt` instead of as a paired unit
- Accept the behavior if omission is acceptable for search (success implies attempt anyway)

---

## P2 — Dynamics / Prevalence Deprioritization (CLOSED — Not Actionable)

Previously identified as `dynamics_max_velocity` dropped in favor of average velocity, and `prevalence_*` concepts dropped in favor of activity concepts.

**Re-evaluation:**
- `dynamics_max_velocity` vs `dynamics_average_velocity` — these measure the same musical intuition (loudness). The LLM picking one over the other is harmless for search. The "extras are acceptable" criterion covers this.
- `prevalence_*` was tested with over-specific expectations (e.g., expecting `drum_prevalence_snare_clap_snare_1` when the query said "almost no snare"). The LLM correctly interpreted "snare" as the family level and returned family-level activity concepts. The test was wrong, not the LLM.

**Status:** ❌ Not actionable — existing LLM behavior is correct. The failures were test artifacts.

---

## P3 — Interval Detail vs Summary (DONE)

Added interval-name metadata to all detail interval concepts (`profile_harmonic_intervals_pct_00–24_semitones`, `profile_melodic_intervals_pct_asc/desc_1–12_semitones`) that were previously bare number wrappers. Each concept now has `llm_description`, `llm_interpretation`, and `llm_examples` mapping semitone values to musical interval names (e.g., `07=perfect fifth`, `12=octave`). Updated `_render_concept_group` in `prompt_builder.py` to show the mapping in group descriptions.

Sub-issues re-evaluated:
- **Harmonic↔melodic confusion** — old test queries were ambiguous ("unisons", "tritones" without modality). Not an LLM issue. New test confirmed correct modality selection when the query is explicit (4/4 harmonic, 4/4 melodic).
- **Compound interval naming** — old test had semitone-to-music-theory mismatches (e.g., "15th" ≠ 15 semitones). Test artifact.  
- **Summary vs detail** — resolved: detail concepts now have rich metadata and compete with summary concepts.

**Status:** ✅ Verified — 14/14 trials pass (100%). Detail concepts correctly preferred over summary when specific intervals are named.

---

## P4 — Piece Confusion in Natural Language (CLOSED — Not Actionable)

Previously flagged as the LLM attributing concepts to the wrong drum piece: "heavy lilt" → swing on hi-hats instead of kick; "backbeat swing" → attributed to hi-hats; open hat omitted when "hi-hat" mentioned generically.

**Re-evaluation:**
- All three cases involve queries where the piece is *implied* but not *explicitly stated*. The LLM defaults to hi-hats for swing/timing concepts because hi-hats are the most common carrier of those attributes — a reasonable semantic default.
- When a query *does* explicitly name a piece (e.g., "snare backbeat"), the LLM correctly constrains output to that piece. The existing test data confirms this.
- For search, a user searching "heavy lilt" or "backbeat swing" would get useful results whether the tagged piece is kick, snare, or hi-hats. Precision on piece attribution for implied references is not a meaningful search requirement.

**Status:** ❌ Not actionable — existing LLM behavior is correct. The failures were test expectations being too strict about implicit piece attribution.

---

## P5 — Register Specifics Dropped (CLOSED — Not Actionable)

`register_spread` and `register_lowest` dropped in favor of `register_median` / `register_highest` under load (#99, #114). Same pattern as P2/P3/P4 — `register_median: Sub-Bass` vs `register_lowest: Sub-Bass` is equivalent for search. "Extras are acceptable" covers this.

**Status:** ❌ Not actionable — existing LLM behavior is acceptable for search.

---

## To Discuss

These two patterns are model-level behaviors identified as "accepted" in the 1st-round analysis. Not actionable with current approach, but worth discussing whether they should be addressed differently.

### Direction / Level Calibration Addressed

The LLM interprets level names semantically and has a central tendency bias — it pulls extreme levels ("Occasional", "Defining") toward the middle ("Present", "Primary").

Updated the `GLOBAL_INSTRUCTIONS` in `prompt_builder.py` with a new **LEVEL INDEX ANCHORING** section that replaces the previous vague intensity guidance. Key changes:
- Explicit index mapping: index 0 = maximum extreme, index N-1 = minimum/absent
- Strong language rule: "absolutely", "relentlessly", "always" must map to index 0 or N-1, not index 1 or N-2
- Mid language rule: "somewhat", "fairly", "moderately" should map to middle indices
- Concrete 5-level example given: "0=Defining, 1=Primary, 2=Significant, 3=Present, 4=Occasional. Strong language must map to 0 or 4, not 1 or 3."

**Status:** 🔧 Fix applied. Needs a dedicated test to verify the central bias is reduced.

### Capacity Ceiling at ~8+ Concepts

Accuracy degrades ~1-2% per additional concept with no sharp cliff. At combo 10, example-based prompts hit ~86% and sentences hit ~65-73%. The model simply cannot track that many distinct concepts simultaneously.

**Root cause:** Model-level working memory / attention capacity. Not fixable.

**Open questions:**
- Should we enforce a practical limit on concept count per query (e.g., cap at 7)?
- For queries exceeding the cap, should we run multiple passes and merge?
- How does chunking the output (split concepts across multiple LLM calls) affect accuracy?
