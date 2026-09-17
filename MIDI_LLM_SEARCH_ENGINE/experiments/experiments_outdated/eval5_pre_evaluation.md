# Eval 5 — Automatic Pre-Evaluation

*Pre-evaluation of the musical-query bank (`evaluation_5_musical_queries.json`) — its
composition, query-type balance, concept coverage, and answer-concept prevalence.
Based on the current 100-query set, with fresh answers for the changed queries.*

---

## 1. Query structure

- **100 queries total: 60 pitched / 40 drum.**
- Ordered as **30 pitched / 20 drum / 30 pitched / 20 drum**:

| Block | Position | Family | Size | Role |
|-------|----------|--------|------|------|
| Block 1 | top 50 | pitched | 30 | maximal coverage |
| Block 2 | top 50 | drum | 20 | maximal coverage |
| Block 3 | bottom 50 | pitched | 30 | redundant (bottom) |
| Block 4 | bottom 50 | drum | 20 | redundant (bottom) |

The **top 50 = Block 1 + Block 2** is designed for maximal concept coverage;
redundancies are pushed to the bottom 50.

---

## 2. Query types (by `subtype`)

| subtype | top 50 | bottom 50 | all 100 |
|---------|-------:|----------:|--------:|
| technical | 14 | 12 | 26 |
| vibe-technical | 8 | 9 | 17 |
| vibe | 7 | 3 | 10 |
| genre | 4 | 4 | 8 |
| genre-artist | 5 | 3 | 8 |
| genre-technical | 1 | 6 | 7 |
| genre-vibe | 3 | 1 | 4 |
| technical-vibe | 1 | 3 | 4 |
| emotional | 2 | 2 | 4 |
| genre-emotional | 2 | 1 | 3 |
| vibe-emotional | 0 | 3 | 3 |
| technical-genre | 2 | 1 | 3 |
| technical-emotional | 1 | 0 | 1 |
| emotional-genre | 0 | 1 | 1 |
| emotional-technical | 0 | 1 | 1 |
| **Total** | **50** | **50** | **100** |

Observations: technical and vibe-technical dominate (43/100); genre-artist references
are concentrated in the top 50 (5 of 8); the bottom 50 holds most of the
emotional/vibe-emotional entries.

---

## 3. Concept coverage

Active taxonomy: **283 concepts**.

| Subset | Concepts surfaced | Share |
|--------|------------------|-------|
| Top 50 | **123** | 43.5% |
| Bottom 50 | 78 | 27.6% |
| All 100 | **123** | 43.5% |

- **The bottom 50 adds 0 new concepts** — every concept it surfaces is already in
  the top 50 (confirmed the top 50 has maximal coverage; redundancies are in the bottom).
- **Not covered: 160 concepts (56.5%)**, grouped by category:

| Category | Count | Examples |
|----------|------:|----------|
| rhythm | 87 | grid attempt/success positions (pitched + all drum pieces), spacing/duration `*_share` bins, `medium_profile`, `turnaround_shift` |
| melody | 26 | per-semitone `profile_melodic_intervals_pct_asc/desc_*` bins |
| voicing | 28 | per-semitone `profile_harmonic_intervals_pct_*` bins, `texture_mono_vs_chords_register`, `texture_pct_3/5/6+_notes`, `texture_polyphonic_burst_rate` |
| drums | 14 | specific cymbal/ride/crash/tom `drum_prevalence_*` variants |
| metadata | 3 | `metadata_root_key`, `metadata_time_sig_den`, `metadata_time_sig_num` |
| dynamics | 1 | `drum_hats_cymbals_dynamics_intensity_trend` |
| tonality | 1 | `tonality_unique_pitches_count_trend` |

### Why the uncovered concepts are fine

These 160 are almost entirely **fine-grained / distributional features** that natural
language does not elicit: rhythmic share bins (16th/32nd/8th/…), grid positions beyond
`offbeat`/`2and4`, per-semitone interval-profile bins, and specific kit-piece
prevalence. The model surfaces the **aggregates** instead (`duration_long_profile`,
`rhythmic_density_average_events_per_beat`, `groove_macro_jitter`, etc.).

This is **not a retrieval gap**, because:
1. **Eval 1 (literal)** and **eval 2 (examples)** cover every one of these concepts
   exhaustively — they prove the model can route them when named.
2. The **scorer retrieves by exact tag**: any user query that maps to one of these
   concepts finds the tagged files, even if natural/quiby queries don't elicit them.
3. Eval 5 measures *natural-query elicitation*, which by nature reaches salient
   aggregate descriptors, not fine-grained bins.

So the uncovered set is expected, documented, and reachable through other layers.

### Uncovered concepts, by subcategory

*Counts reflect the available run results; the current 100-query set (with the drum
additions) surfaces roughly 22 more concepts, mostly drum/rhythm, so the true gap is
~160 rather than the sums below. The subcategory reasons hold regardless.*

#### Drums (100)

| Subcategory | Count | Why it's fine it's not covered |
|-------------|------:|--------------------------------|
| grid | 35 | grid attempt/success positions beyond `offbeat`/`2and4`; the model surfaces the salient backbeat/offbeat, not beat3/even1/odd1 or most drum-piece positions |
| spacing | 37 | per-duration `*_share` bins + `long/medium_profile`; the model uses `short/long_profile` instead |
| prevalence | 18 | specific cymbal/ride/crash/tom prevalence + whole-family aggregates — fine-grained kit-piece presence; the model uses the main-piece prevalence |
| dynamics | 4 | per-piece `intensity_trend` + `velocity_spread` — niche; the model uses aggregate velocity |
| rhythmic density | 4 | per-piece `burstiness/trend/turnaround`; the model uses `average_events_per_beat` + `bar_to_bar` |
| groove | 2 | toms/others `groove_macro_jitter` + `swing_shuffle_ratio` — niche per-piece groove variants |

#### Pitched (82)

| Subcategory | Count | Why it's fine it's not covered |
|-------------|------:|--------------------------------|
| melodic intervals | 26 | per-semitone `asc/desc` profile bins — near-duplicate fine-grained bins; the model uses median + asc/desc aggregates |
| harmonic intervals | 23 | per-semitone harmonic profile bins — same, fine-grained |
| duration | 8 | `duration_*_share` bins + `medium_profile`; the model uses `long/short_profile` and `duration_quarter_share`  |
| grid | 7 | grid attempt/success positions beyond `offbeat`/`2and4`; the model surfaces the salient backbeat/offbeat |
| spacing | 7 | `spacing_*_share` bins + `medium_profile`; the model uses `short/long_profile` |
| texture | 6 | `texture_pct_3/4/5/6+`, `texture_mono_vs_chords_register`, `texture_polyphonic_burst_rate` — richer voicings; the model uses `texture_polyphonic_pct` + `pct_1/2` |
| metadata | 3 | `root_key`, `time_sig_num/den` — structural facts, rarely the point of a "sound" query |
| rhythmic density | 1 | `turnaround_shift` — niche |
| tonality | 1 | `unique_pitches_count_trend` — niche |

---

## 4. Answer-concept prevalence (histogram)

Frequency = how many queries in that subset surface the concept.

### Top 50
| frequency | # concepts |
|----------:|-----------:|
| 1 | 61 |
| 2 | 30 |
| 3 | 11 |
| 4 | 7 |
| 5 | 5 |
| 6 | 2 |
| 7 | 1 |
| 8 | 1 |
| 10 | 2 |
| 12 | 1 |
| 13 | 1 |
| 30 | 1 |

Top concepts: `metadata_instrument_family` (30), `duration_long_profile` (13),
`dynamics_average_velocity` (12), `register_median_note_midi` (10),
`rhythmic_density_average_events_per_beat` (10), `texture_polyphonic_pct` (8).

### Bottom 50
| frequency | # concepts |
|----------:|-----------:|
| 1 | 25 |
| 2 | 18 |
| 3 | 10 |
| 4 | 5 |
| 5 | 7 |
| 6 | 4 |
| 7 | 3 |
| 8 | 1 |
| 10 | 1 |
| 12 | 1 |
| 13 | 2 |
| 27 | 1 |

Top concepts: `metadata_instrument_family` (27), `rhythmic_density_average_events_per_beat` (13),
`groove_macro_jitter` (13), `texture_pct_1_notes` (12), `dynamics_average_velocity` (10).

### All 100
| frequency | # concepts |
|----------:|-----------:|
| 1 | 38 |
| 2 | 19 |
| 3 | 16 |
| 4 | 12 |
| 5 | 6 |
| 6 | 7 |
| 7 | 4 |
| 8 | 4 |
| 9 | 3 |
| 10 | 3 |
| 11 | 1 |
| 12 | 1 |
| 13 | 1 |
| 14 | 1 |
| 17 | 2 |
| 18 | 2 |
| 22 | 1 |
| 23 | 1 |
| 57 | 1 |

Top concepts: `metadata_instrument_family` (57), `rhythmic_density_average_events_per_beat` (23),
`dynamics_average_velocity` (22), `texture_pct_1_notes` (18), `duration_long_profile` (18),
`register_median_note_midi` (17).

---

*Interpretation: the top 50 covers the full surfaced set with a long tail of
single-use concepts (61 at freq 1); the bottom 50 is more concentrated on the
prevalent core; `metadata_instrument_family` + the aggregate rhythm/dynamics/register
concepts dominate prevalence across the whole bank.*
