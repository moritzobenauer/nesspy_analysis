"""Interactive (zoom/pan) four-panel comparison figure, built with Plotly.

One function, `build_comparison_figure()`, used by both Tab 2 (a single
`AnalyzedRun`) and Tab 3 (several, overlaid). This mirrors the matplotlib layout
in `2026/compare_order_disorder_runs.py::compare_runs()`:

(a) order parameter m vs log(S) = dphi, with the refit sigmoid curve and the
    run's critical supersaturation marked;
(b) susceptibility chi = <m^2> - <m>^2 vs log(S);
(c) interface growth speed (log y-axis) vs log(S), with a star at the value
    nearest the critical supersaturation;
(d) cluster observables: wrong-bond fraction q (primary y, filled markers) and
    normalized blue cluster size r (secondary y, open markers).

Two conventions worth knowing:

* Every data series is drawn as `lines+markers` -- the points are ordered in
  `dphi` (`load_run()` sorts them), so the connecting line is a reading aid
  along the mu sweep, not a fit. The only genuine *fit* curve in the figure is
  the sigmoid in panel (a), which is drawn without markers.
* In panel (d) the two observables get different colours: q keeps the run's own
  colour, r gets that colour hue-rotated by 180 degrees (`_complementary()`).
  Deriving r's colour from the run's rather than fixing it means overlaid runs
  in Tab 3 still each get their own pair. With a single run on screen the two
  y-axis titles are tinted to match, which is the unambiguous legend; with
  several, filled-vs-open markers and solid-vs-dotted lines separate q from r.

Axis titles are plain Unicode (Δφ, χ, ⟨q⟩), *not* LaTeX: Streamlit serves Plotly
without MathJax, so a `$...$` title renders as literal dollar-sign text.
"""

from __future__ import annotations

import colorsys

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import nesspy_analysis as npa

from webapp.pipeline_status import growth_speed_at_critical

# x-axis quantity, shared by all four panels.
X_LABEL = "Δφ = log S"

# Fallback colour for the secondary (cluster-size) series if a run's colour is
# not a plain '#rrggbb' string we can hue-rotate.
FALLBACK_SECONDARY_COLOR = "#ff8b6b"

# Dark styling, matching the app's navy -> slate gradient background (see
# webapp/app.py). The paper is transparent so the gradient shows through and the
# figure reads as part of the page rather than as a pasted-in white rectangle;
# the plot area itself gets a faint light wash so the data still sits on a
# defined panel.
FONT_COLOR = "#e6e9ef"
PAPER_BGCOLOR = "rgba(0,0,0,0)"
PLOT_BGCOLOR = "rgba(255,255,255,0.04)"
GRID_COLOR = "rgba(230,233,239,0.14)"
ZERO_LINE_COLOR = "rgba(230,233,239,0.30)"

# Perceived-luminance floor for the derived cluster-size colour: on the dark
# plot background a dark colour disappears, so `_complementary()` brightens
# until it clears this.
MIN_LUMINANCE = 0.38


def _luminance(r: float, g: float, b: float) -> float:
    """Rec. 709 relative luminance of an RGB triple in [0, 1]."""
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _complementary(color: str) -> str:
    """Hue-rotate a '#rrggbb' colour by 180 degrees, then brighten if needed.

    Used only to pick the second colour of a run's (q, r) pair in panel (d), so
    the two observables are always distinguishable from each other while staying
    tied to the run they belong to.
    """
    color = color.strip()
    if not (color.startswith("#") and len(color) == 7):
        return FALLBACK_SECONDARY_COLOR
    try:
        r, g, b = (int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    except ValueError:
        return FALLBACK_SECONDARY_COLOR
    h, lightness, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + 0.5) % 1.0
    # Bump saturation a little so the rotated colour stays vivid next to the
    # original even for washed-out inputs.
    s = min(1.0, s * 1.1)
    # Then lighten until it reads on the dark plot background. Equal lightness
    # in HLS is not equal brightness to the eye (a rotated blue lands on a
    # yellow that is already bright, a rotated yellow on a dim blue), so this
    # steps on perceived luminance rather than on HLS lightness alone.
    while lightness < 0.85 and _luminance(*colorsys.hls_to_rgb(h, lightness, s)) < MIN_LUMINANCE:
        lightness += 0.02
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return "#{:02x}{:02x}{:02x}".format(*(round(c * 255) for c in (r, g, b)))


def minimum_growth_speed(runs: list) -> float:
    """Smallest strictly positive growth speed across every run.

    This is the reference for the "relative" growth-speed mode: dividing by it
    puts the slowest measured interface in the whole comparison at exactly 1.
    Non-positive and NaN speeds are ignored (they cannot be plotted on the log
    axis either). Returns NaN if no run has a usable speed.
    """
    speeds = [
        v
        for run in runs
        for v in np.asarray(run.data["growth_speed"], dtype=float)
        if np.isfinite(v) and v > 0
    ]
    return float(min(speeds)) if speeds else float("nan")


def _mark_critical(fig: go.Figure, run, row: int, col: int) -> None:
    """Draw a run's critical supersaturation as a dashed vline + error band."""
    if np.isnan(run.critical):
        return
    fig.add_vline(
        x=run.critical, row=row, col=col,
        line_color=run.color, line_dash="dash", line_width=1.5,
    )
    if np.isfinite(run.critical_err):
        fig.add_vrect(
            x0=run.critical - run.critical_err,
            x1=run.critical + run.critical_err,
            row=row, col=col,
            fillcolor=run.color, opacity=0.12, line_width=0,
        )


def build_comparison_figure(
    runs: list,
    title: str | None = None,
    growth_speed_reference: float | None = None,
) -> go.Figure:
    """Overlay one or more AnalyzedRun objects in a four-panel Plotly figure.

    ``growth_speed_reference``, when a finite positive number, divides every
    growth speed (and its error, and the star at the critical point) in panel
    (c). Pass :func:`minimum_growth_speed` to read that panel as "how many times
    faster than the slowest interface in this comparison", which is what the
    Compare tab's relative mode does. ``None`` plots the absolute speeds.
    """
    normalize = growth_speed_reference is not None and (
        np.isfinite(growth_speed_reference) and growth_speed_reference > 0
    )
    v_scale = float(growth_speed_reference) if normalize else 1.0

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "(a) order parameter", "(b) susceptibility",
            "(c) growth speed", "(d) cluster observables",
        ),
        specs=[[{}, {}], [{}, {"secondary_y": True}]],
        horizontal_spacing=0.12, vertical_spacing=0.16,
    )

    for run in runs:
        data = run.data
        cluster_color = _complementary(run.color)
        # Shared style for every measured series: markers on top of a thin
        # connecting line through the mu sweep.
        line_style = dict(color=run.color, width=1.5)
        marker_style = dict(color=run.color, size=8)

        # --- (a) order parameter + logistic fit -----------------------------
        fig.add_trace(
            go.Scatter(
                x=data["dphi"], y=data["m"],
                error_y=dict(type="data", array=data["dm"]),
                mode="lines+markers", line=line_style, marker=marker_style,
                name=run.label, legendgroup=run.label, showlegend=True,
            ),
            row=1, col=1,
        )
        dphi_fit = np.linspace(data["dphi"].min(), data["dphi"].max(), 400)
        fig.add_trace(
            go.Scatter(
                x=dphi_fit, y=npa.sigmoid(dphi_fit, *run.sigmoid_params),
                mode="lines", line=dict(color=run.color, width=2, dash="dot"),
                name=f"{run.label}: sigmoid fit",
                legendgroup=run.label, showlegend=False, hoverinfo="skip",
            ),
            row=1, col=1,
        )
        _mark_critical(fig, run, row=1, col=1)

        # --- (b) susceptibility -----------------------------------------------
        fig.add_trace(
            go.Scatter(
                x=data["dphi"], y=data["susceptibility"],
                mode="lines+markers", line=line_style, marker=marker_style,
                name=f"{run.label}: χ",
                legendgroup=run.label, showlegend=False,
            ),
            row=1, col=2,
        )
        _mark_critical(fig, run, row=1, col=2)

        # --- (c) growth speed ---------------------------------------------------
        fig.add_trace(
            go.Scatter(
                x=data["dphi"], y=data["growth_speed"] / v_scale,
                error_y=dict(type="data", array=data["dgrowth_speed"] / v_scale),
                mode="lines+markers", line=line_style, marker=marker_style,
                name=f"{run.label}: v",
                legendgroup=run.label, showlegend=False,
            ),
            row=2, col=1,
        )
        speed, dspeed = growth_speed_at_critical(data, run.critical)
        if not np.isnan(speed):
            fig.add_trace(
                go.Scatter(
                    x=[run.critical], y=[speed / v_scale],
                    error_y=dict(type="data", array=[dspeed / v_scale]),
                    mode="markers",
                    marker=dict(
                        symbol="star", size=18, color=run.color,
                        line=dict(color=FONT_COLOR, width=1),
                    ),
                    name=f"{run.label}: v at critical",
                    legendgroup=run.label, showlegend=False,
                    hovertemplate=(
                        f"v(critical) = {speed / v_scale:.3g} × v_min<extra></extra>"
                        if normalize
                        else f"v(critical) = {speed:.3e}<extra></extra>"
                    ),
                ),
                row=2, col=1,
            )
        _mark_critical(fig, run, row=2, col=1)

        # --- (d) cluster observables q (primary) and r (secondary) -------------
        # Different colours per observable, per the module docstring.
        fig.add_trace(
            go.Scatter(
                x=data["dphi"], y=data["q_mean"],
                error_y=dict(type="data", array=data["q_sem"]),
                mode="lines+markers",
                line=dict(color=run.color, width=1.5),
                marker=dict(color=run.color, size=8),
                name=f"{run.label}: ⟨q⟩",
                legendgroup=run.label, showlegend=False,
            ),
            row=2, col=2, secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=data["dphi"], y=data["r_mean"],
                error_y=dict(type="data", array=data["r_sem"], color=cluster_color),
                mode="lines+markers",
                line=dict(color=cluster_color, width=1.5, dash="dot"),
                marker=dict(
                    color=cluster_color, size=8, symbol="circle-open",
                    line=dict(color=cluster_color, width=2),
                ),
                name=f"{run.label}: ⟨r⟩",
                legendgroup=run.label, showlegend=False,
            ),
            row=2, col=2, secondary_y=True,
        )
        _mark_critical(fig, run, row=2, col=2)

    # --- axes ---------------------------------------------------------------
    # dtick="D2" labels 1/2/5 per decade instead of Plotly's default 1..9, which
    # turns into an unreadable column of bare digits on a multi-decade axis.
    fig.update_yaxes(type="log", dtick="D2", row=2, col=1)
    for row, col in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        fig.update_xaxes(title_text=X_LABEL, row=row, col=col)
    fig.update_yaxes(title_text="order parameter |m|", row=1, col=1)
    fig.update_yaxes(title_text="susceptibility χ = ⟨m²⟩ − ⟨m⟩²", row=1, col=2)
    fig.update_yaxes(
        title_text=(
            "growth speed v / v_min (log scale)"
            if normalize
            else "growth speed v (log scale)"
        ),
        row=2, col=1,
    )

    # With a single run the panel-(d) axis titles are tinted to match their
    # series, which makes the two-colour mapping self-explanatory. With several
    # runs there is no single colour to tint them with, so they stay default and
    # the marker/line style carries the distinction.
    single = runs[0] if len(runs) == 1 else None
    fig.update_yaxes(
        title_text="wrong-bond fraction ⟨q⟩ (filled, solid)",
        title_font_color=single.color if single else None,
        row=2, col=2, secondary_y=False,
    )
    fig.update_yaxes(
        title_text="cluster size ⟨r⟩ (open, dotted)",
        title_font_color=_complementary(single.color) if single else None,
        row=2, col=2, secondary_y=True,
    )

    # Dark styling to match the app background. `theme=None` is passed to
    # st.plotly_chart by both tabs so these settings survive as written instead
    # of being overwritten by Streamlit's own Plotly template.
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=ZERO_LINE_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=ZERO_LINE_COLOR)
    # Panel (d) has two y axes; gridding both draws a mesh of misaligned lines.
    fig.update_yaxes(showgrid=False, row=2, col=2, secondary_y=True)
    fig.update_layout(
        title=title,
        height=850,
        margin=dict(l=70, r=70, t=110, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
        hovermode="closest",
        template="plotly_dark",
        paper_bgcolor=PAPER_BGCOLOR,
        plot_bgcolor=PLOT_BGCOLOR,
        font=dict(color=FONT_COLOR),
    )
    # make_subplots writes the panel titles as annotations, which the template
    # change above does not reach.
    fig.update_annotations(font_color=FONT_COLOR)
    return fig
