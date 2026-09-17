import pandas as pd
import streamlit as st


def maybe_show_cluster_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Apply a shared active cluster filter if one is set in session state."""
    cluster = st.session_state.get("active_cluster_filter")
    if not cluster:
        return df
    st.warning("Cluster filter active.")
    if st.button("Clear cluster filter"):
        del st.session_state["active_cluster_filter"]
        st.rerun()
    return df[df["path"].isin(cluster)]


def apply_filters(
    df: pd.DataFrame,
    family: str,
    min_stats: int,
    stat_cols: list[str],
) -> pd.DataFrame:
    """Apply the basic discovery filters to the feature matrix."""
    result = df.copy()
    if family != "All":
        result = result[result["family"] == family]
    if min_stats:
        counts = result[stat_cols].notna().sum(axis=1)
        result = result[counts >= min_stats]
    return result
