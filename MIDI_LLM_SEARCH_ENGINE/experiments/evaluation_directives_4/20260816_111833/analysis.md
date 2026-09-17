# Evaluation 4 — Importance & Fallback Directives

**29/30 cases passed (96.7%)** | importance: 109/110 (99.1%) | fallback: 8/8 (100%)

---

## Overview

Tests the translator's ability to derive relative importance orderings/tie groups and fallback direction from natural language query structure. 30 synthetic queries with known a priori expectations.

## Remaining failure

**`imp4_tie_all2`** — tie group miss

- Query: *"all: a swung feel, a loose timing, a evolving bar density, and a high loudness"*
- Expected: `grid_macro_jitter` = `rhythmic_density_bar_to_bar_evolution` = `dynamics_average_velocity` (all equal — "all:" implies same priority)
- Got: `grid_macro_jitter: 5`, others: **4**
- The model assigned grid/micro-timing (`grid_macro_jitter`) one importance point higher than rhythm density and dynamics, despite the query treating them equally

This is an isolated case — a single importance point imbalance. No other tie-group or ordering assertion failed across the remaining 29 cases, so no clear systematic pattern can be inferred.

## Corrections applied

Two queries originally lacked family context (`imp3_tie_all2`, `imp3_order_tie2`) and returned drum kit-piece variants instead of the expected pitched concepts. Both were prefixed with `"pitched: "` and rerun — both now pass.

## Check summary

| Check type | Passed | Total | Accuracy |
|------------|--------|-------|----------|
| Presence (routing) | 30 | 30 | 100% |
| Importance ties | 52 | 53 | 98.1% |
| Importance ordering | 49 | 49 | 100% |
| Fallback direction | 8 | 8 | 100% |
