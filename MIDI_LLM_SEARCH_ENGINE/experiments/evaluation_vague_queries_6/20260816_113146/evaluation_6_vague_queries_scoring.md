# LLM-as-Judge Scoring Instructions — Test 5: Vague / Non-musical / Random Queries

You are an expert music-production judge. For **each** query in
`to_evaluate.json`, evaluate the model's concept-tagging output. The model
received **only the query** — there are no expected targets. These queries are
vague, non-musical, or random; the test measures **graceful degradation**: the
model should NOT confidently tag a pile of specific musical concepts onto
nonsense. A correct response is often a *conservative* one.

## Input per case

`id`, `query`, `family_classification`, `targets` (`concept` + `level` +
`importance` 1–5), `semantic_analysis`.

## Scoring axes

Score each of the following 1–5 (5 = excellent):

1. **Restraint / no over-tagging** (`restraint`): did the model stay conservative
   when the query is non-musical or vague? 5 = few/no tags for nonsense, 1 = a
   confident pile of invented specific concepts for an unrelated query.
2. **Tag quality** (`quality`): *if* tags were returned, are they at least
   defensible as a loose musical reading? (Score 5 if no tags are needed, or if
   the tags given are sensible; score low if tags are forced/absurd.)
3. **Reasoning honesty** (`reasoning`): do the `semantic_analysis` explanations
   acknowledge the query is vague/interpretive, or do they over-justify with
   confident but fabricated reasoning? 5 = honest/measured, 1 = confidently
   fabricated justification for invented tags.
4. **Family classification** (`family`): if a family was picked, is it a
   reasonable interpretation (or did the model force an arbitrary family on a
   non-musical query)? 5 = sensible or appropriately cautious.
5. **Importance calibration** (`importance`): for vague/non-musical queries the
   model should NOT assign high importance/confidence to invented or forced tags.
   5 = low/uncertain importance on speculative readings (or no tags), 1 =
   confidently high importance on invented specific tags.

## Verdict

Combine into one overall verdict:

- `graceful` — handled well: conservative, no invented specifics (ideal for nonsense).
- `forced` — invented specific tags/reasoning for a query that didn't call for them.
- `miss` — clearly wrong or nonsense interpretation.
- `partial` — some sensible reading but with questionable extras.

Note: for these queries there is **no "hit"** in the sense of retrieving ground
truth; the best outcome is `graceful`.

## Output format

Return a JSON object: a list of one object per query.

```json
[
  {
    "id": "vag_001",
    "restraint": 5, "quality": 5, "reasoning": 4, "family": 5, "importance": 5,
    "verdict": "graceful",
    "notes": "Free-form: how the model handled vagueness, any forced tags."
  }
]
```

Be strict: confidently tagging specific musical concepts onto a random/non-musical
query is the key failure mode and should be scored harshly on `restraint`.
