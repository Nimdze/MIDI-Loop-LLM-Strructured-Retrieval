# Translator evaluation — recorded runs

These folders are the recorded runs behind the companion paper's evaluation of the semantic
translation layer. Each round was produced by the corresponding script in
`../evaluation/translator_evaluation/`, using a behavioral-testing framework of Minimum
Functionality and Invariance tests.

Each timestamped run folder contains the raw `results.json` and `summary.json`, and in most cases an
`analysis.md` write-up.

| Folder | Round | What it tests |
|---|---|---|
| `evaluation_literal_1/` | Test 1 | Literal `concept: level` reproduction at combination sizes 1–10 — pure taxonomy reproduction, no paraphrase. |
| `evaluation_examples_2/` | Test 2 | Taxonomy example validation: each concept's first `llm_example`, singles and combinations. |
| `evaluation_paraphrases_3/` | Test 3 | Semantic invariance over lexically-distanced paraphrases (concept-presence and level-direction calibration). |
| `evaluation_directives_4/` | Evaluation 4 | Whether the translator derives relative *importance* and *fallback direction* from query structure. |
| `evaluation_musical_queries_5/` | Test 5 | Natural musical queries (vibes, genre, technical phrasing) with no expected targets; scored manually and by an LLM judge. |
| `evaluation_vague_queries_6/` | Test 6 | Vague, rare, or non-musical queries — graceful degradation rather than confident over-tagging. |

The query banks and scoring rubrics live next to each script under
`../evaluation/translator_evaluation/evaluation_*`.

Earlier development rounds and planning notes were intentionally removed from this repository; they
are kept locally out of tree.
