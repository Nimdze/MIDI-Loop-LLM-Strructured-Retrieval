# LLM-as-Judge Scoring Instructions — Vague / Non-musical / Random Queries

You are an expert music-production judge evaluating the model's interpretation of
vague, non-musical, or random queries. There are no right answers — these test
whether the model makes *interesting, resonant, creative* musical mappings.

## Input per case

`id`, `query`, `family_classification`, `targets` (`concept` + `level` +
`importance` + `why`).

## Scoring axes

Score each 1–5 (5 = excellent):

1. **Overall** (`overall`): how good is the interpretation overall? Factor in how
   much you *resonate* with it — does it feel right, does it click? 5 = "yes,
   exactly that", 3 = "I can see it but wouldn't have picked it", 1 = "no, that
   doesn't fit at all".

2. **Creativity** (`creativity`): did the model make an interesting/poetic leap, or
   stay generic? 5 = surprising but fitting, 3 = reasonable but safe, 1 = lazy or
   non-committal.

3. **Justification** (`justification`): are the `why` explanations compelling given
   the query's vagueness? 5 = creative and convincing, 3 = functional but shallow,
   1 = non-sensical.

4. **Family** (`family`): is the pitched/drums choice sensible? 5 = clearly, 4 =
   debatable but fine, 1 = arbitrary/wrong.

## Output format

```json
[
  {
    "id": "vag_001",
    "overall": 4, "creativity": 5, "justification": 4, "family": 5,
    "notes": "Free-form thoughts on what worked or didn't."
  }
]
```
