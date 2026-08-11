"""Read-only status checks for a run directory's cached analysis pipeline output.

Everything here mirrors the file-existence/freshness rules `database/analyze_new.sh`
already uses to decide what's outstanding -- the UI must agree with the pipeline
about what "analyzed" means, not invent its own definition.

`ANALYSIS_CSV`/`CRITICAL_SUPERSAT_TXT`/`read_critical_supersat()`/
`growth_speed_at_critical()` are duplicated (not imported) from
`2026/analyzing_order_disorder.py`: that module lives in a dated scratch directory
with no `__init__.py` and isn't meant to be imported from, and the amount of logic
needed here is small and stable. Keep the two in sync by hand if that file's output
format ever changes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Output files written by 2026/analyzing_order_disorder.py::analyze_directory().
ANALYSIS_CSV = "order_disorder_analysis.csv"
CRITICAL_SUPERSAT_TXT = "critical_supersat.txt"
LATTICE_OVERVIEW_PNG = "lattice_overview.png"

# Written by database/analyze_new.sh (FAILED_FILE in database/config.sh) when a
# run's analysis raises; its presence stops the pipeline from retrying every cycle.
FAILED_FILE = "analysis_failed.md"


def read_critical_supersat(run_dir: Path) -> tuple[float, float]:
    """Read the critical supersaturation (+ error) from ``critical_supersat.txt``.

    Duplicated from 2026/analyzing_order_disorder.py::read_critical_supersat --
    keep in sync if that changes. Returns ``(nan, nan)`` for either field that is
    missing or unparsable.
    """
    txt = run_dir / CRITICAL_SUPERSAT_TXT

    def _parse(line: str) -> float:
        try:
            return float(line.rsplit(":", 1)[1])
        except (ValueError, IndexError):
            return float("nan")

    try:
        lines = txt.read_text().strip().splitlines()
    except OSError:
        logger.warning("Could not read critical supersaturation from %s", txt)
        return float("nan"), float("nan")

    value = _parse(lines[0]) if len(lines) >= 1 else float("nan")
    error = _parse(lines[1]) if len(lines) >= 2 else float("nan")
    return value, error


def growth_speed_at_critical(
    data: pd.DataFrame, critical_supersat: float
) -> tuple[float, float]:
    """Growth speed (+ error) at the sampled point nearest the critical supersaturation.

    Duplicated from 2026/analyzing_order_disorder.py::growth_speed_at_critical --
    keep in sync if that changes.
    """
    required = {"dphi", "growth_speed", "dgrowth_speed"}
    if data is None or not required.issubset(data.columns) or np.isnan(critical_supersat):
        return float("nan"), float("nan")

    usable = data.dropna(subset=["dphi", "growth_speed"])
    if usable.empty:
        return float("nan"), float("nan")

    idx = (usable["dphi"] - critical_supersat).abs().idxmin()
    row = usable.loc[idx]
    return float(row["growth_speed"]), float(row["dgrowth_speed"])


@dataclass
class RunStatus:
    """Structured status of one run directory's cached analysis, read from disk."""

    run_dir: Path
    looks_like_run_dir: bool
    has_analysis_csv: bool
    analysis_stale: bool
    has_lattice_overview: bool
    has_failed_marker: bool
    failed_marker_stale: bool
    critical_supersat: float | None
    critical_supersat_err: float | None


def _any_out_csv_newer_than(run_dir: Path, reference_mtime: float) -> bool:
    return any(
        f.stat().st_mtime > reference_mtime for f in run_dir.rglob("out.csv")
    )


def compute_run_status(run_dir: Path) -> RunStatus:
    """Compute a run directory's analysis status, replicating database/analyze_new.sh.

    A run "needs analysis" if ``order_disorder_analysis.csv`` is missing, or any
    ``out.csv`` under it is newer than that CSV. "Needs vis" is simply whether the
    run-root ``lattice_overview.png`` exists (per-mu overview PNGs are not checked,
    matching the pipeline's own gate).
    """
    # Cheap one-level-down check: does any immediate subdirectory hold an out.csv?
    # This is a badge/hint, not full validation -- it does not use rglob.
    looks_like_run_dir = False
    if run_dir.is_dir():
        for child in run_dir.iterdir():
            if child.is_dir() and (child / "out.csv").is_file():
                looks_like_run_dir = True
                break

    analysis_csv = run_dir / ANALYSIS_CSV
    has_analysis_csv = analysis_csv.is_file()
    analysis_stale = (
        _any_out_csv_newer_than(run_dir, analysis_csv.stat().st_mtime)
        if has_analysis_csv
        else False
    )

    has_lattice_overview = (run_dir / LATTICE_OVERVIEW_PNG).is_file()

    failed_marker = run_dir / FAILED_FILE
    has_failed_marker = failed_marker.is_file()
    failed_marker_stale = (
        _any_out_csv_newer_than(run_dir, failed_marker.stat().st_mtime)
        if has_failed_marker
        else False
    )

    critical_supersat: float | None = None
    critical_supersat_err: float | None = None
    if has_analysis_csv:
        critical_supersat, critical_supersat_err = read_critical_supersat(run_dir)

    return RunStatus(
        run_dir=run_dir,
        looks_like_run_dir=looks_like_run_dir,
        has_analysis_csv=has_analysis_csv,
        analysis_stale=analysis_stale,
        has_lattice_overview=has_lattice_overview,
        has_failed_marker=has_failed_marker,
        failed_marker_stale=failed_marker_stale,
        critical_supersat=critical_supersat,
        critical_supersat_err=critical_supersat_err,
    )


def is_analyzed(status: RunStatus) -> bool:
    """Whether this run's cached analysis is present and up to date."""
    return status.has_analysis_csv and not status.analysis_stale
