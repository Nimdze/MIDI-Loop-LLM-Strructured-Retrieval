"""Correlation engine: filtering, matrix computation, and audit."""

from typing import Any

import numpy as np
import pandas as pd

from midi_exploration.pages.correlations.categories import get_column_category


def select_numeric_columns(
    matrix: pd.DataFrame,
    active_cols: list[str],
    taxonomy: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Return only numeric ``*_norm`` columns from ``active_cols``.

    The second list contains the names of columns that were skipped
    along with a short reason (``non-numeric`` or ``not_norm``).
    """
    skipped: list[str] = []
    selected: list[str] = []
    for col in active_cols:
        if not col.endswith("_norm"):
            skipped.append(f"{col}: not _norm")
            continue
        if not pd.api.types.is_numeric_dtype(matrix[col]):
            skipped.append(f"{col}: non-numeric")
            continue
        selected.append(col)
    return selected, skipped


def detect_constant_columns(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> list[str]:
    """Return columns that have zero variance in the selected subset."""
    constant: list[str] = []
    for col in feature_cols:
        vals = df[col].dropna()
        if vals.empty or vals.nunique() <= 1:
            constant.append(col)
    return constant


def prepare_correlation_data(
    matrix: pd.DataFrame,
    active_cols: list[str],
    taxonomy: dict[str, Any],
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    """Prepare a clean DataFrame and feature list for correlation analysis.

    Returns:
        - A DataFrame containing only the selected numeric columns.
        - The list of feature columns selected.
        - Skipped columns with reasons.
        - Constant columns among the selected features.
    """
    selected, skipped = select_numeric_columns(matrix, active_cols, taxonomy)
    constant = detect_constant_columns(matrix, selected)
    usable = [c for c in selected if c not in constant]
    return (
        matrix[usable].copy(),
        usable,
        skipped,
        constant,
    )


def compute_correlation_matrices(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute Pearson, Spearman, and absolute difference matrices."""
    pearson = df.corr(method="pearson")
    spearman = df.corr(method="spearman")
    diff = (spearman - pearson).abs()
    return pearson, spearman, diff


def mask_diagonal(matrix: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with the diagonal replaced by NaN."""
    eye = pd.DataFrame(
        np.eye(len(matrix), dtype=bool),
        index=matrix.index,
        columns=matrix.columns,
    )
    return matrix.where(~eye)


def apply_cross_category_mask(
    matrix: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> pd.DataFrame:
    """Mask cells where the two columns share the same subcategory."""
    cats = pd.Series(
        [get_column_category(c, taxonomy) for c in matrix.columns],
        index=matrix.columns,
    )
    cat_array = cats.to_numpy()
    same = cat_array[:, None] == cat_array[None, :]
    return matrix.where(~same)
