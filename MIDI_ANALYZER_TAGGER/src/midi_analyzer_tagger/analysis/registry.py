import json
import logging
from pathlib import Path
from typing import Any

from midi_analyzer_tagger.core import FeatureExtractor
from midi_analyzer_tagger.analysis.llm_categories import (
    LLM_CATEGORY_METADATA,
    LLM_SUBCATEGORY_METADATA,
    LLM_UNKNOWN_CATEGORY_DESCRIPTION,
)

logger = logging.getLogger(__name__)


class ExtractorRegistry:
    """Collects feature extractors and compiles the taxonomy.

    Each plugin can define its own concepts. The registry validates that
    concept names are unique and assigns a stable global index to every level.
    Indices from a previous taxonomy are reused so that adding a new concept
    does not shift existing level indices.
    """

    def __init__(
        self,
        plugins: list[FeatureExtractor] = None,
        existing_taxonomy: dict[str, dict[str, Any]] | None = None,
    ):
        self.plugins: list[FeatureExtractor] = []
        self._concept_to_plugin: dict[str, str] = {}
        self._existing_level_indices: dict[tuple[str, str], int] = {}
        self._index_counter: int = 0
        self._built: bool = False

        self._seed_indices(existing_taxonomy or {})

        for plugin in list(plugins or []):
            self.register(plugin)

    def _seed_indices(self, existing_taxonomy: dict[str, dict[str, Any]]) -> None:
        """Reuse level indices from a previous taxonomy as a starting point."""
        max_index = -1
        for concept_name, data in existing_taxonomy.items():
            llm = data.get("llm") or {}
            for level_entry in llm.get("levels", []):
                level_index, level_name, *_ = level_entry
                self._existing_level_indices[(concept_name, level_name)] = level_index
                max_index = max(max_index, level_index)
        self._index_counter = max_index + 1

    def register(self, plugin: FeatureExtractor) -> None:
        for concept in plugin.concepts:
            if concept.name in self._concept_to_plugin:
                logger.warning(
                    "Duplicate concept %r in plugin %r: already defined by plugin %r",
                    concept.name,
                    plugin.name,
                    self._concept_to_plugin[concept.name],
                )
            else:
                self._concept_to_plugin[concept.name] = plugin.name

        self.plugins.append(plugin)
        self._built = False

    def _assign_indices(self) -> None:
        if self._built:
            return

        for plugin in self.plugins:
            for concept in plugin.concepts:
                if self._concept_to_plugin.get(concept.name) != plugin.name:
                    continue

                for level in concept.levels:
                    if level.index is not None:
                        continue
                    key = (concept.name, level.name)
                    if key in self._existing_level_indices:
                        level.index = self._existing_level_indices[key]
                    else:
                        level.index = self._index_counter
                        self._index_counter += 1

        self._built = True

    def get_for_family(self, family: str) -> list[FeatureExtractor]:
        return [plugin for plugin in self.plugins if any(family in concept.family for concept in plugin.concepts)]

    def owns_concept(self, plugin_name: str, concept_name: str) -> bool:
        """Return whether the given plugin owns the concept in the registry."""
        return self._concept_to_plugin.get(concept_name) == plugin_name

    def owned_concepts(self, plugin_name: str) -> set[str]:
        """Return the concept names owned by a given plugin."""
        return {concept_name for concept_name, owner in self._concept_to_plugin.items() if owner == plugin_name}

    def compile_taxonomy(self) -> dict[str, Any]:
        self._assign_indices()
        taxonomy: dict[str, Any] = {}
        llm_categories: dict[str, Any] = {}
        subcategories: dict[str, dict[str, Any]] = {}

        # First pass: build all entries
        for plugin in self.plugins:
            for concept in plugin.concepts:
                if self._concept_to_plugin.get(concept.name) != plugin.name:
                    continue

                subcategory = concept.llm_subcategory or plugin.llm_subcategory
                if subcategory and concept.default_weight:
                    if subcategory not in subcategories:
                        subcategories[subcategory] = {
                            "description": plugin.llm_description,
                            "source": plugin.name,
                        }
                    elif plugin.name != "drum_router" and subcategories[subcategory]["source"] == "drum_router":
                        # Prefer the real extractor's description over the router's generic one
                        subcategories[subcategory] = {
                            "description": plugin.llm_description,
                            "source": plugin.name,
                        }

                if concept.category not in llm_categories:
                    llm_category = None
                    if plugin.llm_category_description:
                        llm_category = {
                            "description": plugin.llm_category_description,
                            "interpretation": plugin.llm_category_interpretation or "",
                            "examples": plugin.llm_category_examples or [],
                        }
                    elif concept.category in LLM_CATEGORY_METADATA:
                        llm_category = LLM_CATEGORY_METADATA[concept.category]
                    else:
                        logger.warning("Category %r not documented for LLM; using fallback description.", concept.category)
                        llm_category = LLM_UNKNOWN_CATEGORY_DESCRIPTION
                    llm_categories[concept.category] = llm_category

                llm_block: dict[str, Any] = {
                    "category": concept.category,
                    "subcategory": subcategory or "",
                    "instrument_family": concept.family,
                    "scope": concept.scope,
                    "levels": [[level.index, level.name, level.weight] for level in concept.levels],
                }

                if plugin.name == "drum_router" and concept.family == ["drums"]:
                    # Drum concepts that are base-concept applications: emit a minimal
                    # reference to the base concept instead of duplicating its text.
                    # Include the (piece-localized) examples so the concept is usable
                    # as a test/routing probe.
                    base_name = _drum_base_concept_name(concept.name)
                    kit_piece = _drum_kit_piece(concept.name)
                    if base_name and kit_piece:
                        llm_block["examples"] = concept.llm_examples or []
                        entry: dict[str, Any] = {
                            "extractor": plugin.name,
                            "base_concept": base_name,
                            "kit_piece": kit_piece,
                            "mutually_exclusive": concept.mutually_exclusive,
                            "base_weight": concept.default_weight,
                            "llm": llm_block,
                        }
                    else:
                        entry = _full_concept_entry(plugin, concept, llm_block, subcategory)
                else:
                    entry = _full_concept_entry(plugin, concept, llm_block, subcategory)

                if concept.pair_with:
                    entry["llm"]["pair_with"] = concept.pair_with
                    entry["llm"]["pair_role"] = concept.pair_role

                # Bin concepts: mark the family + bin. For share/profile families, drop
                # the fully-shared interpretation (identical across the family, rendered
                # once at the group level). Grid families keep per-position interpretation
                # (the attempt text embeds the position description). Explicitly-declared
                # aggregation families (llm_bin_family) keep their interpretation — each
                # member carries its own "Use for" directive. Interval families keep theirs
                # so the first member's directive can serve as the group-level "How to use".
                if not entry.get("base_concept"):
                    bin_info = _bin_info(concept.name)
                    if concept.llm_bin_family:
                        entry["llm"]["bin_family"] = concept.llm_bin_family
                        entry["llm"]["bin_label"] = concept.llm_bin_label or ""
                    elif bin_info:
                        entry["llm"]["bin_family"] = bin_info[0]
                        entry["llm"]["bin_label"] = bin_info[1]
                        if (
                            not bin_info[0].endswith("_profile")
                            and not bin_info[0].startswith("grid_")
                            and bin_info[0] != "metadata_time_sig"
                            and bin_info[0] not in _KEEP_INTERPRETATION_BIN_FAMILIES
                        ):
                            entry["llm"].pop("interpretation", None)

                taxonomy[concept.name] = entry

        # Third pass: add paired_dimensions for concepts with pair_with
        for concept_name, entry in taxonomy.items():
            llm = entry.get("llm", {})
            pair_with = llm.get("pair_with")
            if pair_with and pair_with in taxonomy:
                paired = taxonomy[pair_with]
                paired_llm = paired.get("llm", {})
                role = llm.get("pair_role", "primary")
                paired_role = paired_llm.get("pair_role", "secondary")
                llm["paired_dimensions"] = {
                    role: {"levels": llm.get("levels", [])},
                    paired_role: {"levels": paired_llm.get("levels", [])},
                }

        taxonomy["llm_categories"] = llm_categories
        taxonomy["llm_subcategories"] = {}
        for name, meta in sorted(subcategories.items()):
            curated = LLM_SUBCATEGORY_METADATA.get(name, {})
            taxonomy["llm_subcategories"][name] = {
                "description": curated.get("description") or meta.get("description", ""),
                "interpretation": curated.get("interpretation", ""),
                "disambiguation": curated.get("disambiguation", ""),
                "examples": curated.get("examples", []),
                "families": curated.get("families", []),
            }
        return taxonomy


_KIT_PIECES = ("kick", "snare_clap", "hats_cymbals", "toms_others")


def _drum_kit_piece(concept_name: str) -> str | None:
    """Return the kit piece token if concept_name is a drum base application."""
    if not concept_name.startswith("drum_"):
        return None
    for piece in _KIT_PIECES:
        if concept_name.startswith(f"drum_{piece}_"):
            return piece
    return None


def _drum_base_concept_name(concept_name: str) -> str | None:
    """Return the unp-refixed base concept name, or None if not applicable."""
    piece = _drum_kit_piece(concept_name)
    if not piece:
        return None
    prefix = f"drum_{piece}_"
    if concept_name.startswith("drum_prevalence_"):
        return None
    return concept_name[len(prefix):]


def _full_concept_entry(plugin, concept, llm_block: dict[str, Any], subcategory: str | None) -> dict[str, Any]:
    """Build a full concept entry including shared text fields (non-reference concepts)."""
    llm_block["description"] = concept.llm_description or concept.description
    llm_block["interpretation"] = concept.llm_interpretation
    llm_block["level_descriptions"] = concept.llm_level_descriptions or {}
    llm_block["examples"] = concept.llm_examples or []
    return {
        "extractor": plugin.name,
        "mutually_exclusive": concept.mutually_exclusive,
        "base_weight": concept.default_weight,
        "llm": llm_block,
    }


# Bin families whose per-member interpretation is meaningful and should be kept
# (each member carries its own directive; the first member's serves as the
# group-level "How to use" in the prompt).
_KEEP_INTERPRETATION_BIN_FAMILIES = (
    "profile_harmonic_intervals_pct",
    "profile_melodic_intervals_pct_asc",
    "profile_melodic_intervals_pct_desc",
)

_BIN_FAMILIES = (
    ("spacing_", "_share"),
    ("spacing_", "_profile"),
    ("duration_", "_share"),
    ("duration_", "_profile"),
    ("texture_pct_", "_notes"),
    ("profile_harmonic_intervals_pct_", "_semitones"),    ("profile_melodic_intervals_pct_asc_", "_semitones"),
    ("profile_melodic_intervals_pct_desc_", "_semitones"),
    ("grid_attempt_pct_", ""),
    ("grid_success_pct_", ""),
    ("metadata_time_sig_", ""),
)


def _bin_info(concept_name: str) -> tuple[str, str] | None:
    """Return (bin_family, bin_label) if concept_name is a histogram bin, else None.

    A bin family is a set of concepts that share the same measurement shape
    (a percentage/share with identical levels) and differ only in which bin
    (subdivision, note count, or interval distance) they measure.
    """
    for prefix, suffix in _BIN_FAMILIES:
        if concept_name.startswith(prefix) and concept_name.endswith(suffix):
            inner = concept_name[len(prefix):-len(suffix)] if suffix else concept_name[len(prefix):]
            family = prefix.rstrip("_")
            if suffix == "_profile":
                family = f"{family}_profile"
            return family, inner
    return None


