import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import nesspy_analysis as npa

logger = logging.getLogger(__name__)

# Output files written by the full (w(q)) pipeline. Their presence is what the
# --no-wq / --skip paths reuse instead of recomputing the expensive w(q) scan.
ANALYSIS_CSV = "order_disorder_analysis.csv"
CRITICAL_SUPERSAT_TXT = "critical_supersat.txt"


def read_critical_supersat(run_dir: Path) -> tuple[float, float]:
    """Read the critical supersaturation (+ error) from ``critical_supersat.txt``.

    The file (written by :func:`analyze_directory`) has two lines of the form
    ``critical_supersat (...): <value>`` and
    ``critical_supersat_error (...): <error>``. Returns ``(value, error)``, with
    ``float('nan')`` for either field that is missing or unparsable (older files
    written before the error was added have no second line, so their error comes
    back as NaN).

    Kept here as the single source of truth so both this module and
    ``parent_sweeper.py`` (the --skip path) read the cache the same way.
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
    """Growth speed (+ error) at the critical supersaturation.

    Picks the sampled data point whose corrected logarithmic supersaturation
    ``dphi`` is closest to ``critical_supersat`` and returns its
    ``(growth_speed, dgrowth_speed)``. We deliberately return the *nearest raw
    data point* rather than interpolating: it maps directly onto the per-mu
    ``growth_speed`` computed in ``read_csv.py`` and keeps the reported value
    transparent. If ``critical_supersat`` lies outside the sampled ``dphi``
    range the nearest endpoint is used.

    Returns ``(nan, nan)`` when there is nothing usable to select from (no rows,
    a NaN critical value, or the required columns are missing).
    """
    required = {"dphi", "growth_speed", "dgrowth_speed"}
    if data is None or not required.issubset(data.columns) or np.isnan(critical_supersat):
        return float("nan"), float("nan")

    usable = data.dropna(subset=["dphi", "growth_speed"])
    if usable.empty:
        return float("nan"), float("nan")

    # Row minimizing |dphi - critical_supersat|.
    idx = (usable["dphi"] - critical_supersat).abs().idxmin()
    row = usable.loc[idx]
    return float(row["growth_speed"]), float(row["dgrowth_speed"])

# Shared figure styling. plot_defaults.py sits next to this script (duplicated
# from the repo root, as in 2025/); fall back silently to matplotlib defaults if
# it is not importable.
try:
    from plot_defaults import set_plot_defaults
    set_plot_defaults()
except ImportError:
    logger.warning("plot_defaults not found; using matplotlib defaults.")

data_path = Path("/Volumes/2025/RETHINKING_SUPERSAT/X_320_Y_80_1.0_D0.0_JHOM_-3.9_F0.0_K1.0")


def _speed_from_cache(data_path: Path, data: pd.DataFrame) -> tuple[float, float]:
    """Growth speed at the critical supersaturation, reusing cached w(q) output.

    Used by the --no-wq path: instead of rerunning the expensive w(q) scan, this
    reads the previously written ``critical_supersat.txt`` (for the critical
    value) and ``order_disorder_analysis.csv`` (for the per-mu ``dphi`` mapping),
    attaches that cached ``dphi`` onto the *freshly* computed per-mu growth
    speeds in ``data`` by a nearest-mu join, and reports the growth speed at the
    critical supersaturation via :func:`growth_speed_at_critical`.

    Returns ``(nan, nan)`` and logs a warning if the cache is unavailable, so the
    caller can leave the growth-speed columns empty and tell the user to run
    w(q) first.
    """
    critical_supersat, _ = read_critical_supersat(data_path)
    cached_csv = data_path / ANALYSIS_CSV
    if np.isnan(critical_supersat) or not cached_csv.is_file():
        logger.warning(
            "w(q) not available for %s; run without --no-wq first to report the "
            "growth speed at the critical supersaturation.",
            data_path.name,
        )
        return float("nan"), float("nan")

    cached = pd.read_csv(cached_csv)
    if "dphi" not in cached.columns or "mu" not in cached.columns:
        logger.warning(
            "Cached %s for %s has no dphi/mu columns; run without --no-wq first.",
            ANALYSIS_CSV, data_path.name,
        )
        return float("nan"), float("nan")

    # Attach the cached dphi(mu) mapping onto the fresh per-mu growth speeds by a
    # nearest-mu join, so we select the growth speed at the mu whose dphi is
    # closest to the critical supersaturation.
    merged = pd.merge_asof(
        data.sort_values(by="mu"),
        cached[["mu", "dphi"]].dropna(subset=["dphi"]).sort_values(by="mu"),
        on="mu",
        direction="nearest",
    )
    return growth_speed_at_critical(merged, critical_supersat)


def analyze_directory(
    data_path: Path,
    min_size: int = 8,
    run_wq: bool = True,
    compute_speed: bool = False,
) -> dict:
    """Run the order-disorder pipeline on a single run directory.

    Auto-detects the supersaturation parameters and, when ``run_wq`` is True
    (the default), computes w(q) and the corrected logarithmic supersaturation,
    fits the sigmoid to find the critical value, and writes the CSV / text /
    plot outputs into ``data_path``.

    ``run_wq=False`` skips the expensive w(q) / cluster-observable multiprocessing
    scans entirely and leaves the cached w(q) outputs untouched; the critical
    supersaturation is then read back from those caches rather than recomputed.

    ``compute_speed=True`` adds ``growth_speed_at_critical`` /
    ``dgrowth_speed_at_critical`` to the returned summary dict: the interface
    growth speed at the critical supersaturation.

    Returns a summary dict with the detected parameters and the critical
    supersaturation (plus growth speed when requested).
    """
    data_path = Path(data_path)

    # get_wq() uses a multiprocessing Pool, so callers must sit behind a
    # __main__ guard. get_data() (per-mu growth speed) is cheap and always runs.
    analysis_object = npa.DynamicalOrderDisorder(data_path.name, data_path)
    data = analysis_object.get_data().sort_values(by='mu')

    # auto-detect the supersaturation parameters from the output files
    thermos = analysis_object.get_thermos_from_file()
    logger.info("%s", thermos)

    summary = {
        "directory": data_path.name,
        "jhom": thermos.jhom,
        "jhet": thermos.jhet,
        "fres": thermos.fres,
        "dmu": thermos.dmu,
        "k": thermos.k,
        "method": thermos.method,
        "critical_supersat": float("nan"),
        "critical_supersat_err": float("nan"),
    }
    if compute_speed:
        summary["growth_speed_at_critical"] = float("nan")
        summary["dgrowth_speed_at_critical"] = float("nan")

    # --no-wq: reuse the cached w(q) results rather than recomputing them.
    if not run_wq:
        critical_supersat, critical_supersat_err = read_critical_supersat(data_path)
        summary["critical_supersat"] = critical_supersat
        summary["critical_supersat_err"] = critical_supersat_err
        if np.isnan(critical_supersat):
            logger.warning(
                "w(q) not available for %s; run without --no-wq first to obtain "
                "the critical supersaturation.", data_path.name,
            )
        if compute_speed:
            gs, dgs = _speed_from_cache(data_path, data)
            summary["growth_speed_at_critical"] = gs
            summary["dgrowth_speed_at_critical"] = dgs
        return summary

    # now calculate wq and the new supersaturation with the parameters
    analysis_object.get_wq()
    data = analysis_object.get_logarithmic_supersat_corrected(thermos)

    # per-mu wrong-bond fraction <q> and normalized blue cluster size <r>, so the
    # m=0 regime can be split into truly-mixed (high q, small r) vs
    # flopping-domain (lower q, large r) states.
    data = analysis_object.get_cluster_observables(min_size=min_size)
    data = data.sort_values(by='mu')
    logger.info("\n%s", data)

    data['susceptibility'] = data['m2'] - data['m']**2

    # fit m vs log(S) to a sigmoid and find the inflection point (+ its
    # sampling-resolution error, i.e. the mean dphi spacing bracketing it).
    critical_supersat, critical_supersat_err = analysis_object.get_critical_supersat()
    summary["critical_supersat"] = critical_supersat
    summary["critical_supersat_err"] = critical_supersat_err
    logger.info(
        "Critical supersaturation (inflection point): %.6f +- %.6f",
        critical_supersat, critical_supersat_err,
    )

    # growth speed at the critical supersaturation (from the live per-mu data,
    # which already carries growth_speed / dgrowth_speed and dphi).
    if compute_speed:
        gs, dgs = growth_speed_at_critical(data, critical_supersat)
        summary["growth_speed_at_critical"] = gs
        summary["dgrowth_speed_at_critical"] = dgs

    # save all the calculated results to the base path
    data.to_csv(data_path / ANALYSIS_CSV, index=False)

    # write the critical supersaturation (+ error) to a text file in the parent
    # directory. Two clearly-labelled lines so parent_sweeper can read both back.
    with open(data_path / CRITICAL_SUPERSAT_TXT, "w") as fh:
        fh.write(f"critical_supersat (inflection point of m vs log(S)): {critical_supersat}\n")
        fh.write(f"critical_supersat_error (mean dphi spacing bracketing the inflection point): {critical_supersat_err}\n")

    # save an order parameter versus logarithmic supersaturation plot
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].errorbar(
        data['dphi'],
        data['m'],
        yerr=data['dm'],
        fmt='o',
        capsize=5,
        label=r'Exact $w(q)$ method',
    )

    # overlay the sigmoidal fit
    dphi_fit = np.linspace(data['dphi'].min(), data['dphi'].max(), 400)
    ax[0].plot(dphi_fit, npa.sigmoid(dphi_fit, *analysis_object.sigmoid_params),
               color='k', lw=2, label='Sigmoidal fit')

    # indicate the critical supersaturation (inflection point) with its error
    # band (mean dphi spacing to the bracketing data points).
    ax[0].axvline(
        critical_supersat,
        color='tab:red',
        linestyle='--',
        label=rf'$\Delta\phi_c = {critical_supersat:.3f} \pm {critical_supersat_err:.3f}$',
    )
    ax[0].axvspan(
        critical_supersat - critical_supersat_err,
        critical_supersat + critical_supersat_err,
        color='tab:red', alpha=0.15,
    )

    ax[0].set_xlabel(r'Logarithmic supersaturation $\Delta\phi = \log S$')
    ax[0].set_ylabel(r'Absolute Order parameter $|m|$')
    ax[0].legend()

    ax[1].errorbar(
        data['dphi'],
        data['susceptibility'],
        fmt='o',
        capsize=5,
        label=r'Exact $w(q)$ method',
    )

    ax[1].axvline(
        critical_supersat,
        color='tab:red',
        linestyle='--',
        label=rf'$\Delta\phi_c = {critical_supersat:.3f} \pm {critical_supersat_err:.3f}$',
    )
    ax[1].axvspan(
        critical_supersat - critical_supersat_err,
        critical_supersat + critical_supersat_err,
        color='tab:red', alpha=0.15,
    )

    ax[1].set_xlabel(r'Logarithmic supersaturation $\Delta\phi = \log S$')
    ax[1].set_ylabel(r'Susceptibility $\chi$')
    ax[1].legend()

    fig.tight_layout()
    fig.savefig(data_path / "order_parameter_vs_supersat.png", dpi=300)
    plt.close(fig)

    # combined q(log S) / r(log S) figure
    fig, _ = npa.plot_cluster_observables(
        data, critical_supersat=critical_supersat, min_size=min_size
    )
    fig.savefig(data_path / "cluster_observables_vs_supersat.png", dpi=300)
    plt.close(fig)
    logger.info("Saved results and plots to %s", data_path)

    return summary


if __name__ == "__main__":

    npa.print_verbose_startup()

    analyze_directory(data_path)
