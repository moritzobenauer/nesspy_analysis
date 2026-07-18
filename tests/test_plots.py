"""Lattice observables and the log(S) plotting helpers."""
import matplotlib
matplotlib.use("Agg")  # headless; no display needed for figure construction

import numpy as np
import pandas as pd
import pytest

from nesspy_analysis import (
    calculate_order_parameter, calculate_average_cluster_size,
    plot_q_vs_logS, plot_r_vs_logS, plot_cluster_observables,
)


def test_order_parameter_zero_when_species_balanced():
    # Equal reds (1) and blues (2) over the whole band -> |m| = 0 exactly.
    lat = np.array([[1, 2] * 5] * 6)
    m, m2 = calculate_order_parameter(lat, "MLO2024", lb_trr=0.0, ub_trr=1.0)
    assert m == pytest.approx(0.0)
    assert m2 == pytest.approx(0.0)


def test_order_parameter_all_blue():
    # All-blue band: the implementation seeds counts=1, so m = N/(N+1).
    lat = np.full((6, 10), 2)
    n = lat.size
    m, m2 = calculate_order_parameter(lat, "MLO2024", lb_trr=0.0, ub_trr=1.0)
    assert m == pytest.approx(n / (n + 1))
    assert m2 == pytest.approx(m**2)


def test_cluster_size_counts_blue_block(blue_block_lattice):
    # One 3x3 blue cluster (size 9 >= min_size); helper returns (count, 2*mean).
    num, doubled_mean = calculate_average_cluster_size(
        blue_block_lattice, lb_trr=0.0, ub_trr=1.0, min_size=8
    )
    assert num == 1
    assert doubled_mean == pytest.approx(2 * 9)


def test_cluster_size_threshold_and_empty(blue_block_lattice):
    # Raising the threshold above the cluster size discards it -> (0, 0).
    assert calculate_average_cluster_size(
        blue_block_lattice, lb_trr=0.0, ub_trr=1.0, min_size=10
    ) == (0, 0)
    assert calculate_average_cluster_size(
        np.zeros((10, 10), dtype=int), lb_trr=0.0, ub_trr=1.0
    ) == (0, 0)


def _fake_curve_df():
    return pd.DataFrame({
        "dphi": [-1.0, 0.0, 1.0, np.nan],   # last row dropped by the plotters
        "q_mean": [0.05, 0.25, 0.5, 0.5], "q_sem": [0.01] * 4,
        "r_mean": [0.6, 0.3, 0.05, 0.05], "r_sem": [0.02] * 4,
    })


@pytest.mark.parametrize("fn,ylabel", [
    (plot_q_vs_logS, "wrong-bond"),
    (plot_r_vs_logS, "cluster size"),
])
def test_single_panel_plotters_drop_nan_rows(fn, ylabel):
    fig, ax = fn(_fake_curve_df())
    assert ylabel in ax.get_ylabel()
    # 3 finite dphi points: the main data line carries 3 vertices (errorbar also
    # adds shorter cap lines, so take the longest).
    assert max(len(ln.get_xdata()) for ln in ax.get_lines()) == 3


def test_combined_figure_has_two_panels_and_critical_marker():
    fig, axes = plot_cluster_observables(_fake_curve_df(), critical_supersat=0.2, min_size=8)
    assert len(axes) == 2
    # critical_supersat draws a vertical line on each panel.
    for ax in axes:
        assert any(np.allclose(ln.get_xdata(), 0.2) for ln in ax.get_lines())
