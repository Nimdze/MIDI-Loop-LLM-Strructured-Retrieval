# Test 9 — Logical Operators (AND, OR, NOT)

**Result:** 1.68/2.0 avg, **24/25 (96%) acceptable**
**Archive:** `test_logic_9/20260729_110117/`

## Summary

| Grade | Count | % |
|-------|-------|---|
| Perfect (2) | 18 | 72% |
| Partial (1) | 6 | 24% |
| Fail (0) | 1 | 4% |

| Operator | Trials | Performance |
|----------|--------|-------------|
| AND | 5 | Perfect — all constraints combined correctly |
| OR | 5 | Perfect — alternatives handled, both often present |
| AND + NOT | 10 | 8 perfect, 2 partial, 1 fail |
| Combo (AND+OR+NOT) | 5 | Good — some missed dimensions |

## Patterns

**AND works perfectly.** When the prompt says "X and Y", both concepts are returned
at the correct levels.

**OR works perfectly.** The LLM returns concepts for both alternatives, not just one.

**NOT is mostly correct but occasionally weak.** "No swing" → swing_low (correct).
"No crash" → simply didn't return crash prevalence (debatable).
"No punch" → still returned accents_present at moderate level (incorrect).

## Only Fail (1)

- **#16 "heavy with no punch"** — returned accents_present for snare+kick despite
  "no punch" explicitly requesting no accents. The LLM kept accents at moderate
  levels rather than suppressing them.

## Conclusion

The LLM correctly interprets logical operators in natural language queries.
AND, OR, and simple NOT ("no X") work reliably. The only weakness is negation
of concepts that are semantically close to the positive statement (e.g.,
"no punch" near "heavy"). For production search, this is acceptable — a
search for "heavy with no punch" would still return relevant results even
if accents are slightly higher than ideal.
