"""Category and subcategory mapping for correlation analysis."""

from typing import Any

# Taxonomy category order from the sidebar.
CATEGORY_ORDER = [
    "metadata",
    "rhythm",
    "harmony",
    "melody",
    "tonality",
    "expression",
    "drums",
    "placeholder",
]

# Drum stem identifiers that should be surfaced as subcategories.
DRUM_STEMS = [
    "drum_kick",
    "drum_snare_clap",
    "drum_snare",
    "drum_hats_cymbals",
    "drum_hats",
    "drum_cymbals",
    "drum_toms_others",
    "drum_toms",
    "drum_perc",
    "drum_others",
    "drum",
]

# Statistical "family" keywords used inside concept names.
# These are inferred from concept names rather than from a dedicated
# taxonomy field. When the analyzer taxonomy gains a ``subcategory``
# export, this heuristic should be replaced by a direct lookup.
SUBCATEGORIES = [
    "rhythmic_density",
    "duration",
    "spacing",
    "dynamics",
    "groove",
    "prevalence",
    "harmonic_intervals",
    "melodic_intervals",
    "register",
    "tonality_profile",
    "texture",
    "grid",
    "profile",
    "density",
    "intensity",
]


def _strip_suffix(col: str) -> str:
    """Return the concept name without the feature suffix."""
    for suffix in ("_norm", "_raw", "_tag"):
        if col.endswith(suffix):
            return col[: -len(suffix)]
    return col


def _extract_drum_stem(concept_name: str) -> str | None:
    """Pick the longest matching drum stem for ordering and grouping."""
    matches = [stem for stem in DRUM_STEMS if stem in concept_name]
    if not matches:
        return None
    return max(matches, key=len)


def _extract_subcategory(concept_name: str, taxonomy: dict[str, Any]) -> str | None:
    """Return the subcategory from the taxonomy, falling back to name-based heuristic."""
    data = taxonomy.get(concept_name, {})
    sub = data.get("llm", {}).get("subcategory")
    if sub:
        return sub
    matches = [s for s in SUBCATEGORIES if s in concept_name]
    if not matches:
        return None
    return max(matches, key=len)


def get_category(concept_name: str, taxonomy: dict[str, Any]) -> str:
    """Return a grouping key for a concept.

    The key starts with the taxonomy category, then optionally adds a
    subcategory. For drums, the stem is also included so the old
    "drum_kick_rhythmic_density" style grouping remains possible.
    """
    data = taxonomy.get(concept_name, {})
    category = data.get("llm", {}).get("category", "unknown")

    if category == "drums":
        stem = _extract_drum_stem(concept_name)
        sub = _extract_subcategory(concept_name, taxonomy)
        if stem and sub:
            return f"drums/{stem}/{sub}"
        if stem:
            return f"drums/{stem}"
        if sub:
            return f"drums/{sub}"
        return "drums"

    sub = _extract_subcategory(concept_name, taxonomy)
    if sub:
        return f"{category}/{sub}"
    return category


def get_column_category(column: str, taxonomy: dict[str, Any]) -> str:
    """Convenience wrapper for a feature column."""
    return get_category(_strip_suffix(column), taxonomy)


def get_top_category(concept_name: str, taxonomy: dict[str, Any]) -> str:
    """Return the top-level taxonomy category for a concept."""
    data = taxonomy.get(concept_name, {})
    return data.get("llm", {}).get("category", "unknown")


def get_column_top_category(column: str, taxonomy: dict[str, Any]) -> str:
    """Return the top-level taxonomy category for a feature column."""
    return get_top_category(_strip_suffix(column), taxonomy)
