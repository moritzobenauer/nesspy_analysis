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


def plot_lattice_overviews(run_dir: Path) -> None:
    """Render overview grids of the final lattices for a single run directory.

    Produces two kinds of figure:

    - ``lattice_overview.png`` inside every mu subfolder, tiling that folder's
      ``lattice_final.npy`` file(s) (there may be several replicate seeds).
    - ``lattice_overview.png`` inside ``run_dir`` itself, tiling every final
      lattice found anywhere under the run.

    Failures for an individual mu folder are logged and skipped so one bad
    folder doesn't abort the whole run.
    """
    # per-mu-folder grids: each immediate subdirectory that holds one or more
    # lattice_final.npy (possibly nested under replicate-seed subfolders).
    for mu_folder in sorted(f for f in run_dir.iterdir() if f.is_dir()):
        try:
            files = sorted(npa.find_all_final_configs(mu_folder))
        except ValueError:
            # no lattice_final.npy under this subfolder; not a mu run folder.
            continue
        try:
            fig, _ = npa.plot_all_configurations(files)
            fig.savefig(mu_folder / "lattice_overview.png", dpi=200)
            plt.close(fig)
            logger.info("Saved %d-lattice overview to %s", len(files), mu_folder)
        except Exception as e:
            logger.warning("Could not plot lattices for %s: %s", mu_folder, e)

    # combined grid over every final lattice in the run
    try:
        all_files = sorted(npa.find_all_final_configs(run_dir))
    except ValueError:
        logger.warning("No lattice_final.npy files found under %s", run_dir)
        return
    try:
        fig, _ = npa.plot_all_configurations(all_files)
        fig.savefig(run_dir / "lattice_overview.png", dpi=200)
        plt.close(fig)
        logger.info(
            "Saved combined %d-lattice overview to %s", len(all_files), run_dir
        )
    except Exception as e:
        logger.warning("Could not plot combined lattice overview for %s: %s", run_dir, e)


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
