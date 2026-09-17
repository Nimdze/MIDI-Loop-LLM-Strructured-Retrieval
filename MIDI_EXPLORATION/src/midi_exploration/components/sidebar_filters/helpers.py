"""Pure helper functions for the sidebar filter/focus component."""

from typing import Any

import pandas as pd

SECTION_ORDER = [
    "metadata",
    "rhythmic density",
    "spacing",
    "duration",
    "groove",
    "grid",
    "dynamics",
    "tonality",
    "melodic intervals",
    "register",
    "texture",
    "harmonic intervals",
    "prevalence",
]

DRUM_PIECE_PREFIXES = {
    "drum_kick_": "🥁 Kick",
    "drum_prevalence_kick": "🥁 Kick",
    "drum_snare_clap_": "🥁 Snare / Clap",
    "drum_prevalence_snare_clap": "🥁 Snare / Clap",
    "drum_hats_cymbals_": "🥁 Hats & Cymbals",
    "drum_prevalence_hats_cymbals": "🥁 Hats & Cymbals",
    "drum_toms_others_": "🥁 Toms & Others",
    "drum_prevalence_toms_others": "🥁 Toms & Others",
}

DRUM_PIECE_ORDER = [
    "🥁 Kick",
    "🥁 Snare / Clap",
    "🥁 Hats & Cymbals",
    "🥁 Toms & Others",
]

_DRUM_NAME_SECTION = {
    "velocity": "dynamics",
    "dynamic": "dynamics",
    "groove": "groove",
    "grid": "grid",
    "spacing": "spacing",
    "silence": "spacing",
    "duration": "duration",
    "density": "rhythmic density",
    "evolution": "rhythmic density",
    "prevalence": "prevalence",
    "identity": "metadata",
}


def _drum_piece_name(concept_name: str) -> str | None:
    for prefix, name in DRUM_PIECE_PREFIXES.items():
        if concept_name.startswith(prefix):
            return name
    return None


def _build_drum_categories(taxonomy: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Build drum categories: kit piece → subcategory → concepts."""
    raw: dict[str, dict[str, list[str]]] = {piece: {} for piece in DRUM_PIECE_ORDER}

    for concept_name, data in taxonomy.items():
        piece = _drum_piece_name(concept_name)
        if piece is None:
            continue
        sub = data.get("llm", {}).get("subcategory", "")
        section = sub if sub else None
        if not section:
            for kw, sec in _DRUM_NAME_SECTION.items():
                if kw in concept_name:
                    section = sec
                    break
        if not section:
            section = "other"
        raw[piece].setdefault(section, []).append(concept_name)

    return {k: v for k, v in raw.items() if v}


def _build_feature_descriptions(taxonomy: dict[str, Any]) -> dict[str, str]:
    """Build subcategory_name → subcategory_description mapping."""
    result: dict[str, str] = {}
    for sub_name, meta in taxonomy.get("llm_subcategories", {}).items():
        desc = meta.get("description", "") if isinstance(meta, dict) else ""
        if desc:
            result[sub_name] = desc
    return result


def _build_concept_categories(taxonomy: dict[str, Any]) -> dict[str, list[str]]:
    categories = {section: [] for section in SECTION_ORDER}
    categories["other"] = []
    for concept_name, data in taxonomy.items():
        if concept_name in ("llm_categories", "llm_subcategories"):
            continue
        llm = data.get("llm", {})
        fam = llm.get("instrument_family", [])
        if isinstance(fam, list) and len(fam) == 1 and fam[0] == "drums":
            continue
        sub = llm.get("subcategory", "unsorted")
        categories.setdefault(sub, []).append(concept_name)
    return categories


def _all_concepts(categories: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for section in categories.values():
        if isinstance(section, dict):
            for concepts in section.values():
                result.extend(concepts)
        else:
            result.extend(section)
    return result


def _stat_cols(matrix: pd.DataFrame) -> list[str]:
    return [c for c in matrix.columns if c.endswith(("_raw", "_tag", "_norm"))]


def _level_names_present(concept: str, matrix: pd.DataFrame, taxonomy: dict[str, Any]) -> list[str]:
    tag_col = f"{concept}_tag"
    if tag_col not in matrix.columns:
        return []
    present_indices = set(matrix[tag_col].dropna().unique())
    levels = taxonomy.get(concept, {}).get("llm", {}).get("levels", [])
    idx_to_name = {idx: name for idx, name, _ in levels}
    return [idx_to_name[idx] for idx in sorted(present_indices) if idx in idx_to_name]


def _names_to_indices(names: list[str], concept: str, taxonomy: dict[str, Any]) -> list[int]:
    levels = taxonomy.get(concept, {}).get("llm", {}).get("levels", [])
    name_to_idx = {name: idx for idx, name, _ in levels}
    return [name_to_idx[name] for name in names if name in name_to_idx]


def _range_is_active(range_values: tuple[float, float] | None, matrix: pd.DataFrame, col: str) -> bool:
    if range_values is None:
        return False
    if col not in matrix.columns:
        return False
    vals = matrix[col].dropna()
    if vals.empty:
        return False
    lo, hi = range_values
    return bool(lo > float(vals.min()) or hi < float(vals.max()))


def _apply_numeric_filter(df: pd.DataFrame, col: str, range_values: tuple[float, float] | None) -> pd.DataFrame:
    if range_values is None or col not in df.columns:
        return df
    lo, hi = range_values
    return df[df[col].between(lo, hi)]


def _apply_tag_filter(
    df: pd.DataFrame,
    concept: str,
    include: list[str],
    exclude: list[str],
    taxonomy: dict[str, Any],
) -> pd.DataFrame:
    tag_col = f"{concept}_tag"
    if tag_col not in df.columns:
        return df
    if include:
        indices = _names_to_indices(include, concept, taxonomy)
        df = df[df[tag_col].isin(indices)]
    if exclude:
        indices = _names_to_indices(exclude, concept, taxonomy)
        df = df[~df[tag_col].isin(indices)]
    return df
