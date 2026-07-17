# This is a sweeper over a parent-parent directory

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import nesspy_analysis as npa

from analyzing_order_disorder import analyze_directory

logger = logging.getLogger(__name__)


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
        logger.info("=== Analyzing %s ===", sub.name)
        try:
            results.append(analyze_directory(sub))
        except Exception as e:
            # A subfolder may not be a valid run directory (e.g. no out.csv),
            # or the sigmoid fit may fail; skip it and keep sweeping.
            logger.warning("Skipping %s: %s", sub.name, e)

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
