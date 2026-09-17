# LLM-as-Judge Scoring Instructions — Natural Musical Queries

You are an expert music-production judge. For **each** query in
`to_evaluate.json`, evaluate the model's concept-tagging output. The model
received **only the query and system prompt** — there are no expected targets. Your job is to
judge whether the tags are a *musically sensible interpretation* of the query.

## Input per case

`id`, `query`, `subtype` (vibe / technical / genre / artist / emotional — may be
combined, e.g. `genre-artist`, `vibe-technical`; judge each category present),
`family_classification` (drums/pitched), `targets` (`concept` + `level` +
`importance` 1–5), and `semantic_analysis` (the model's per-concept reasoning —
the "why" for each tag).

> Report scores per subtype: for genre/artist queries add one extra judgment —
> did the cultural reference get translated to the *right musical character*
> (the model must know what the artist/genre sounds like, then map it to
> concepts)? For vibe/emotional/imagery queries, judge whether the inferred
> concepts match the descriptive language directly.

## Scoring axes

Score each of the following 1–5 (5 = excellent):

1. **Family classification** (`family`): is the model's drums/pitched choice
   sensible for this query? (Score 5 if sensible, 4 if debatable but defensible,
   1 if clearly wrong, if the query spans both — then score 5.)
2. **Concept relevance / precision** (`relevance`): are the returned concepts
   actually implied by the query? Penalize tags that are off-topic or have
   nothing to do with what the query describes.
3. **Coverage / recall** (`coverage`): does the tag set capture the obvious,
   salient musical meaning of the query, or does it miss an important concept?
   (Do not demand every conceivable concept — just the clear salient ones.)
4. **Level calibration** (`levels`): are the chosen levels (high/mid/low etc.)
   reasonable given the query's intensity language ("huge", "barely", "crisp",
   "thundering")?
5. **Reasoning quality** (`reasoning`): do the `semantic_analysis` explanations
   convincingly justify each tag from the query text? 
6. **Over-tagging** (`over_tag`): did the model add tags that are *not* implied
   (invented content)? Count any such tags. 5 = none, 4 = one minor, 3 = one
   clear, 2 = several unrelated, 1 = egregious.
7. **Importance and fallback calibration** (`importance`): are the `importance` weights (1–5)
   and `fallback` directions ("nearest", "up", "down") sensible — do the most salient concepts get the highest importance, and
   peripheral/incidental ones lower? 5 =
   well-ranked, 4 = one minor mis-order, 3 = a clear mis-rank, 2 = several
   mis-ranks, 1 = inverted/arbitrary.

## Verdict

Combine the axes into one overall verdict:

- `great` — the interpretation is clearly right and musically useful (axes mostly 4–5).
- `good` - some minor issues.
- `debatable` — 1 clear issue and maybe 1 or 2 minor ones but overall correct vibe.
- `bad` - multiple clear issues
- `wrong` — the interpretation is wrong or largely off-target.

## Output format

Return a JSON object: a list of one object per query.

```json
[
  {
    "id": "mus_001",
    "family": 4, "relevance": 5, "coverage": 4, "levels": 5, "reasoning": 4, "over_tag": 5, "importance": 5,
    "verdict": "great",
    "notes": "Free-form: what worked, what was questionable, any invented tags.",
    "suggested_missing": ["optional concept_name(s) clearly implied but not tagged"]
  }
]
```

Do not invent scores. Base every score on the query text, the returned tags, and
the semantic analysis. Be strict about invented tags (over-tagging) and about
off-topic concepts (relevance).
