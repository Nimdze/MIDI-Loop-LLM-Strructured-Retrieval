# Test 4 — Natural Musical Queries: Run Analysis & Scoring

Run archive: `experiments/evaluation_musical_queries_5/20260808_174937/`
Runner: `test_4_musical_queries.py` · Bank: `test_4_musical_queries.json`

## What this test measures

100 natural musical queries (vibes/imagery, technical, genre, artist, emotional
and their combinations), **no expected targets**. The model interprets each and
tags concepts. Outputs are judged with the rubric in
`test_4_musical_queries_scoring.md` — 6 axes (family, relevance, coverage,
levels, reasoning, over-tagging) 1–5 + a verdict. Semantic analysis is on, so
each tag carries a "why".

## Scoring result

Per-query scores in `scores.json`. Aggregate:

| verdict | count |
|---|---|
| **hit** | 98 |
| **partial** | 2 |
| **miss** | 0 |
| **over-tagged** | 0 |

**Axis averages (1–5):**

| axis | avg |
|---|---|
| family | 5.0 |
| relevance | 4.98 |
| coverage | **3.97** |
| levels | 5.0 |
| reasoning | 5.0 |
| over_tag | 5.0 |
| importance | 4.93 |

**Interpretation:** the model is strong on family classification, relevance,
level calibration and reasoning. **Over-tagging is not a problem (5.0)** — judged
on the `semantic_analysis` "why", the extra tags are defensible interpretations,
not invented off-topic content. The only real weakness is **coverage** (3.97) —
for a few queries the model misses an obvious salient concept (e.g. instrument
family). **Importance (7th axis)** is strong (4.93): differentiated and
well-ranked, with the salient concepts getting the highest weights.

## Output characteristics

- **Targets/query:** avg 5.75 (3–11), none empty.
- **Family:** 78 pitched / 22 drums — matches the queries' instruments.
- **Instrument-family tagging is reliable** — the model almost always emits
  `metadata_instrument_family` (violin→Strings, synth→Synth Lead/Pad,
  sax/clarinet/oboe→Reed, brass, guitar, bass, piano, organ, harp, etc.).

## Notable findings

**Cultural / artist references are correctly translated** (the genre/artist
queries): J Dilla → swung/loose hip-hop groove; Daft Punk → tight electro-funk;
Aphex Twin → glitchy/stuttering; Brian Eno → sparse ambient pads; Nine Inch Nails
→ grinding industrial; Kraftwerk → stark/minimal synth; King Tubby → bottom-heavy
dub bass; Smashing Pumpkins → loud/guitar rock; Tangerine Dream → analog lead.
No artist reference was mistranslated.

**The 2 partials:**
- `mus_020` "synth that drifts like it's daydreaming, never committing" — tagged
  straying tonal anchor + varying intervals (right idea), but under-covered the
  tonality/melodic angle.
- `mus_034` "synth with clear, ringing notes that sparkle" — missed
  `metadata_instrument_family` (Synth), a clear coverage miss.

**Over-tagging re-scored as non-issue:** cases like `mus_004` pulse → "Tight"
macro jitter, `mus_006` bass → `duration_long`, `mus_005` shimmering → `duration_long`
are defensible interpretations (their "why" is plausible), so they are **not**
penalized (over_tag = 5.0). Over-tagging is only penalized for genuinely invented
or off-topic concepts, which are not present here.

**Importance (7th axis) notes:** importance is now captured in `to_evaluate.json`
per target and scored. Only a handful of minor mis-ranks: `mus_034` ranked a
peripheral duration above its (missing) core instrument family (importance 3),
and a few queries slightly over-weighted a peripheral register/duration tag
(`mus_005`, `mus_006`, `mus_026`, `mus_069`, `mus_081` → 4). Otherwise well-ranked.

## Bottom line

Test 4 is excellent: **98/100 hits, 0 misses**, near-perfect family/relevance/
levels/reasoning, light over-tagging. The only real weakness is **coverage** —
an occasional missed salient concept (especially instrument family in a couple of
queries). Overall the model interprets natural musical language to the taxonomy
very well. Judge input is `to_evaluate.json`; scores in `scores.json`.
