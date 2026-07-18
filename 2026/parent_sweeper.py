# This is a sweeper over a parent-parent directory

import logging
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import nesspy_analysis as npa

from analyzing_order_disorder import analyze_directory

logger = logging.getLogger(__name__)

# Output file written by analyze_directory; its presence marks a run as already
# analyzed for the --skip flag.
ANALYSIS_CSV = "order_disorder_analysis.csv"


def _read_critical_supersat(run_dir: Path) -> float:
    """Read the critical supersaturation back from ``critical_supersat.txt``.

    The file (written by ``analyze_directory``) has a single line of the form
    ``critical_supersat (...): <value>``. Returns ``float('nan')`` if the file
    is missing or unparsable.
    """
    txt = run_dir / "critical_supersat.txt"
    try:
        line = txt.read_text().strip()
        return float(line.rsplit(":", 1)[1])
    except (OSError, ValueError, IndexError):
        logger.warning("Could not read critical supersaturation from %s", txt)
        return float("nan")


def summarize_skipped(run_dir: Path) -> dict:
    """Rebuild an ``analyze_directory``-shaped summary for an already-analyzed run.

    Re-parses the thermodynamic parameters from the run's out.csv headers (cheap;
    no ``get_wq()`` multiprocessing) and reads the previously computed critical
    supersaturation from ``critical_supersat.txt``, so a skipped run still appears
    as a full row in the final sweep summary.
    """
    analysis_object = npa.DynamicalOrderDisorder(run_dir.name, run_dir)
    thermos = analysis_object.get_thermos_from_file()
    return {
        "directory": run_dir.name,
        "jhom": thermos.jhom,
        "jhet": thermos.jhet,
        "fres": thermos.fres,
        "dmu": thermos.dmu,
        "k": thermos.k,
        "method": thermos.method,
        "critical_supersat": _read_critical_supersat(run_dir),
    }


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
                results.append(summarize_skipped(sub))
            except Exception as e:
                logger.warning(
                    "Could not reuse existing results for %s: %s", sub.name, e
                )
            continue

        logger.info("=== Analyzing %s ===", sub.name)
        try:
            results.append(analyze_directory(sub, min_size=args.min_size))
        except Exception as e:
            # A subfolder may not be a valid run directory (e.g. no out.csv),
            # or the sigmoid fit may fail; skip it and keep sweeping.
            logger.warning("Skipping %s: %s", sub.name, e)

        # plot the final-lattice overviews regardless of whether the
        # order-disorder analysis above succeeded, so the lattices can always
        # be eyeballed.
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

    # bar chart of the critical supersaturation for every analyzed run
    fig, ax = plt.subplots(figsize=(max(6, len(summary) * 0.6), 5))
    ax.bar(summary["directory"], summary["critical_supersat"], color="tab:blue")
    ax.set_ylabel(r"Critical supersaturation $\Delta\phi_c$")
    ax.set_xlabel("Run directory")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(parent_dir / "sweep_critical_supersat.png", dpi=300)
    plt.close(fig)

    print(f"\nSaved sweep summary and plot to {parent_dir}")
