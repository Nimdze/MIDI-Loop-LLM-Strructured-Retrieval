"""Combine all workspace libraries into a single pooled view (All-datasets mode).

The three wide tabled apps (main inspection app, eval app, comparison app) each
need to operate on every dataset at once. This module centralises the pooling
so the behaviour is identical everywhere: feature matrices are concatenated,
per-library ``file_id`` values are made globally unique (``<library>_<id>``), a
``library`` column tags each row, taxonomies are merged, and a combined MIDI
root is built via symlinks so ``resolve_midi_path`` can find any file from any
library under one root.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from midi_exploration.loader import load_feature_matrix_cached, load_tags_cached
from midi_exploration.orchestrator import library_paths, list_libraries
from midi_llm_search_engine import FileScorer, SearchIndex
from midi_llm_search_engine.llm_client import LLMTranslator
from midi_llm_search_engine.models import SearchResponse
from midi_llm_search_engine.prompt_builder import SystemPromptBuilder

ALL_DATASETS_LABEL = "All datasets"
"""Label of the special selector entry that enables pooled (all) mode."""

_PREFIX_SEP = "_"


def all_dataset_labels() -> list[str]:
    """Return the workspace library labels usable in pooled mode."""
    return list_libraries()


def _prefix(fid: Any, label: str) -> str:
    return f"{label}{_PREFIX_SEP}{fid}"


def _prefix_path(p: Any, label: str) -> str:
    return f"{label}/{p}"


def load_library_matrix(label: str) -> tuple[pd.DataFrame, dict[str, Any], Path | None]:
    """Load a single library's feature matrix, taxonomy, and midi root."""
    lp = library_paths(label)
    if lp is None:
        return pd.DataFrame(), {}, None
    tax = json.loads(lp["taxonomy_path"].read_text()) if lp["taxonomy_path"].exists() else {}
    matrix = load_feature_matrix_cached(str(lp["db_path"]), json.dumps(tax))
    return matrix, tax, lp["midi_root"]


def load_library_tags(label: str) -> pd.DataFrame:
    """Load a single library's tag rows."""
    lp = library_paths(label)
    if lp is None:
        return pd.DataFrame()
    return load_tags_cached(str(lp["db_path"]))


def build_combined_root(midi_roots: dict[str, Path], root: Path | None = None) -> Path:
    """Create a temp dir with symlinks so DB paths from any library resolve.

    Matrix ``path`` values are prefixed as ``<library>/<subdir>/<file>``, and
    each library's ``midi_root`` is ``<workspace>/<library>/clean``. We symlink
    ``<root>/<library>`` -> ``<midi_root>`` so ``resolve_midi_path`` resolves
    ``<root>/<library>/<subdir>/<file>`` for every library.
    """
    root = root or Path(tempfile.mkdtemp(prefix="midi_combined_"))
    for label, src in midi_roots.items():
        if src is None or not src.exists():
            continue
        dst = root / label
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink():
                dst.unlink()
            else:
                shutil.rmtree(dst, ignore_errors=True)
        try:
            dst.symlink_to(src, target_is_directory=True)
        except (OSError, NotImplementedError):
            # Fallback when symlinks are unsupported: bind the root directly.
            dst.symlink_to(src, target_is_directory=True)
    return root


def cleanup_combined_root(root: Path | None) -> None:
    if root and Path(root).exists():
        shutil.rmtree(root, ignore_errors=True)


def build_combined() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], Path]:
    """Concatenate all workspace libraries into one pooled view.

    Returns ``(matrix, tags_df, merged_taxonomy, combined_root)``. ``file_id``
    is made globally unique (``<library>_<id>``) in BOTH the matrix and the tag
    rows so the pages' ``file_id`` joins keep working. Adds a ``library`` column
    tagging each matrix row's source dataset.
    """
    labels = all_dataset_labels()
    matrices: list[pd.DataFrame] = []
    tag_frames: list[pd.DataFrame] = []
    merged_tax: dict[str, Any] = {}
    midi_roots: dict[str, Path] = {}

    for label in labels:
        matrix, tax, midi_root = load_library_matrix(label)
        if matrix is None or matrix.empty:
            continue
        matrix = matrix.copy()
        matrix.insert(0, "library", label)
        matrix["file_id"] = matrix["file_id"].map(lambda fid, lb=label: _prefix(fid, lb))
        matrix["path"] = matrix["path"].map(lambda p, lb=label: _prefix_path(p, lb))

        tags = load_library_tags(label)
        if not tags.empty:
            tags = tags.copy()
            tags["file_id"] = tags["file_id"].map(lambda fid, lb=label: _prefix(fid, lb))
            tag_frames.append(tags)

        matrices.append(matrix)
        merged_tax.update(tax)
        if midi_root is not None:
            midi_roots[label] = midi_root

    if not matrices:
        return pd.DataFrame(), pd.DataFrame(), {}, Path(".")

    combined = pd.concat(matrices, ignore_index=True)
    tags = pd.concat(tag_frames, ignore_index=True) if tag_frames else pd.DataFrame()
    root = build_combined_root(midi_roots)
    return combined, tags, merged_tax, root


# ── Full-corpus structured search (all files, NOT the 1000-file pool) ──────


@st.cache_resource(show_spinner=False)
def _corpus_indexes() -> dict[str, tuple[SearchIndex, Any]]:
    """Build per-dataset indexes (unrestricted = ALL files)."""
    scorers: dict[str, tuple[SearchIndex, Any]] = {}
    for label in all_dataset_labels():
        lp = library_paths(label)
        if lp is None:
            continue
        db = lp["db_path"]
        tax = db.parent / "taxonomy.json"
        if not db.exists() or not tax.exists():
            continue
        index = SearchIndex(db, tax)  # restrict_to=None -> all files
        scorers[label] = (index, FileScorer(index))
    return scorers


def _corpus_components() -> tuple[dict[str, tuple[SearchIndex, Any]], str | None]:
    """Build per-dataset indexes (unrestricted = ALL files) and one merged prompt."""
    scorers = _corpus_indexes()
    prompt: str | None = None
    for label, (index, _) in scorers.items():
        prompt = SystemPromptBuilder(index).build(include_semantic_analysis=False)
        break
    return scorers, prompt


def _corpus_prompt(include_semantic_analysis: bool) -> str | None:
    """Build a merged corpus prompt with the given semantic-analysis flag."""
    scorers = _corpus_indexes()
    for label, (index, _) in scorers.items():
        return SystemPromptBuilder(index).build(
            include_semantic_analysis=include_semantic_analysis
        )
    return None


def corpus_search(
    query: str,
    api_key: str = "",
    base_url: str | None = None,
    model: str | None = None,
    limit: int = 20,
    include_semantic_analysis: bool = False,
) -> SearchResponse:
    """Translate once with the corpus translator, then score across ALL files.

    Unlike the fair-comparison pool, this covers every file in every workspace
    library. Raises an informative error if translation fails.
    """
    from midi_llm_search_engine.llm_client import LLMTranslator as _T

    scorers = _corpus_indexes()
    if not scorers:
        raise RuntimeError("No libraries available for search. Import a dataset via the main app first.")

    first_index = next(iter(scorers.values()))[0]
    prompt = _corpus_prompt(include_semantic_analysis)
    translator = _T(
        first_index,
        api_key=api_key or None,
        base_url=base_url or None,
        model=model or None,
        include_semantic_analysis=include_semantic_analysis,
        system_prompt=prompt,
    )
    translation, record = translator.translate(query)

    combined = []
    for _, scorer in scorers.values():
        try:
            combined.extend(scorer.score(translation.targets, limit=limit))
        except Exception:
            continue
    combined.sort(key=lambda it: it.raw_score, reverse=True)
    return SearchResponse(
        query=query,
        instrument_family=translation.family_classification or "",
        targets=translation.targets,
        results=combined[:limit],
        duration_ms=0.0,
        llm_call_record=record,
    )
