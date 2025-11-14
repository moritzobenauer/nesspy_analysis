from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import numpy as np

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