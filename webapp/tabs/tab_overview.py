"""Tab 2: status checkboxes + the four-panel plot for one selected dataset."""

from pathlib import Path

import streamlit as st

from webapp.analyzed_run import load_run
from webapp.pipeline_status import compute_run_status, is_analyzed
from webapp.plots_interactive import build_comparison_figure

SINGLE_RUN_COLOR = "#1f77b4"


def render_overview_tab() -> None:
    datasets = st.session_state["datasets"]
    if not datasets:
        st.info("No datasets loaded yet -- add one in the Load data tab.")
        return

    names = [d.name for d in datasets]
    selected_name = st.selectbox("Dataset", names, key="overview_tab__select")
    dataset = next(d for d in datasets if d.name == selected_name)
    run_dir = Path(dataset.path)
    status = compute_run_status(run_dir)

    col1, col2 = st.columns(2)
    with col1:
        st.checkbox(
            "w(q) analysis done (order_disorder_analysis.csv up to date)",
            value=is_analyzed(status),
            disabled=True,
            key="overview_tab__wq_check",
        )
    with col2:
        st.checkbox(
            "All lattices plotted (lattice_overview.png present)",
            value=status.has_lattice_overview,
            disabled=True,
            key="overview_tab__vis_check",
        )

    if status.has_failed_marker and not status.failed_marker_stale:
        st.error(
            "This run's analysis previously failed (analysis_failed.md is "
            "present). See that file in the run directory for details."
        )

    if not is_analyzed(status):
        st.warning(
            "This dataset hasn't been analyzed yet (or has new out.csv data "
            "since it was loaded). Run `2026/analyzing_order_disorder.py` or "
            "`database/run_pipeline.sh` on it, then reload this tab."
        )
        return

    try:
        run = load_run(run_dir, label=dataset.name, color=SINGLE_RUN_COLOR)
    except FileNotFoundError as e:
        st.error(str(e))
        return

    fig = build_comparison_figure([run], title=dataset.name)
    st.plotly_chart(fig, width="stretch")
