"""Side-by-side comparison of two (or more) analyzed order-disorder run directories.

Every run directory that has been through ``analyzing_order_disorder.analyze_directory``
carries two cached results:

* ``order_disorder_analysis.csv`` -- one row per chemical potential with the order
  parameter ``m``, the corrected logarithmic supersaturation ``dphi = log S``, the
  susceptibility, the interface growth speed and the cluster observables ``q``/``r``.
* ``critical_supersat.txt`` -- the inflection point of ``m`` vs ``log S`` together
  with its sampling-resolution error and the driving scheme.

This module reads those caches back (it never re-runs the expensive w(q) scan) and
overlays the runs in one four-panel figure, so two data sets processed with the
identical pipeline can be compared directly. Run it as a script to reproduce the
S3/Δμ=0 vs. equilibrium-baseline comparison in ``RETHINKING_SUPERSAT``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import nesspy_analysis as npa

from analyzing_order_disorder import (
    ANALYSIS_CSV,
    growth_speed_at_critical,
    read_critical_supersat,
)

logger = logging.getLogger(__name__)

# Shared figure styling, as in the rest of 2026/.
try:
    from plot_defaults import BLUE, RED, set_plot_defaults

    set_plot_defaults()
except ImportError:  # pragma: no cover - styling is cosmetic
    logger.warning("plot_defaults not found; using matplotlib defaults.")
    RED, BLUE = "#ce3627", "#7894a2"


@dataclass
class AnalyzedRun:
    """One analyzed run directory, loaded from its cached pipeline output."""

    label: str            # short human-readable name used in the legend
    path: Path            # the run directory itself
    data: pd.DataFrame    # order_disorder_analysis.csv, sorted by dphi
    critical: float       # critical supersaturation (inflection point of m vs log S)
    critical_err: float   # its sampling-resolution error
    scheme: str           # canonical driving scheme, S0-S6
    thermos: npa.Thermos  # the parameters auto-detected from the out.csv headers
    color: str            # plot colour

    @property
    def sigmoid_params(self) -> np.ndarray:
        """Refit the logistic to the cached (dphi, m) pairs.

        The pipeline does not cache the fit parameters, only the inflection point
        it extracted from them, so the curve drawn here is refitted from the same
        points with the same estimator (:func:`nesspy_analysis.fit_sigmoid`). The
        refit therefore reproduces the cached ``critical`` value.
        """
        usable = self.data.dropna(subset=["dphi", "m"])
        return npa.fit_sigmoid(usable["dphi"].values, usable["m"].values)


def load_run(path: Path, label: str, color: str) -> AnalyzedRun:
    """Load one analyzed run directory from its cached pipeline output.

    Raises ``FileNotFoundError`` when the directory has not been through
    ``analyze_directory`` yet -- comparing runs analyzed with different settings
    would be misleading, so we require the cache rather than recomputing here.
    """
    path = Path(path)
    csv = path / ANALYSIS_CSV
    if not csv.is_file():
        raise FileNotFoundError(
            f"{csv} not found. Run analyzing_order_disorder.analyze_directory() "
            f"on {path} first."
        )

    data = pd.read_csv(csv).sort_values(by="dphi")
    critical, critical_err = read_critical_supersat(path)

    # Read the scheme back from the raw out.csv headers rather than trusting the
    # cached 'scheme' column: that is the same version-aware resolution the
    # pipeline itself uses, so a legacy run is remapped onto its S-name here too.
    thermos = npa.DynamicalOrderDisorder(path.name, path).get_thermos_from_file()

    return AnalyzedRun(
        label=label,
        path=path,
        data=data,
        critical=critical,
        critical_err=critical_err,
        scheme=npa.scheme_short_label(thermos.method),
        thermos=thermos,
        color=color,
    )


def _describe(run: AnalyzedRun) -> str:
    """Legend entry: the label plus the parameters that distinguish the runs."""
    t = run.thermos
    return (
        f"{run.label} "
        f"({npa.scheme_math_label(t.method)}, "
        rf"$\Delta\mu={t.dmu:g}$, $\Delta f={t.fres:g}$, $k={t.k:g}$)"
    )


def _mark_critical(ax, run: AnalyzedRun) -> None:
    """Draw a run's critical supersaturation as a dashed line + error band."""
    if np.isnan(run.critical):
        return
    ax.axvline(run.critical, color=run.color, linestyle="--", lw=1.5)
    if not np.isnan(run.critical_err):
        ax.axvspan(
            run.critical - run.critical_err,
            run.critical + run.critical_err,
            color=run.color,
            alpha=0.12,
            lw=0,
        )


def compare_runs(
    runs: list[AnalyzedRun],
    outfile: Path | None = None,
    title: str | None = None,
) -> plt.Figure:
    """Overlay the analyzed runs in a four-panel comparison figure.

    The panels are

    (a) order parameter ``m`` vs ``log S`` with the logistic fit and each run's
        critical supersaturation,
    (b) susceptibility ``chi = <m^2> - <m>^2`` vs ``log S``,
    (c) interface growth speed vs ``log S`` (logarithmic ordinate), with the
        speed at each run's critical supersaturation marked, and
    (d) the cluster observables: wrong-bond fraction ``q`` (left ordinate,
        filled markers) and normalized blue cluster size ``r`` (right ordinate,
        open markers).

    Panel (d) is what separates a genuinely mixed ``m = 0`` state (high ``q``,
    small ``r``) from flopping finite domains (lower ``q``, large ``r``).
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    ax_m, ax_chi, ax_v, ax_q = axes.ravel()

    markers = ["o", "s", "^", "D"]

    for run, marker in zip(runs, markers * len(runs)):
        data = run.data

        # --- (a) order parameter + logistic fit -----------------------------
        ax_m.errorbar(
            data["dphi"], data["m"], yerr=data["dm"],
            fmt=marker, capsize=4, ms=8, color=run.color,
            label=_describe(run),
        )
        dphi_fit = np.linspace(data["dphi"].min(), data["dphi"].max(), 400)
        ax_m.plot(
            dphi_fit, npa.sigmoid(dphi_fit, *run.sigmoid_params),
            color=run.color, lw=2, alpha=0.8,
        )
        _mark_critical(ax_m, run)

        # --- (b) susceptibility ---------------------------------------------
        # Recomputed here rather than read from the cached 'susceptibility'
        # column, which older analysis CSVs may not carry.
        ax_chi.plot(
            data["dphi"], data["m2"] - data["m"] ** 2,
            marker, ms=8, color=run.color, label=run.label,
        )
        _mark_critical(ax_chi, run)

        # --- (c) growth speed ------------------------------------------------
        ax_v.errorbar(
            data["dphi"], data["growth_speed"], yerr=data["dgrowth_speed"],
            fmt=marker, capsize=4, ms=8, color=run.color, label=run.label,
        )
        speed, dspeed = growth_speed_at_critical(data, run.critical)
        if not np.isnan(speed):
            ax_v.errorbar(
                [run.critical], [speed], yerr=[dspeed],
                fmt="*", ms=22, color=run.color, mec="k", mew=0.8, zorder=5,
                label=rf"$v(\Delta\phi_c) = {speed:.2e}$",
            )
        _mark_critical(ax_v, run)

        # --- (d) cluster observables q and r ---------------------------------
        ax_q.errorbar(
            data["dphi"], data["q_mean"], yerr=data["q_sem"],
            fmt=marker, capsize=4, ms=8, color=run.color, linestyle="none",
            label=rf"$\langle q \rangle$, {run.label}",
        )
        ax_q_r = getattr(ax_q, "_twin", None)
        if ax_q_r is None:
            ax_q_r = ax_q.twinx()
            ax_q._twin = ax_q_r  # reuse the same twin for every run
        ax_q_r.errorbar(
            data["dphi"], data["r_mean"], yerr=data["r_sem"],
            fmt=marker, capsize=4, ms=8, color=run.color,
            mfc="none", linestyle=":", lw=1.2,
            label=rf"$\langle r \rangle$, {run.label}",
        )
        _mark_critical(ax_q, run)

    ax_m.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax_m.set_ylabel(r"Order parameter $|m|$")
    ax_m.set_title("(a) order parameter", loc="left")
    ax_m.legend(fontsize=11)

    ax_chi.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax_chi.set_ylabel(r"Susceptibility $\chi = \langle m^2\rangle - \langle m\rangle^2$")
    ax_chi.set_title("(b) susceptibility", loc="left")
    ax_chi.legend(fontsize=13)

    ax_v.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax_v.set_ylabel(r"Interface growth speed $v$")
    ax_v.set_yscale("log")
    ax_v.set_title(r"(c) growth speed ($\star$ at $\Delta\phi_c$)", loc="left")
    ax_v.legend(fontsize=11)

    ax_q.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax_q.set_ylabel(r"Wrong-bond fraction $\langle q \rangle$ (filled)")
    ax_q._twin.set_ylabel(r"Cluster size $\langle r \rangle$ (open)")
    ax_q.set_title("(d) cluster observables", loc="left")
    # q lives on ax_q and r on its twin, so collect the handles of both axes into
    # a single legend; drawing it on the twin keeps it on top of every data set.
    handles_q, labels_q = ax_q.get_legend_handles_labels()
    handles_r, labels_r = ax_q._twin.get_legend_handles_labels()
    ax_q._twin.legend(
        handles_q + handles_r, labels_q + labels_r, fontsize=11, loc="center left"
    )

    if title:
        fig.suptitle(title, fontsize=18)
    fig.tight_layout()

    if outfile is not None:
        fig.savefig(outfile, dpi=300)
        logger.info("Saved comparison figure to %s", outfile)

    return fig


def summarize(runs: list[AnalyzedRun]) -> pd.DataFrame:
    """One row per run with the parameters and the critical supersaturation."""
    records = []
    for run in runs:
        speed, dspeed = growth_speed_at_critical(run.data, run.critical)
        records.append(
            {
                "label": run.label,
                "directory": run.path.name,
                "nesspy_scheme": run.scheme,
                "jhom": run.thermos.jhom,
                "jhet": run.thermos.jhet,
                "dmu": run.thermos.dmu,
                "fres": run.thermos.fres,
                "k": run.thermos.k,
                "n_mu": len(run.data),
                "critical_supersat": run.critical,
                "critical_supersat_err": run.critical_err,
                "growth_speed_at_critical": speed,
                "dgrowth_speed_at_critical": dspeed,
            }
        )
    return pd.DataFrame(records)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    PARENT = Path("/Volumes/2025/RETHINKING_SUPERSAT")

    runs = [
        load_run(
            PARENT / "BASELINE_JHOM_35",
            label="Baseline (no inert states)",
            color=BLUE,
        ),
        load_run(
            PARENT / "X_320_Y_80_3.0_D0.0_JHOM_-3.50_F0.0_K1.0",
            label=r"S3, $\Delta\mu=0$",
            color=RED,
        ),
    ]

    summary = summarize(runs)
    print(summary.to_string(index=False))
    summary.to_csv(PARENT / "comparison_S3_D0_vs_baseline.csv", index=False)

    compare_runs(
        runs,
        outfile=PARENT / "comparison_S3_D0_vs_baseline.png",
        title=r"Undriven S3 vs. equilibrium baseline  ($J_{\rm hom}=-3.5$, $J_{\rm het}=-2.0$)",
    )
