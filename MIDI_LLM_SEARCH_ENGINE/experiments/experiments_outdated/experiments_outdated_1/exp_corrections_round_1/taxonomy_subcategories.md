# Taxonomy Subcategory Structure

## Subcategory List

| # | Subcategory | Concepts | Category | Notes |
|---|-------------|----------|----------|-------|
| 1 | rhythmic density | 25 | rhythm | Was split into `density` + `evolution`. Merged. |
| 2 | spacing | 55 | rhythm | `max_silence` moved from its own `silence` subcategory into spacing. |
| 3 | duration | 11 | rhythm | Clean. |
| 4 | groove | 16 | rhythm | Timing feel (swing, jitter). |
| 5 | grid | 50 | rhythm | Position-specific attack/success. Separate from groove — measures *which* positions, not *how* timed. |
| 6 | texture | 11 | harmony | "How many notes at once" — chordal density, voicing spread, polyphonic rate/duration, monophonic pitch. |
| 7 | register | 5 | harmony | Pitch range (lowest, highest, median, spread, shift). |
| 8 | harmonic intervals | 28 | harmony | Harmonic interval percentages (00-24 semitones) + summary (consonance/dissonance). |
| 9 | melodic intervals | 33 | melody | All melodic concepts: direction, interval profile (asc/desc 1-12+), static, sequence repetition, vocabulary. |
| 10 | dynamics | 25 | dynamics | Velocity, accents, spread, trend, max velocity. Renamed from `[EXPRESSION]`. |
| 11 | metadata | 11 | metadata | All file-level concepts merged: instrument, program, note count, time sig, root key, scale type, tempo, measures. |
| 12 | tonality | 4 | tonality | Unique pitches, out-of-key notes, dominant pitch. |
| 13 | prevalence | 21 | drums | Which specific kit pieces exist (per-piece breakdown). |

## Rationale for Keepers

### `texture` (not renamed to "harmonic density")
- "Texture" is the standard music theory term for how many notes sound at once
- Avoids confusion with "rhythmic density"
- Naturally covers the 11 concepts: histogram (1-6+ notes), polyphonic share/rate/duration, voicing spread, monophonic pitch

### `grid` (not merged into "groove")
- Grid measures *which* beat positions are attacked (positional emphasis)
- Groove measures *how* the timing deviates (performance feel)
- Different musical dimensions even though both sit under rhythm

## Cleanup Changes Applied

| Change | File | Before | After |
|--------|------|--------|-------|
| spacing max_silence → spacing | spacing.py | `silence` | `spacing` |
| rhythmic density concepts merged | rhythmic_density.py | `density` / `evolution` | `rhythmic density` |
| melodic subcategory renamed | melodic.py | `contour` / `palette` | `melodic intervals` |
| harmonic subcategory renamed | harmonic_intervals.py | `intervals` | `harmonic intervals` |
| expression category → dynamics | dynamics.py, llm_categories.py | `[EXPRESSION]` | `[DYNAMICS]` |
| dynamics_max_velocity missing subcategory | dynamics.py | (none) | `dynamics` |
| metadata subcategories merged | metadata.py | `identity` / `tonality` / `metadata` | `metadata` |
| drums prevalence renamed | drum_router.py | `identity` | `prevalence` |
| tonality subcategories merged | tonality.py | `pitch` / `tonal center` | `tonality` |
