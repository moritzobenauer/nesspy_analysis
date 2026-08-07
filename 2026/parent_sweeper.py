# This is a sweeper over a parent-parent directory

import logging
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import nesspy_analysis as npa

from analyzing_order_disorder import (
    ANALYSIS_CSV,
    analyze_directory,
    growth_speed_at_critical,
    # plot_lattice_overviews now lives next to analyze_directory so the single-run
    # CLI in analyzing_order_disorder.py can call it too (it used to be defined
    # here, which would have made that a circular import).
    plot_lattice_overviews,
    read_critical_supersat,
)

logger = logging.getLogger(__name__)


def summarize_skipped(run_dir: Path, compute_speed: bool = False) -> dict:
    """Rebuild an ``analyze_directory``-shaped summary for an already-analyzed run.

    Re-parses the thermodynamic parameters from the run's out.csv headers (cheap;
    no ``get_wq()`` multiprocessing) and reads the previously computed critical
    supersaturation from ``critical_supersat.txt``, so a skipped run still appears
    as a full row in the final sweep summary.

    When ``compute_speed`` is set, the growth speed at the critical
    supersaturation is recovered from the cached ``order_disorder_analysis.csv``
    (which already holds per-mu ``dphi`` and ``growth_speed``), keeping the
    skipped rows consistent with the freshly analyzed ones.
    """
    analysis_object = npa.DynamicalOrderDisorder(run_dir.name, run_dir)
    thermos = analysis_object.get_thermos_from_file()
    critical_supersat, critical_supersat_err = read_critical_supersat(run_dir)
    summary = {
        "directory": run_dir.name,
        "jhom": thermos.jhom,
        "jhet": thermos.jhet,
        "fres": thermos.fres,
        "dmu": thermos.dmu,
        "k": thermos.k,
        "method": thermos.method,
        # short driving-scheme label (S1..S6), consistent with analyze_directory.
        "scheme": npa.scheme_short_label(thermos.method),
        "critical_supersat": critical_supersat,
        "critical_supersat_err": critical_supersat_err,
    }
    if compute_speed:
        gs, dgs = float("nan"), float("nan")
        cached_csv = run_dir / ANALYSIS_CSV
        if cached_csv.is_file():
            cached = pd.read_csv(cached_csv)
            gs, dgs = growth_speed_at_critical(cached, critical_supersat)
        summary["growth_speed_at_critical"] = gs
        summary["dgrowth_speed_at_critical"] = dgs
    return summary


if __name__ == "__main__":
    # Everything sits behind the __main__ guard because analyze_directory ->
    # get_wq() spawns a multiprocessing Pool.

    argparser = argparse.ArgumentParser(
        description="Sweep over a parent directory and analyze order-disorder transitions."
    )
    argparser.add_argument(
        "-i",
        "--parent_dir",
        type=str,
        required=True,
        help="Path to the parent directory containing subdirectories with simulation data.",
    )

    argparser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output during analysis.",
    )

    argparser.add_argument(
        "-s",
        "--skip",
        action="store_true",
        help="Skip runs already analyzed (an %s is present); reuse their existing "
        "results in the final summary instead of recomputing." % ANALYSIS_CSV,
    )

    argparser.add_argument(
        "-m",
        "--min_size",
        type=int,
        default=8,
        help="Minimum blue-cluster cardinality kept for the r(log S) observable "
        "(default: 8; use 5 for the 'larger than four' rule).",
    )

    argparser.add_argument(
        "--speed",
        action="store_true",
        help="Also report the interface growth speed at the critical "
        "supersaturation (+ error) in the sweep summary.",
    )

    # w(q) is the expensive part (a multiprocessing lattice scan). It runs by
    # default; --no-wq skips it and instead reuses any cached w(q) results on
    # disk to locate the critical supersaturation (warning if none exist).
    argparser.add_argument(
        "--wq",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run the expensive w(q) lattice scan (default: on). Use --no-wq to "
        "skip it and reuse cached w(q) results instead.",
    )

    # Lattice-overview rendering is also slow (it tiles every lattice_final.npy),
    # so it is off unless explicitly requested.
    argparser.add_argument(
        "--vis",
        action="store_true",
        help="Render the lattice-overview grids for each run (slow; off by "
        "default).",
    )

    args = argparser.parse_args()

    # --verbose -> INFO logging; otherwise stay mostly silent (warnings + the
    # final summary only). This overrides the INFO-level basicConfig the package
    # sets at import time.
    logging.getLogger().setLevel(logging.INFO if args.verbose else logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    
    npa.print_verbose_startup()

    # define the parent directory to sweep over
    parent_dir = Path(args.parent_dir)
    if not parent_dir.is_dir():
        raise SystemExit(f"Parent directory {parent_dir} does not exist.")

    sub_folders_to_analyze = sorted(f for f in parent_dir.iterdir() if f.is_dir())

    # analyze each subdirectory using the analyzing_order_disorder pipeline
    results = []
    for sub in sub_folders_to_analyze:
        # --skip: if this run was already analyzed, reuse its results instead of
        # recomputing (and leave its lattice overview PNGs untouched).
        analysis_csv = sub / ANALYSIS_CSV
        if args.skip and analysis_csv.is_file():
            analyzed_at = datetime.fromtimestamp(analysis_csv.stat().st_mtime)
            print(
                f"Skipping {sub.name} (analyzed {analyzed_at:%Y-%m-%d %H:%M:%S})"
            )
            try:
                results.append(summarize_skipped(sub, compute_speed=args.speed))
            except Exception as e:
                logger.warning(
                    "Could not reuse existing results for %s: %s", sub.name, e
                )
            continue

        logger.info("=== Analyzing %s ===", sub.name)
        try:
            results.append(
                analyze_directory(
                    sub,
                    min_size=args.min_size,
                    run_wq=args.wq,
                    compute_speed=args.speed,
                )
            )
        except Exception as e:
            # A subfolder may not be a valid run directory (e.g. no out.csv),
            # or the sigmoid fit may fail; skip it and keep sweeping.
            logger.warning("Skipping %s: %s", sub.name, e)

        # plot the final-lattice overviews (slow) only when --vis is passed, so
        # the lattices can be eyeballed on demand without paying the cost every
        # sweep.
        if args.vis:
            try:
                plot_lattice_overviews(sub)
            except Exception as e:
                logger.warning("Could not plot lattice overviews for %s: %s", sub.name, e)

    if not results:
        raise SystemExit(f"No subdirectories under {parent_dir} could be analyzed.")

    # save a combined summary of every run to the parent directory
    summary = pd.DataFrame(results).sort_values(by="critical_supersat")
    summary.to_csv(parent_dir / "sweep_summary.csv", index=False)
    print("\n=== Sweep summary ===")
    print(summary)

    # bar chart of the critical supersaturation for every analyzed run, with the
    # sampling-resolution error bars (mean dphi spacing bracketing each fit).
    fig, ax = plt.subplots(figsize=(max(6, len(summary) * 0.6), 5))
    ax.bar(
        summary["directory"],
        summary["critical_supersat"],
        yerr=summary["critical_supersat_err"],
        capsize=4,
        color="tab:blue",
    )
    ax.set_ylabel(r"Critical supersaturation $\Delta\phi_c$")
    ax.set_xlabel("Run directory")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(parent_dir / "sweep_critical_supersat.png", dpi=300)
    plt.close(fig)

    # companion bar chart of the growth speed at the critical supersaturation,
    # mirroring the plot above (only when --speed populated those columns).
    if args.speed and "growth_speed_at_critical" in summary.columns:
        fig, ax = plt.subplots(figsize=(max(6, len(summary) * 0.6), 5))
        ax.bar(
            summary["directory"],
            summary["growth_speed_at_critical"],
            yerr=summary["dgrowth_speed_at_critical"],
            capsize=4,
            color="tab:green",
        )
        ax.set_ylabel(r"Growth speed at $\Delta\phi_c$  $\langle v \rangle$")
        ax.set_xlabel("Run directory")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()
        fig.savefig(parent_dir / "sweep_growth_speed.png", dpi=300)
        plt.close(fig)

    print(f"\nSaved sweep summary and plot to {parent_dir}")
