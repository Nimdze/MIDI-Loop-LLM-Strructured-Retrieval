# Eval 5 — Automatic Pre-Evaluation

*Pre-evaluation of the musical-query bank (`evaluation_5_musical_queries.json`) based on
the actual run results (100 queries, 0 errors, mean lexical novelty 0.44). Covers query
composition, block-level concept coverage, and answer-concept prevalence.*

---

## 1. Run summary

- **100 queries**, 0 errors, mean lexical novelty **0.44** (vs. 0.71 for eval 6 vague queries)
- **60** self-classified as pitched, **40** as drums — matches the bank design
- **100 unique concepts surfaced** (see §3), plus 17 drum kit-piece variants shared with the
  main set = **133 total unique entries**

---

## 2. Query structure

- **100 queries total: 60 pitched / 40 drum.**
- Ordered as **30 pitched / 20 drum / 30 pitched / 20 drum**:

| Block | Position | Family | Size | Concepts surfaced |
|-------|----------|--------|------|------------------:|
| Block 1 | top 50 | pitched | 30 | 47 |
| Block 2 | top 50 | drum | 20 | 68 |
| Block 3 | bottom 50 | pitched | 30 | 51 |
| Block 4 | bottom 50 | drum | 20 | 64 |

| Subset | Concepts surfaced |
|--------|------------------:|
| Top 50 | 110 |
| Bottom 50 | 110 |
| All 100 | **133** |
| Only in top 50 | 23 |
| Only in bottom 50 | 23 |

The top and bottom halves surface an identical total (110 each) but with partial overlap —
23 concepts appear only in the top 50, 23 only in the bottom 50. The bank's split is
balanced: the top 50 carries the primary coverage, the bottom 50 probes redundancy and
adds niche drum/per-piece variants.

---

## 3. Query types (by `subtype`)

| subtype | top 50 | bottom 50 | all 100 |
|---------|-------:|----------:|--------:|
| technical | 14 | 12 | 26 |
| vibe-technical | 8 | 9 | 17 |
| vibe | 7 | 3 | 10 |
| genre-artist | 5 | 3 | 8 |
| genre | 4 | 4 | 8 |
| genre-technical | 1 | 6 | 7 |
| genre-vibe | 3 | 1 | 4 |
| technical-vibe | 1 | 3 | 4 |
| emotional | 2 | 2 | 4 |
| genre-emotional | 2 | 1 | 3 |
| technical-genre | 2 | 1 | 3 |
| vibe-emotional | 0 | 3 | 3 |
| technical-emotional | 1 | 0 | 1 |
| emotional-technical | 0 | 1 | 1 |
| emotional-genre | 0 | 1 | 1 |
| **Total** | **50** | **50** | **100** |

Observations: technical and vibe-technical dominate (43/100); genre-artist references
are concentrated in the top 50 (5 of 8); the bottom 50 holds most of the
emotional/vibe-emotional entries.

---

## 4. Concept coverage

Active taxonomy: **282 concepts**.

| Subset | Concepts surfaced | Share |
|--------|------------------|-------|
| Top 50 | **110** | 39.0% |
| Bottom 50 | 110 | 39.0% |
| All 100 | **133** | 47.2% |

- **Not covered: 149 concepts (52.8%)** — **76 drums, 73 pitched**

---

### Uncovered drums (76)

| Subcategory | Count | Examples | Why acceptable |
|-------------|------:|----------|----------------|
| spacing | 33 | `drum_*_spacing_{16th,32nd,8th,quarter,half,whole,above_whole}_share`, `drum_*_spacing_{long,medium}_profile`, `drum_*_spacing_max_silence_beats` | The model surfaces `drum_kick_spacing_{short,medium,max_silence}_profile` + `drum_*_spacing_short_profile` for most pieces; the uncovered are per-piece share bins, long/medium profiles beyond kick, and max silence beyond kick |
| grid | 22 | `drum_*_grid_{attempt,success}_pct_{beat3,even1,odd1,2and4}` | The model surfaces `drum_kick_grid_{attempt,success}_pct_{2and4,beat3,even1,odd1}` (all kick positions) and `drum_snare_clap_grid_{attempt,success}_pct_{2and4}` (snare backbeat). The uncovered are hats-cymbals/toms-others grid positions |
| prevalence | 15 | `drum_prevalence_{hats_cymbals,kick,snare_clap,toms_others}_{specific_variant}` | Fine-grained kit-piece variants; the model uses the main-piece aggregates + `metadata_instrument_family` |
| rhythmic density | 4 | `drum_{hats_cymbals,kick,snare_clap}_rhythmic_density_{trend,turnaround_shift,bar_to_bar}` | The model uses the aggregate `rhythmic_density_average_events_per_beat` |
| dynamics | 2 | `drum_{hats_cymbals,kick}_dynamics_intensity_trend` | The model uses aggregate `dynamics_average_velocity` + `velocity_spread` |
| **Total** | **76** | | |

### Uncovered pitched (73)

| Subcategory | Count | Examples | Why acceptable |
|-------------|------:|----------|----------------|
| melodic intervals | 26 | `profile_melodic_intervals_pct_{asc,desc}_{1-13+}_semitones` | Per-semitone profile bins are near-duplicate fine-grained; the model uses `melodic_intervals_absolute_median_semitones` + `pct_ascending/pct_descending` |
| harmonic intervals | 22 | `profile_harmonic_intervals_pct_{00-24}_semitones` | Per-semitone harmonic profile bins, same fine-grained issue; the model uses `harmonic_dissonance_pct` + `imperfect/perfect_consonance_pct` |
| grid | 6 | `grid_{attempt,success}_pct_{beat3,even1,2and4}` | Grid positions beyond `offbeat`/`2and4` are rarely specified in natural language |
| duration | 5 | `duration_{16th,32nd,8th,half,whole}_share` | The model uses `duration_{long,short,medium}_profile` as aggregate alternatives |
| spacing | 4 | `spacing_{32nd,half,whole,above_whole}_share` | The model uses `spacing_{short,medium,long}_profile` + `spacing_max_silence_beats` + `spacing_{8th,16th,quarter}_share` as alternatives |
| texture | 4 | `texture_pct_{2,3,5,6+}_notes` | The model uses `texture_pct_1_notes` (surface) + `texture_polyphonic_pct` (chordal) as complementary aggregates |
| metadata | 3 | `metadata_root_key`, `metadata_time_sig_num/den` | Structural metadata rarely the focus of a query |
| rhythmic density | 1 | `rhythmic_density_turnaround_shift` | Niche feature |
| register | 1 | `register_boundary_shift_semitones` | The model uses `register_spread_semitones` instead |
| tonality | 1 | `tonality_unique_pitches_count_trend` | Niche trend feature |
| **Total** | **73** | | |

### Why the uncovered concepts are acceptable

These 149 are almost entirely **fine-grained / distributional features** that natural
language does not elicit: rhythmic share bins (16th/32nd/8th/…), grid positions beyond
`offbeat`/`2and4`, per-semitone interval-profile bins, and specific kit-piece
prevalence. The model surfaces the **aggregates** instead (`duration_long_profile`,
`rhythmic_density_average_events_per_beat`, `grid_macro_jitter`, etc.).

This is **not a retrieval gap**, because:
1. **Eval 1 (literal)** and **eval 2 (examples)** cover every one of these concepts
   exhaustively — they prove the model can route them when named.
2. The **scorer retrieves by exact tag**: any user query that maps to one of these
   concepts finds the tagged files, even if natural/vibey queries don't elicit them.
3. Eval 5 measures *natural-query elicitation*, which by nature reaches salient
   aggregate descriptors, not fine-grained bins.
4. The uncovered set overlaps almost perfectly with the old pre-evaluation — the
   categories and counts are stable across bank versions.

---

## 5. Answer-concept prevalence (histogram)

Frequency = how many queries in that subset surface the concept.

### Top 50
| frequency | # concepts |
|----------:|-----------:|
| 1 | 38 |
| 2 | 28 |
| 3 | 14 |
| 4 | 7 |
| 5 | 9 |
| 6 | 3 |
| 7 | 1 |
| 8 | 2 |
| 9 | 2 |
| 13 | 1 |
| 14 | 1 |
| 15 | 2 |
| 16 | 1 |
| 32 | 1 |

Top concepts: `metadata_instrument_family` (32), `dynamics_average_velocity` (16),
`texture_pct_1_notes` (15), `register_median_note_midi` (15),
`rhythmic_density_average_events_per_beat` (14).

### Bottom 50
| frequency | # concepts |
|----------:|-----------:|
| 1 | 45 |
| 2 | 24 |
| 3 | 9 |
| 4 | 7 |
| 5 | 7 |
| 6 | 3 |
| 7 | 5 |
| 8 | 2 |
| 11 | 3 |
| 12 | 1 |
| 13 | 1 |
| 15 | 1 |
| 17 | 1 |
| 28 | 1 |

Top concepts: `metadata_instrument_family` (28), `texture_pct_1_notes` (17),
`dynamics_average_velocity` (15), `rhythmic_density_average_events_per_beat` (13),
`grid_macro_jitter` (12).

### All 100
| frequency | # concepts |
|----------:|-----------:|
| 1 | 35 |
| 2 | 24 |
| 3 | 13 |
| 4 | 11 |
| 5 | 11 |
| 6 | 8 |
| 7 | 5 |
| 8 | 2 |
| 9 | 3 |
| 10 | 4 |
| 11 | 1 |
| 12 | 2 |
| 13 | 2 |
| 14 | 2 |
| 16 | 2 |
| 18 | 1 |
| 20 | 1 |
| 21 | 1 |
| 26 | 1 |
| 27 | 1 |
| 31 | 1 |
| 32 | 1 |
| 60 | 1 |

Top concepts: `metadata_instrument_family` (60), `texture_pct_1_notes` (32),
`dynamics_average_velocity` (31), `rhythmic_density_average_events_per_beat` (27),
`register_median_note_midi` (26), `grid_macro_jitter` (21), `duration_long_profile` (20).

---

*Interpretation: the bank surfaces 133 unique concepts (47% of the active taxonomy)
with a long tail of single-use concepts (35 at freq 1). `metadata_instrument_family`
dominates prevalence (60/100 queries). The core aggregate descriptors
(rhythm/dynamics/register/texture/duration) are consistently surfaced across both
halves, while fine-grained bins remain uncovered by design.*
