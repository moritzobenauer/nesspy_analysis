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
        