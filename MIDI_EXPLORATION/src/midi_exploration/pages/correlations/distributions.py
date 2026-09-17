"""Correlation distribution histograms."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def _draw_histogram(temp_matrix: pd.DataFrame, title: str, is_diff: bool = False) -> None:
    vals = temp_matrix.values.flatten()
    vals = vals[~np.isnan(vals)]
    if len(vals) == 0:
        return

    fig = px.histogram(
        x=vals,
        nbins=50,
        range_x=[0, 1] if is_diff else [-1, 1],
        color_discrete_sequence=["#EF553B"] if is_diff else ["#636EFA"],
        title=title,
        template="plotly_dark",
        labels={"x": "r value"},
    )
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=30, b=10),
        bargap=0.1,
    )
    if not is_diff:
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, width="stretch")


def render(
    temp_p: pd.DataFrame,
    temp_s: pd.DataFrame,
    temp_d: pd.DataFrame,
) -> None:
    st.divider()
    st.subheader("Correlation Distributions")
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        _draw_histogram(temp_p, "Pearson Spread")
    with dc2:
        _draw_histogram(temp_s, "Spearman Spread")
    with dc3:
        _draw_histogram(temp_d, "Diff Spread", is_diff=True)
