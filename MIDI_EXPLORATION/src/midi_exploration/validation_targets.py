"""Feature-validation target resolver.

For a chosen set of concepts, produce the tags a human validator should check:
the two intensity extremes per concept (lowest + highest) for maximum contrast.
If an extreme tag has too few files, step one level toward the middle until it
has enough. Single-level concepts produce one tag.

Dataset-aware: file counts come from a provided matrix (rows = files). The
matrix's ``{concept}_tag`` columns hold the level **index** (ordinal position),
so all counting/filtering here maps level names to indices via the taxonomy.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# An extreme tag with fewer than this many files is stepped inward.
MIN_FILES = 3
# Cap how many steps inward we take before giving up on a tag.
MAX_INWARD_STEPS = 4

# Extra "mid" level tags (besides the two extremes) so a validator can inspect
# intermediate cases — e.g. a moderate texture level for two-hand (melody +
# accompaniment) playing. Value = the level index to start from.
MID_LEVELS: dict[str, int] = {
    "texture_polyphonic_pct": 3,  # Present Chordal (3+ Notes) — partial polyphony
    "texture_pct_1_notes": 3,     # Present 1 Notes — partial monophony
}

# Explicit validation extremes for concepts where the default position-based
# extremes don't make sense. (The old absolute mono-register override was removed
# when it was replaced by the relative mono-vs-chords feature, whose extremes are
# inherently sensible.)
EXTREME_OVERRIDES: dict[str, dict[str, str]] = {}


def concept_levels(taxonomy: dict[str, Any], concept: str) -> list[str]:
    """Ordered level names (index 0 = most intense/highest)."""
    levels = (taxonomy.get(concept, {}).get("llm", {}) or {}).get("levels") or []
    return [lv[1] for lv in levels if isinstance(lv, (list, tuple)) and len(lv) >= 2]


def _index_map(taxonomy: dict[str, Any]) -> dict[str, dict[str, int]]:
    """concept -> {level_name: ordinal index} matching the matrix's _tag columns."""
    imap: dict[str, dict[str, int]] = {}
    for concept, data in taxonomy.items():
        if not isinstance(data, dict):
            continue
        levels = (data.get("llm", {}) or {}).get("levels") or []
        imap[concept] = {
            lv[1]: i for i, lv in enumerate(levels)
            if isinstance(lv, (list, tuple)) and len(lv) >= 2
        }
    return imap


def _file_count(matrix: pd.DataFrame, concept: str, level: str, imap: dict) -> int:
    col = f"{concept}_tag"
    if col not in matrix.columns:
        return 0
    idx = imap.get(concept, {}).get(level)
    if idx is None:
        return 0
    return int((matrix[col] == idx).sum())


def _step_until_enough(
    matrix: pd.DataFrame, concept: str, start_idx: int, levels: list[str], step_dir: int, imap: dict
) -> tuple[str, int] | None:
    """Walk from ``start_idx`` in ``step_dir`` until a level has >= MIN_FILES.

    Returns ``(level, file_count)`` or ``None`` if we walk off the end or exceed
    ``MAX_INWARD_STEPS`` without finding enough files.
    """
    idx = start_idx
    for _ in range(MAX_INWARD_STEPS + 1):
        if idx < 0 or idx >= len(levels):
            break
        level = levels[idx]
        count = _file_count(matrix, concept, level, imap)
        if count >= MIN_FILES:
            return level, count
        idx += step_dir  # move one degree toward the middle
    return None


def _is_harmonic(concept: str) -> bool:
    """Harmonic interval concepts (bins + consonance/dissonance aggregates).

    Mono is not relevant to harmonic intervals: their "Defining" level is
    polluted by mono-line stepwise overlap (a monophonic line's stepwise motion
    registers as dissonant vertical intervals). So validation must not use it.
    """
    return concept.startswith("profile_harmonic_intervals_pct_") or concept.startswith("harmonic_")


def _high_start_idx(concept: str) -> int:
    """Start index for the high extreme. Harmonic concepts skip 'Defining' and
    'Primary' and use 'Significant' (index 2) so they can be combined with high
    polyphony and still have enough samples.
    """
    return 2 if _is_harmonic(concept) else 0


def resolve_extreme_tags(matrix: pd.DataFrame, taxonomy: dict[str, Any], concepts: list[str]) -> list[dict]:
    """Resolve the validation tags for each concept.

    Returns a list of ``{"concept", "level", "file_count"}`` where ``file_count``
    is the actual count of files carrying that tag in the matrix.
    """
    imap = _index_map(taxonomy)
    tags: list[dict] = []
    for concept in concepts:
        levels = concept_levels(taxonomy, concept)
        if not levels:
            continue
        n = len(levels)
        seen: set[str] = set()
        candidates = []
        override = EXTREME_OVERRIDES.get(concept)
        if override:
            extremes = [(levels.index(override["high"]), 1), (levels.index(override["low"]), 1)]
        else:
            high_start = _high_start_idx(concept)
            extremes = [(high_start, 1), (n - 1, -1)]
        for start, step in extremes:
            resolved = _step_until_enough(matrix, concept, start, levels, step, imap)
            if resolved:
                level, count = resolved
                if level not in seen:
                    seen.add(level)
                    candidates.append({"concept": concept, "level": level, "file_count": count})
        # optional mid-level tag (e.g. moderate texture to inspect 2-hand cases)
        mid_start = MID_LEVELS.get(concept)
        if mid_start is not None:
            resolved = _step_until_enough(matrix, concept, mid_start, levels, 1, imap)
            if resolved:
                level, count = resolved
                if level not in seen:
                    seen.add(level)
                    candidates.append({"concept": concept, "level": level, "file_count": count})
        if not candidates:
            # no extreme tag had enough files; fall back to the most populated level
            best, best_n = None, -1
            for lv in levels:
                c = _file_count(matrix, concept, lv, imap)
                if c > best_n:
                    best, best_n = lv, c
            if best is not None:
                candidates.append({"concept": concept, "level": best, "file_count": best_n})
        tags.extend(candidates)
    return tags


def files_for_tag(matrix: pd.DataFrame, taxonomy: dict[str, Any], concept: str, level: str) -> list[str]:
    col = f"{concept}_tag"
    if col not in matrix.columns:
        return []
    idx = _index_map(taxonomy).get(concept, {}).get(level)
    if idx is None:
        return []
    mask = matrix[col] == idx
    return list(matrix.loc[mask, "path"])
