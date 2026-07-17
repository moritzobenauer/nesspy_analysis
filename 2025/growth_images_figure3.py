import numpy as np
# import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from plot_defaults import *
set_plot_defaults()
whiteout()

from matplotlib.colors import ListedColormap


fig, axes = plt.subplots(2,2, figsize=(7.5,3), sharey=False, sharex=False)


cmap = ListedColormap(["#f2f2f2", "#f2f2f2", "#f2f2f2", "#e7685d", "#5652a3"])
cmap = ListedColormap(["#8c86ed", "#e7968f", "#f2f2f2", "#e7685d", "#5652a3"])

norm = plt.Normalize(vmin=-2, vmax=2)


   



fig, ax = plt.subplots(1,1, sharey=False, sharex=False)

ax.set_xticks([])
ax.set_yticks([])

for spine in ax.spines.values():
    spine.set_visible(False)

# 2.85 unordered

lattice = np.load('/Volumes/2025/2026_paper/ALTERING_COMPOSITION/2026_PROJ1 2/X_160_Y_40_6.0_D0.0_JHOM_-2.85_F0.2_K1.0/-5.5918/2026-03-14-22:38_0/lattice_final.npy')
ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="nearest")
# ax.set_xlim(0,160)
# ax.axvline(5, ls="dashed", color="white", lw=0.4)



plt.savefig('growth_images_figure3_unordered.pdf', dpi=400)


lattice = np.load('/Volumes/2025/2026_paper/RED_SEED/HRC_S6/-4.9961/2026-06-09-15:39_0/lattice_final.npy')
ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="nearest")
# ax.set_xlim(0,160)
# ax.axvline(5, ls="dashed", color="white", lw=0.4)


plt.savefig('growth_images_figure3_red_seed.pdf', dpi=400)


# # 2.85 ordered due to chemical drive

lattice = np.load("/Volumes/2025/2026_paper/ALTERING_COMPOSITION/2026_PROJ1 2/X_160_Y_40_6.0_D6.0_JHOM_-2.85_F0.2_K1.0/-4.9961/2026-03-14-22:50_2/lattice_final.npy")
ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="nearest")
# axes[1,0].set_xlim(0,320)
# axes[1,0].axvline(5, ls="dashed", color="white", lw=0.4)
plt.savefig('growth_images_figure3_blue_seed.pdf', dpi=400)

lattice = np.load('/Volumes/2025/2026_paper/2026_285_at_eq/-5.6/2026-06-09-17:32_1/lattice_final.npy')
ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="nearest")
# axes[1,0].set_xlim(0,320)
# axes[1,0].axvline(5, ls="dashed", color="white", lw=0.4)
plt.savefig('growth_images_figure3_at_eq.pdf', dpi=400)


# plt.subplots_adjust(wspace=-1.5, hspace=-1.2)

# plt.tight_layout()
# plt.savefig('growth_images_figure3.pdf', dpi=300)



lattice = np.load('/Volumes/2025/2026_paper/2026_285_at_eq_elongated/-5.6/2026-06-12-09_52_0/lattice_final.npy')
ax.imshow(lattice, cmap=cmap, norm=norm, interpolation="nearest")
# axes[1,0].set_xlim(0,320)
# axes[1,0].axvline(5, ls="dashed", color="white", lw=0.4)
plt.savefig('full_eq_for_fig3.pdf', dpi=400)