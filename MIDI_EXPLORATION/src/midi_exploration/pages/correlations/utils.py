"""Utility helpers shared across the correlation page."""


def clamp(n: float, minn: float, maxn: float) -> float:
    """Clamp ``n`` between ``minn`` and ``maxn``."""
    return max(min(n, maxn), minn)


def format_column_name(col: str) -> str:
    """Convert a feature column into a readable label."""
    return col.rsplit("_", 1)[0].replace("_", " ").title()
