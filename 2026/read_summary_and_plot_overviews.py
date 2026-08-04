# Read a parent sweep's sweep_summary.csv, let the user pick which of its analyzed
# datasets to include (interactive questionary checkbox), then plot the growth
# speed and order parameter as a function of the logarithmic supersaturation for
# every selected dataset -- both as individual per-dataset figures (saved next to
# the dataset) and as combined overlay figures across all selections (saved in the
# parent directory).
#
# Each dataset's order_disorder_analysis.csv (written by analyzing_order_disorder.py)
# holds one row per chemical potential mu with, among others:
#   - dphi            : logarithmic supersaturation  Delta phi = log S   (x axis)
#   - m,   dm         : (absolute) order parameter + error
#   - growth_speed, dgrowth_speed : interface growth speed + error
#
# The sweep_summary.csv in the parent directory lists one row per analyzed dataset
# (its `directory` column names the subfolder), so it is our menu of choices.

import sys
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import nesspy_analysis as npa

# Reuse the sweeper's definition of "growth speed at the critical
# supersaturation" (the nearest sampled raw point, not an interpolation) so the
# star we draw matches the value in sweep_summary.csv exactly.
from analyzing_order_disorder import growth_speed_at_critical

logger = logging.getLogger(__name__)

# The per-dataset analysis CSV produced by analyzing_order_disorder.py. Kept as a
# module constant so the name lives in exactly one place here too.
ANALYSIS_CSV = "order_disorder_analysis.csv"
SUMMARY_CSV = "sweep_summary.csv"

# Shared figure styling. plot_defaults.py sits next to this script (duplicated
# from the repo root, as elsewhere in 2026/); fall back silently to matplotlib
# defaults if it is not importable.
try:
    from plot_defaults import set_plot_defaults

    set_plot_defaults()
except ImportError:
    logger.warning("plot_defaults not found; using matplotlib defaults.")


def tui_to_select_datasets(parent_dir: Path, summary: pd.DataFrame) -> list[str]:
    """Interactively choose which datasets from the sweep summary to plot.

    Presents a ``questionary`` checkbox (all datasets pre-selected) listing every
    ``directory`` in ``summary`` that (a) exists as a subfolder of ``parent_dir``
    and (b) actually has an ``order_disorder_analysis.csv`` to plot -- rows without
    that CSV are dropped up front so the user cannot pick something unplottable.

    Returns the list of selected directory names (a subset of ``summary``'s
    ``directory`` column). Raises ``SystemExit`` if nothing plottable exists or the
    user cancels / selects nothing, so callers can treat the return as non-empty.
    """
    # keep only summary rows whose dataset directory has an analysis CSV to plot.
    plottable = []
    for directory in summary["directory"]:
        csv = parent_dir / directory / ANALYSIS_CSV
        if csv.is_file():
            plottable.append(directory)
        else:
            logger.warning(
                "Skipping %s: no %s found (run the analysis first).",
                directory, ANALYSIS_CSV,
            )

    if not plottable:
        raise SystemExit(
            f"No datasets under {parent_dir} have an {ANALYSIS_CSV} to plot."
        )

    # the interactive checkbox needs a real terminal; when stdin is piped (e.g.
    # run non-interactively) prompt_toolkit crashes, so bail out with a hint.
    if not sys.stdin.isatty():
        raise SystemExit(
            "Interactive dataset selection needs a terminal (stdin is not a "
            "tty). Re-run with --all to include every plottable dataset."
        )

    # questionary is an optional dependency used only for this interactive menu;
    # import it lazily so the module still imports (e.g. for its plotting helpers)
    # in environments where questionary is unavailable.
    try:
        import questionary
    except ImportError:
        raise SystemExit(
            "questionary is required for the interactive dataset selection; "
            "install it (`uv add questionary`) or add --all to skip the menu."
        )

    # all datasets checked by default; the user unchecks the ones to exclude.
    choices = [questionary.Choice(title=d, checked=True) for d in plottable]
    selected = questionary.checkbox(
        "Select datasets to include in the overview plots:",
        choices=choices,
    ).ask()

    # .ask() returns None if the user aborts (Ctrl-C); [] if they deselect all.
    if not selected:
        raise SystemExit("No datasets selected; nothing to plot.")

    return selected


def growth_speed_versus_supersat(
    data: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Growth speed as a function of the logarithmic supersaturation.

    Takes a dataset's ``order_disorder_analysis.csv`` (already loaded) and returns
    ``(x, y, yerr)`` = (logarithmic supersaturation ``dphi``, ``growth_speed``,
    ``dgrowth_speed``), sorted by ``dphi`` and with any rows missing ``dphi`` or
    ``growth_speed`` dropped so the arrays are clean for plotting.
    """
    usable = data.dropna(subset=["dphi", "growth_speed"]).sort_values(by="dphi")
    x = usable["dphi"].to_numpy()
    y = usable["growth_speed"].to_numpy()
    # dgrowth_speed may be absent in older CSVs; fall back to no error bars.
    yerr = (
        usable["dgrowth_speed"].to_numpy()
        if "dgrowth_speed" in usable.columns
        else None
    )
    return x, y, yerr


def order_parameter_versus_supersat(
    data: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Order parameter as a function of the logarithmic supersaturation.

    Takes a dataset's ``order_disorder_analysis.csv`` (already loaded) and returns
    ``(x, y, yerr)`` = (logarithmic supersaturation ``dphi``, order parameter
    ``m``, its error ``dm``), sorted by ``dphi`` and with rows missing ``dphi`` or
    ``m`` dropped.
    """
    usable = data.dropna(subset=["dphi", "m"]).sort_values(by="dphi")
    x = usable["dphi"].to_numpy()
    y = usable["m"].to_numpy()
    yerr = usable["dm"].to_numpy() if "dm" in usable.columns else None
    return x, y, yerr


def _plot_single_dataset(
    name: str,
    data: pd.DataFrame,
    out_dir: Path,
    critical_supersat: float,
    scheme: str = "",
    critical_supersat_err: float = float("nan"),
) -> None:
    """Save the two per-dataset figures (growth speed + order parameter).

    ``critical_supersat`` (the order-disorder transition point, from
    ``sweep_summary.csv``) marks the growth speed there with a star on the growth
    speed figure; pass ``nan`` to omit the marker. ``critical_supersat_err`` is
    its error (from the same summary), drawn as a shaded band around the
    transition line on the order-parameter figure; pass ``nan`` to omit the band.
    ``scheme`` (e.g. ``'S1'``) is appended to each figure title so the driving
    scheme is stated on the plot; pass ``""`` to omit it.
    """
    title = f"{name} ({scheme})" if scheme else name
    # growth speed vs log supersaturation (log y axis, as growth speeds span
    # roughly an order of magnitude and are strictly positive).
    x, y, yerr = growth_speed_versus_supersat(data)
    fig, ax = plt.subplots()
    ax.errorbar(x, y, yerr=yerr, fmt="o", capsize=5)
    # star the growth speed at the critical supersaturation (transition point).
    gs_c, _ = growth_speed_at_critical(data, critical_supersat)
    if not np.isnan(critical_supersat) and not np.isnan(gs_c):
        ax.plot(
            critical_supersat, gs_c,
            marker="*", markersize=20, color="tab:red", linestyle="none",
            zorder=5,
            label=rf"$\Delta\phi_c = {critical_supersat:.3f}$",
        )
        ax.legend()
    ax.set_yscale("log")
    ax.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax.set_ylabel(r"Growth speed $\langle v \rangle$")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_dir / "growth_speed_vs_supersat.png", dpi=300)
    plt.close(fig)

    # order parameter vs log supersaturation (linear y axis).
    x, y, yerr = order_parameter_versus_supersat(data)
    fig, ax = plt.subplots()
    ax.errorbar(x, y, yerr=yerr, fmt="o", capsize=5, label=r"Exact $w(q)$ method")

    # BUGFIX 2026-07-21 sigmoid fit + transition line were dropped from this
    # per-dataset order-parameter plot (it only has the cached CSV, not the live
    # analysis object). Refit the logistic here from the cached (dphi, m, dm) so
    # this figure matches the one analyze_directory produces: overlay the
    # sigmoidal fit and mark the critical supersaturation with a vertical line.
    try:
        sigmoid_params = npa.fit_sigmoid(x, y, yerr=yerr)
        dphi_fit = np.linspace(x.min(), x.max(), 400)
        ax.plot(
            dphi_fit, npa.sigmoid(dphi_fit, *sigmoid_params),
            color="k", lw=2, label="Sigmoidal fit",
        )
    except Exception as e:
        # a fit failure must not lose the whole figure; skip the overlay only.
        logger.warning("Could not refit sigmoid for %s: %s", name, e)

    if not np.isnan(critical_supersat):
        # transition line, labelled with the value (+ error when available).
        if np.isnan(critical_supersat_err):
            crit_label = rf"$\Delta\phi_c = {critical_supersat:.3f}$"
        else:
            crit_label = (
                rf"$\Delta\phi_c = {critical_supersat:.3f} "
                rf"\pm {critical_supersat_err:.3f}$"
            )
        ax.axvline(
            critical_supersat, color="tab:red", linestyle="--", label=crit_label,
        )
        if not np.isnan(critical_supersat_err):
            ax.axvspan(
                critical_supersat - critical_supersat_err,
                critical_supersat + critical_supersat_err,
                color="tab:red", alpha=0.15,
            )

    ax.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax.set_ylabel(r"Order parameter $|m|$")
    ax.legend()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_dir / "order_parameter_vs_supersat.png", dpi=300)
    plt.close(fig)


def _plot_combined(
    datasets: dict[str, tuple[pd.DataFrame, float, str]], parent_dir: Path
) -> None:
    """Save the two combined overlay figures across all selected datasets.

    ``datasets`` maps a dataset name to ``(data, critical_supersat, scheme)``.
    One color per dataset, shared axes; written into ``parent_dir`` as
    ``overview_growth_speed_vs_supersat.png`` and
    ``overview_order_parameter_vs_supersat.png``. The scheme label (e.g. ``S1``)
    is folded into each legend entry. On the growth speed overlay the growth
    speed at each dataset's critical supersaturation is starred in that dataset's
    own line color.
    """
    # combined growth speed overlay (log y axis).
    fig, ax = plt.subplots()
    for name, (data, critical_supersat, scheme) in datasets.items():
        label = f"{name} ({scheme})" if scheme else name
        x, y, yerr = growth_speed_versus_supersat(data)
        line = ax.errorbar(
            x, y, yerr=yerr, fmt="o-", capsize=4, markersize=5, label=label
        )
        # star the transition-point growth speed in this dataset's line color.
        gs_c, _ = growth_speed_at_critical(data, critical_supersat)
        if not np.isnan(critical_supersat) and not np.isnan(gs_c):
            ax.plot(
                critical_supersat, gs_c,
                marker="*", markersize=18,
                color=line[0].get_color(), markeredgecolor="k",
                linestyle="none", zorder=5,
            )
    ax.set_yscale("log")
    ax.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax.set_ylabel(r"Growth speed $\langle v \rangle$")
    ax.legend(fontsize="small")
    fig.tight_layout()
    fig.savefig(parent_dir / "overview_growth_speed_vs_supersat.png", dpi=300)
    plt.close(fig)

    # combined order parameter overlay (linear y axis).
    fig, ax = plt.subplots()
    for name, (data, _critical_supersat, scheme) in datasets.items():
        label = f"{name} ({scheme})" if scheme else name
        x, y, yerr = order_parameter_versus_supersat(data)
        ax.errorbar(x, y, yerr=yerr, fmt="o-", capsize=4, markersize=5, label=label)
    ax.set_xlabel(r"Logarithmic supersaturation $\Delta\phi = \log S$")
    ax.set_ylabel(r"Order parameter $|m|$")
    ax.legend(fontsize="small")
    fig.tight_layout()
    fig.savefig(parent_dir / "overview_order_parameter_vs_supersat.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Plot growth speed and order parameter vs logarithmic "
        "supersaturation for datasets in a parent sweep directory."
    )
    argparser.add_argument(
        "-i",
        "--parent_dir",
        type=str,
        required=True,
        help="Path to the parent directory containing the %s and the dataset "
        "subdirectories." % SUMMARY_CSV,
    )
    argparser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Skip the interactive menu and include every plottable dataset.",
    )
    argparser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose (INFO-level) output.",
    )
    args = argparser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    # define the parent directory to read from
    parent_dir = Path(args.parent_dir)
    if not parent_dir.is_dir():
        raise SystemExit(f"Parent directory {parent_dir} does not exist.")

    # the sweep summary is our menu of available datasets.
    summary_csv = parent_dir / SUMMARY_CSV
    if not summary_csv.is_file():
        raise SystemExit(
            f"No {SUMMARY_CSV} in {parent_dir}; run parent_sweeper.py first."
        )
    summary = pd.read_csv(summary_csv)

    # choose datasets: either all plottable ones (--all) or via the checkbox TUI.
    if args.all:
        selected = [
            d
            for d in summary["directory"]
            if (parent_dir / d / ANALYSIS_CSV).is_file()
        ]
        if not selected:
            raise SystemExit(
                f"No datasets under {parent_dir} have an {ANALYSIS_CSV} to plot."
            )
    else:
        selected = tui_to_select_datasets(parent_dir, summary)

    # critical supersaturation per dataset, keyed by directory name (the star
    # position). Missing/NaN entries simply omit the star.
    critical_by_dir = (
        summary.set_index("directory")["critical_supersat"].to_dict()
        if "critical_supersat" in summary.columns
        else {}
    )

    # error on the critical supersaturation per dataset (the shaded band around
    # the transition line). Missing/NaN entries simply omit the band.
    critical_err_by_dir = (
        summary.set_index("directory")["critical_supersat_err"].to_dict()
        if "critical_supersat_err" in summary.columns
        else {}
    )

    # driving-scheme label per dataset (e.g. 'S1'), keyed by directory name.
    # Older summaries without a 'scheme' column simply get no label.
    scheme_by_dir = (
        summary.set_index("directory")["scheme"].to_dict()
        if "scheme" in summary.columns
        else {}
    )

    # load each selected dataset once, make its per-dataset plots, and collect it
    # (with its critical supersaturation and scheme) for the combined overlay.
    loaded: dict[str, tuple[pd.DataFrame, float, str]] = {}
    for name in selected:
        dataset_dir = parent_dir / name
        data = pd.read_csv(dataset_dir / ANALYSIS_CSV)
        critical_supersat = float(critical_by_dir.get(name, float("nan")))
        critical_supersat_err = float(critical_err_by_dir.get(name, float("nan")))
        scheme = str(scheme_by_dir.get(name, "") or "")
        _plot_single_dataset(
            name, data, dataset_dir, critical_supersat, scheme,
            critical_supersat_err=critical_supersat_err,
        )
        loaded[name] = (data, critical_supersat, scheme)
        print(f"Saved per-dataset plots for {name}")

    # combined overview across all selected datasets, written to the parent dir.
    _plot_combined(loaded, parent_dir)
    print(
        f"\nSaved combined overview plots for {len(loaded)} dataset(s) to "
        f"{parent_dir}"
    )
