import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import nesspy_analysis as npa

logger = logging.getLogger(__name__)

# Shared figure styling. plot_defaults.py sits next to this script (duplicated
# from the repo root, as in 2025/); fall back silently to matplotlib defaults if
# it is not importable.
try:
    from plot_defaults import set_plot_defaults
    set_plot_defaults()
except ImportError:
    logger.warning("plot_defaults not found; using matplotlib defaults.")

data_path = Path("/Volumes/2025/RETHINKING_SUPERSAT/X_320_Y_80_1.0_D0.0_JHOM_-4.00_F0.0_K1.0")


def analyze_directory(data_path: Path, min_size: int = 8) -> dict:
    """Run the full order-disorder pipeline on a single run directory.

    Auto-detects the supersaturation parameters, computes w(q) and the corrected
    logarithmic supersaturation, fits the sigmoid to find the critical value, and
    writes the CSV / text / plot outputs into ``data_path``.

    Returns a summary dict with the detected parameters and the critical
    supersaturation.
    """
    data_path = Path(data_path)

    # get_wq() uses a multiprocessing Pool, so callers must sit behind a
    # __main__ guard.
    analysis_object = npa.DynamicalOrderDisorder(data_path.name, data_path)
    data = analysis_object.get_data().sort_values(by='mu')

    # auto-detect the supersaturation parameters from the output files
    thermos = analysis_object.get_thermos_from_file()
    logger.info("%s", thermos)

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

    # fit m vs log(S) to a sigmoid and find the inflection point
    critical_supersat = analysis_object.get_critical_supersat()
    logger.info("Critical supersaturation (inflection point): %.6f", critical_supersat)

    # save all the calculated results to the base path
    data.to_csv(data_path / "order_disorder_analysis.csv", index=False)

    # write the critical supersaturation to a text file in the parent directory
    with open(data_path / "critical_supersat.txt", "w") as fh:
        fh.write(f"critical_supersat (inflection point of m vs log(S)): {critical_supersat}\n")

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

    # indicate the critical supersaturation (inflection point)
    ax[0].axvline(
        critical_supersat,
        color='tab:red',
        linestyle='--',
        label=rf'$\Delta\phi_c = {critical_supersat:.3f}$',
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
        label=rf'$\Delta\phi_c = {critical_supersat:.3f}$',
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

    return {
        "directory": data_path.name,
        "jhom": thermos.jhom,
        "jhet": thermos.jhet,
        "fres": thermos.fres,
        "dmu": thermos.dmu,
        "k": thermos.k,
        "method": thermos.method,
        "critical_supersat": critical_supersat,
    }


if __name__ == "__main__":

    npa.print_verbose_startup()

    analyze_directory(data_path)
