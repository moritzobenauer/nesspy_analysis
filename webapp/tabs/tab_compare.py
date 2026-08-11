"""Tab 3: overlay 2+ selected datasets in one interactive four-panel figure."""

from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st

from webapp.analyzed_run import load_run, summarize
from webapp.pipeline_status import compute_run_status, is_analyzed
from webapp.plots_interactive import build_comparison_figure, minimum_growth_speed

PALETTE = px.colors.qualitative.Plotly


def _style_with_colors(table):
    """Paint the `color` column with the colour it names, as a swatch.

    The text is set to the same colour as the cell background so the hex code
    itself disappears -- the column is there to tie a table row to a curve in
    the figure, not to be read.
    """
    return table.style.map(
        lambda hex_color: f"background-color: {hex_color}; color: {hex_color}",
        subset=["color"],
    )


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

    # Checkbox for panel (c): unchecked shows absolute speeds, checked divides
    # every speed by the slowest one in the whole comparison (so that slowest
    # point sits at exactly 1 and every other point reads as "x times faster").
    # BUGFIX 2026-08-10 a two-position select_slider was an awkward control for
    # a binary choice; a checkbox states the on/off nature directly.
    want_relative = st.checkbox(
        "Panel (c): relative growth speed (v / v_min)",
        value=False,
        key="compare_tab__speed_relative",
        help=(
            "Divides every growth speed by the smallest positive growth speed "
            "across all compared datasets."
        ),
    )
    v_min = minimum_growth_speed(runs)
    normalize = want_relative and np.isfinite(v_min)
    if want_relative and not np.isfinite(v_min):
        st.warning("No positive growth speeds in this selection; showing absolute values.")

    fig = build_comparison_figure(
        runs,
        title="Comparison",
        growth_speed_reference=v_min if normalize else None,
    )
    st.plotly_chart(fig, width="stretch", theme=None)
    if normalize:
        st.caption(f"Panel (c) is normalized to v_min = {v_min:.4g} (lattice units).")

    st.subheader("Summary")
    table = summarize(runs)
    if normalize:
        # Same normalization as the plot, so the table can be read against it.
        table.insert(
            table.columns.get_loc("growth_speed_at_critical") + 1,
            "growth_speed_at_critical_rel",
            table["growth_speed_at_critical"] / v_min,
        )
    st.dataframe(_style_with_colors(table), width="stretch")
    st.caption("The `color` column is the curve colour used for that dataset in the figure.")
