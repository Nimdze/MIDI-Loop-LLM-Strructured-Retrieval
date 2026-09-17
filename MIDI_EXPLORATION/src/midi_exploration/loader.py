"""Data loading utilities for MIDI exploration."""

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


def _connect(file_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(file_path)
    conn.row_factory = sqlite3.Row
    return conn


def _read_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {table}", conn)


def _decode_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _build_level_index_by_concept(
    taxonomy: dict[str, Any],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for concept_name, data in taxonomy.items():
        if not isinstance(data, dict):
            continue
        levels = data.get("llm", {}).get("levels", [])
        mapping: dict[str, int] = {}
        if isinstance(levels, list):
            for idx, entry in enumerate(levels):
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    mapping[entry[1]] = idx
        result[concept_name] = mapping
    return result


def _pivot_tags(tags_df: pd.DataFrame, level_index_by_concept: dict[str, dict[str, int]]) -> pd.DataFrame:
    if tags_df.empty:
        return pd.DataFrame()

    pivot = tags_df.pivot(index="file_id", columns="concept_name", values="level_name")
    ordinal = pivot.copy()
    for concept, mapping in level_index_by_concept.items():
        if concept in ordinal.columns:
            ordinal[concept] = ordinal[concept].map(mapping)
    return ordinal.add_suffix("_tag")


@st.cache_data(ttl=300, show_spinner=False)
def load_tags_cached(db_path: str) -> pd.DataFrame:
    conn = _connect(db_path)
    try:
        return _read_table(conn, "tags")
    finally:
        conn.close()


@st.cache_data(ttl=300, show_spinner=False)
def load_feature_matrix_cached(
    db_path: str,
    taxonomy_json: str,
) -> pd.DataFrame:
    taxonomy = json.loads(taxonomy_json) if taxonomy_json else {}
    conn = _connect(db_path)
    try:
        files_df = _read_table(conn, "files").set_index("id")
        tags_df = _read_table(conn, "tags")
        raw_df = _read_table(conn, "raw_features")
        norm_df = _read_table(conn, "normalized_features")
    finally:
        conn.close()

    level_index_by_concept = _build_level_index_by_concept(taxonomy)

    def _pivot_and_decode(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(index=files_df.index)
        pivot = df.pivot(index="file_id", columns="concept_name", values="value")
        for col in pivot.columns:
            pivot[col] = pivot[col].apply(_decode_json_value)
        return pivot.add_suffix(suffix)

    tag_pivot = _pivot_tags(tags_df, level_index_by_concept)
    raw_pivot = _pivot_and_decode(raw_df, "_raw")
    norm_pivot = _pivot_and_decode(norm_df, "_norm")

    matrix = files_df.join(tag_pivot).join(raw_pivot).join(norm_pivot)
    matrix = matrix.reset_index().rename(columns={"id": "file_id"})
    return matrix


class AnalysisLoader:
    """Load analysis.db into pandas DataFrames for exploration."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def _load_table(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Run a query and return a DataFrame, keeping schema even when empty."""
        if not self.connection:
            self.connect()
        cursor = self.connection.execute(query, params)
        rows = cursor.fetchall()
        if not rows:
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(columns=columns)
        return pd.DataFrame([dict(row) for row in rows])

    def load_files(self) -> pd.DataFrame:
        return self._load_table("SELECT * FROM files")

    def load_tags(self) -> pd.DataFrame:
        return self._load_table("SELECT * FROM tags")

    def load_raw_features(self, concept_names: list[str] | None = None) -> pd.DataFrame:
        if concept_names:
            placeholders = ",".join("?" * len(concept_names))
            query = f"SELECT * FROM raw_features WHERE concept_name IN ({placeholders})"
            return self._load_table(query, tuple(concept_names))
        return self._load_table("SELECT * FROM raw_features")

    def load_normalized_features(self) -> pd.DataFrame:
        return self._load_table("SELECT * FROM normalized_features")

    def load_feature_matrix(self, taxonomy: dict[str, Any] | None = None) -> pd.DataFrame:
        """Build a wide feature matrix with one row per file.

        Output columns:
            - file metadata (path, family, duration, note_count, ...)
            - <concept>_tag : ordinal level index within the concept
            - <concept>_raw : raw feature value
            - <concept>_norm: normalized feature value
        """
        taxonomy = taxonomy or {}

        files_df = self.load_files().set_index("id")
        tags_df = self.load_tags()
        raw_df = self.load_raw_features()
        norm_df = self.load_normalized_features()

        level_index_by_concept = self._build_level_index_by_concept(taxonomy)

        def _pivot_and_decode(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
            if df.empty:
                return pd.DataFrame(index=files_df.index)
            pivot = df.pivot(index="file_id", columns="concept_name", values="value")
            for col in pivot.columns:
                pivot[col] = pivot[col].apply(self._decode_json_value)
            return pivot.add_suffix(suffix)

        tag_pivot = self._pivot_tags(tags_df, level_index_by_concept)
        raw_pivot = _pivot_and_decode(raw_df, "_raw")
        norm_pivot = _pivot_and_decode(norm_df, "_norm")

        matrix = files_df.join(tag_pivot).join(raw_pivot).join(norm_pivot)
        matrix = matrix.reset_index().rename(columns={"id": "file_id"})
        return matrix

    @staticmethod
    def _build_level_index_by_concept(
        taxonomy: dict[str, Any],
    ) -> dict[str, dict[str, int]]:
        """Build a level-name -> index mapping for each concept, skipping malformed entries."""
        result: dict[str, dict[str, int]] = {}
        for concept_name, data in taxonomy.items():
            if not isinstance(data, dict):
                continue
            levels = data.get("llm", {}).get("levels", [])
            mapping: dict[str, int] = {}
            if isinstance(levels, list):
                for idx, entry in enumerate(levels):
                    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                        mapping[entry[1]] = idx
            result[concept_name] = mapping
        return result

    @staticmethod
    def _decode_json_value(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    @staticmethod
    def _pivot_tags(tags_df: pd.DataFrame, level_index_by_concept: dict[str, dict[str, int]]) -> pd.DataFrame:
        if tags_df.empty:
            return pd.DataFrame()

        pivot = tags_df.pivot(index="file_id", columns="concept_name", values="level_name")
        ordinal = pivot.copy()
        for concept, mapping in level_index_by_concept.items():
            if concept in ordinal.columns:
                ordinal[concept] = ordinal[concept].map(mapping)
        return ordinal.add_suffix("_tag")

    def load_tag_categories(self, taxonomy: dict[str, Any] | None = None) -> dict[str, list[str]]:
        """Map taxonomy category to concept names."""
        taxonomy = taxonomy or {}
        categories: dict[str, list[str]] = {}
        for concept_name, data in taxonomy.items():
            category = data.get("llm", {}).get("category", "unknown")
            categories.setdefault(category, []).append(concept_name)
        return categories

    def load_audit_stats(
        self, taxonomy: dict[str, Any] | None = None, matrix: pd.DataFrame | None = None
    ) -> dict[str, Any]:
        """Compute per-file total and per-category concept counts."""
        if matrix is None:
            matrix = self.load_feature_matrix(taxonomy)

        concept_cols = [c for c in matrix.columns if c.endswith("_raw") or c.endswith("_tag") or c.endswith("_norm")]
        global_counts = matrix[concept_cols].notna().sum(axis=1).astype(int)

        categories = self.load_tag_categories(taxonomy)
        distributions: dict[str, list[int]] = {"global": global_counts.tolist()}
        for category, concept_names in categories.items():
            suffix_cols = [f"{name}_{suffix}" for name in concept_names for suffix in ("raw", "tag", "norm")]
            available = [c for c in suffix_cols if c in matrix.columns]
            if available:
                distributions[category] = matrix[available].notna().sum(axis=1).astype(int).tolist()

        total = len(global_counts)
        return {
            "distributions": distributions,
            "max_stats": int(global_counts.max()) if total else 0,
            "avg_stats": float(global_counts.mean()) if total else 0.0,
            "total": total,
        }

    def load_file_payload(self, file_id: int, taxonomy: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build a per-file summary grouped by taxonomy category."""
        taxonomy = taxonomy or {}
        category_map = {concept_name: data.get("llm", {}).get("category", "unknown") for concept_name, data in taxonomy.items()}

        tags_df = self._load_table("SELECT * FROM tags WHERE file_id = ?", (file_id,))
        raw_df = self._load_table("SELECT * FROM raw_features WHERE file_id = ?", (file_id,))
        norm_df = self._load_table("SELECT * FROM normalized_features WHERE file_id = ?", (file_id,))

        concepts: dict[str, dict[str, dict[str, Any]]] = {}

        def _concept_entry(concept_name: str) -> dict[str, Any]:
            category = category_map.get(concept_name, "unknown")
            return concepts.setdefault(category, {}).setdefault(concept_name, {"tag": None, "raw": None, "norm": None})

        for _, row in tags_df.iterrows():
            entry = _concept_entry(row["concept_name"])
            entry["tag"] = row["level_name"]

        for _, row in raw_df.iterrows():
            entry = _concept_entry(row["concept_name"])
            entry["raw"] = self._decode_json_value(row["value"])

        for _, row in norm_df.iterrows():
            entry = _concept_entry(row["concept_name"])
            entry["norm"] = self._decode_json_value(row["value"])

        return {"file_id": file_id, "concepts": concepts}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
