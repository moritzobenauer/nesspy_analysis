"""Load one analyzed run directory's cached pipeline output for display.

Ported from `2026/compare_order_disorder_runs.py` (`AnalyzedRun`, `load_run`,
`summarize`) -- that script's matplotlib figure-drawing is replaced by
`webapp/plots_interactive.py`, but the data-loading logic here is the same.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import nesspy_analysis as npa

from webapp.pipeline_status import ANALYSIS_CSV, read_critical_supersat


@dataclass
class AnalyzedRun:
    """One analyzed run directory, loaded from its cached pipeline output."""

    label: str
    path: Path
    data: pd.DataFrame
    critical: float
    critical_err: float
    scheme: str
    thermos: npa.Thermos
    color: str

    @property
    def sigmoid_params(self) -> np.ndarray:
        """Refit the logistic to the cached (dphi, m) pairs.

        The pipeline caches only the resulting critical point, not the fit
        parameters, so the curve is refit here from the same points with the
        same estimator (:func:`nesspy_analysis.fit_sigmoid`).
        """
        usable = self.data.dropna(subset=["dphi", "m"])
        return npa.fit_sigmoid(usable["dphi"].values, usable["m"].values)


def load_run(path: Path, label: str, color: str) -> AnalyzedRun:
    """Load one analyzed run directory from its cached pipeline output.

    Raises ``FileNotFoundError`` when the directory has not been through
    ``analyze_directory()`` yet -- this is the hard "not analyzed" gate for
    Tabs 2/3, enforced here in addition to Tab 1's load-time check.
    """
    path = Path(path)
    csv = path / ANALYSIS_CSV
    if not csv.is_file():
        raise FileNotFoundError(
            f"{csv} not found. Run 2026/analyzing_order_disorder.py "
            f"(or database/run_pipeline.sh) on {path} first."
        )

    data = pd.read_csv(csv).sort_values(by="dphi")

    # Older cached CSVs may not carry a 'susceptibility' column; recompute it as
    # a fallback so both old and new caches work with the same plotting code.
    if "susceptibility" not in data.columns:
        data["susceptibility"] = data["m2"] - data["m"] ** 2

    critical, critical_err = read_critical_supersat(path)

    # Read the scheme back from the raw out.csv headers rather than trusting a
    # cached column: this is the same version-aware resolution the pipeline
    # itself uses, so a legacy run is remapped onto its S-name here too.
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


def summarize(runs: list[AnalyzedRun]) -> pd.DataFrame:
    """One row per run with the parameters and the critical supersaturation."""
    from webapp.pipeline_status import growth_speed_at_critical

    records = []
    for run in runs:
        speed, dspeed = growth_speed_at_critical(run.data, run.critical)
        records.append(
            {
                "label": run.label,
                # Carried into the table so the Compare tab can paint a swatch
                # tying each row to its curve in the figure.
                "color": run.color,
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
