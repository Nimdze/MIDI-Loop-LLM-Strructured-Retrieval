import pandas as pd
import plotly.express as px
import streamlit as st


def render_histogram(df: pd.DataFrame, column: str, title: str | None = None) -> None:
    """Render a Plotly histogram for a numeric column."""
    if column not in df.columns:
        st.info("No data available for this column.")
        return
    values = df[column].dropna()
    if values.empty:
        st.info("No data available for this column.")
        return

    display_name = column.rsplit("_", 1)[0].replace("_", " ").title()
    chart_title = title or f"Distribution of {display_name}"

    is_discrete = False
    if pd.api.types.is_numeric_dtype(values) and not values.empty:
        sample = values.head(100)
        is_discrete = all(int(value) == value for value in sample)

    nbins = None if is_discrete else 50

    fig = px.histogram(
        df,
        x=column,
        nbins=nbins,
        text_auto=True,
        title=chart_title,
        color_discrete_sequence=["#00FFAA"],
        template="plotly_dark",
    )
    if is_discrete:
        fig.update_xaxes(dtick=1)

    fig.update_layout(
        xaxis_title=display_name,
        yaxis_title="Count",
        bargap=0.2 if is_discrete else 0.1,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width="stretch")
