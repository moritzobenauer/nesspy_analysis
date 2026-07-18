from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def plot_lattice_clean(lattice: np.array):
    cmap = ListedColormap(["#f2f2f2", "#f2f2f2", "#f2f2f2", "#e7685d", "#5652a3"])
    bounds = [-2, -1, 0, 1, 2, 3]
    norm = plt.Normalize(vmin=-2, vmax=2)
    y, x = lattice.shape
    fig, ax = plt.subplots()
    ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="none")

    ax.set_xlim(0, x - 1)
    ax.set_ylim(0, y - 1)

    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.set_facecolor('white')
    fig.patch.set_alpha(0.0)

    return (fig,ax)


def calculate_order_parameter(lattice: np.array, method: str, lb_trr: float = 0.5, ub_trr: float = 0.8) -> tuple:

    # This comes directly from `nesspy`!

    if method == 'MLO2024':

        LB = int(lattice.shape[1] * lb_trr)
        UB = int(lattice.shape[1] * ub_trr)
        sliced_array = lattice[:, LB:UB]
        counts, counts_blue, counts_red = 1, 0, 0
        for value in np.nditer(sliced_array):
            if value == 2 or value == -2:
                counts_blue += 1
                counts += 1
            elif value == 1 or value == -1:
                counts_red += 1
                counts += 1
            else:
                pass
            m = np.abs((counts_blue - counts_red)/counts)
        return m, m**2

def calculate_average_cluster_size(lattice: np.array, lb_trr: float = 0.3, ub_trr: float = 0.8,
                                   min_size: int=8) -> float:
    from scipy.ndimage import label
    LB = int(lattice.shape[1] * lb_trr)
    UB = int(lattice.shape[1] * ub_trr)
    sliced_array = lattice[:, LB:UB]
    cluster_sizes = []
    
    for val in [2]:
        mask = (sliced_array == val)

        # 4-connectivity structure
        structure = np.array([[0,1,0],
                              [1,1,1],
                              [0,1,0]])

        labeled, num = label(mask, structure)

        # record sizes
        for idx in range(1, num + 1):
            size = np.sum(labeled == idx)
            if size >= min_size:
                cluster_sizes.append(size)
    
    if len(cluster_sizes) == 0:
        return 0, 0  # no clusters
    
    num_clusters = len(cluster_sizes)
    avg_size = np.mean(cluster_sizes)
    
    return num_clusters, 2*avg_size

    

def _plot_observable_vs_logS(data, ycol, yerrcol, ylabel, ax=None,
                             color="#333333", label=None, **kwargs):
    """Shared errorbar plot of a per-mu observable against log(S) = dphi.

    ``data`` is a DataFrame carrying ``dphi`` plus the requested ``ycol``/
    ``yerrcol`` columns (produced by
    DynamicalOrderDisorder.get_logarithmic_supersat_corrected() and
    .get_cluster_observables()). Rows missing dphi or the observable are dropped.
    Returns ``(fig, ax)``.
    """
    _df = data.dropna(subset=["dphi", ycol]).sort_values(by="dphi")
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure
    ax.errorbar(
        _df["dphi"], _df[ycol],
        yerr=_df[yerrcol] if yerrcol in _df.columns else None,
        fmt="o-", color=color, label=label, capsize=3, **kwargs,
    )
    ax.set_xlabel(r"$\log(S)$")
    ax.set_ylabel(ylabel)
    if label is not None:
        ax.legend()
    return (fig, ax)


def plot_q_vs_logS(data, ax=None, color="#ce3627", label=None, **kwargs):
    """Wrong-bond fraction q against corrected log-supersaturation log(S).

    Expects ``dphi``, ``q_mean`` and ``q_sem`` columns (see
    DynamicalOrderDisorder.get_cluster_observables()). Returns ``(fig, ax)``.
    """
    return _plot_observable_vs_logS(
        data, "q_mean", "q_sem", r"$q$ (wrong-bond fraction)",
        ax=ax, color=color, label=label, **kwargs,
    )


def plot_r_vs_logS(data, ax=None, color="#5652a3", label=None, **kwargs):
    """Normalized blue cluster size r against corrected log-supersaturation.

    Expects ``dphi``, ``r_mean`` and ``r_sem`` columns (see
    DynamicalOrderDisorder.get_cluster_observables()). Returns ``(fig, ax)``.
    """
    return _plot_observable_vs_logS(
        data, "r_mean", "r_sem", r"$r$ (norm. cluster size)",
        ax=ax, color=color, label=label, **kwargs,
    )


def plot_cluster_observables(data, critical_supersat=None, min_size=None):
    """Two-panel q(log S) / r(log S) figure disambiguating the m=0 regime.

    Left panel: wrong-bond fraction ``q``; right panel: normalized blue cluster
    size ``r`` -- both against log(S) = ``dphi`` with SEM error bars. Expects the
    columns added by DynamicalOrderDisorder.get_logarithmic_supersat_corrected()
    and .get_cluster_observables(). If ``critical_supersat`` is given, a dashed
    marker is drawn on both panels; ``min_size`` (if given) is noted in the r
    panel title. Styling follows whatever rcParams are active (e.g. after
    ``set_plot_defaults()``). Returns ``(fig, axes)``.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    plot_q_vs_logS(data, ax=axes[0])
    plot_r_vs_logS(data, ax=axes[1])

    if critical_supersat is not None:
        for ax in axes:
            ax.axvline(
                critical_supersat, color="tab:red", linestyle="--",
                label=rf"$\Delta\phi_c = {critical_supersat:.3f}$",
            )
            ax.legend()

    if min_size is not None:
        axes[1].set_title(rf"blue clusters, $|C| \geq {min_size}$")

    fig.tight_layout()
    return (fig, axes)


def plot_all_configurations(files: list[Path]) -> tuple[plt.Figure, np.array]:
    N = len(files)
    cols = int(np.ceil(np.sqrt(N)))
    rows = int(np.ceil(N / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    axes = np.array(axes).reshape(-1)  # Flatten in case of single row/column

    for i, file in enumerate(files):
        lattice = np.load(file)  # Assuming the files are .npy files
        ax = axes[i]
        cmap = ListedColormap(["#f2f2f2", "#f2f2f2", "#f2f2f2", "#e7685d", "#5652a3"])
        norm = plt.Normalize(vmin=-2, vmax=2)
        ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
        ax.set_xticks([])
        ax.set_yticks([])

        oparam = np.round(calculate_order_parameter(lattice, method="MLO2024"),4)
        oparam_full = np.round(calculate_order_parameter(lattice, method="MLO2024", lb_trr=0.3, ub_trr=0.8),4)

        q = np.round(calculate_average_cluster_size(lattice, lb_trr=0.3, ub_trr=0.8, min_size=4),4)
        normalized_q = np.round(q[1]/ (lattice.shape[0] * lattice.shape[1]),2)

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(rf"$q={normalized_q}, m_f={oparam_full[0]}$", fontsize=12)

    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    fig.tight_layout()

    return (fig, axes)
        