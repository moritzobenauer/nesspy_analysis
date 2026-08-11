"""Tab 3: overlay 2+ selected datasets in one interactive four-panel figure."""

from pathlib import Path

import plotly.express as px
import streamlit as st

from webapp.analyzed_run import load_run, summarize
from webapp.pipeline_status import compute_run_status, is_analyzed
from webapp.plots_interactive import build_comparison_figure

PALETTE = px.colors.qualitative.Plotly


def render_compare_tab() -> None:
    datasets = st.session_state["datasets"]
    if not datasets:
        st.info("No datasets loaded yet -- add some in the Load data tab.")
        return

    names = [d.name for d in datasets]
    selected_names = st.multiselect(
        "Datasets to compare", names, key="compare_tab__select"
    )
    if len(selected_names) < 2:
        st.info("Select at least two datasets to compare (use the Overview tab for one).")
        return

    runs = []
    for i, name in enumerate(selected_names):
        dataset = next(d for d in datasets if d.name == name)
        run_dir = Path(dataset.path)
        status = compute_run_status(run_dir)
        if not is_analyzed(status):
            st.warning(f"{name}: not analyzed / stale, skipping.")
            continue
        color = PALETTE[i % len(PALETTE)]
        try:
            runs.append(load_run(run_dir, label=name, color=color))
        except FileNotFoundError as e:
            st.warning(str(e))

    if len(runs) < 2:
        st.warning("Fewer than two analyzed datasets remain after filtering; nothing to compare.")
        return

    fig = build_comparison_figure(runs, title="Comparison")
    st.plotly_chart(fig, width="stretch")

    st.subheader("Summary")
    st.dataframe(summarize(runs), width="stretch")
