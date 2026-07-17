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


fig, axes = plt.subplots(3,3, figsize=(10,10))

cmap = ListedColormap(["#f2f2f2", "#f2f2f2", "#f2f2f2", "#e7685d", "#5652a3"])
cmap = ListedColormap(["#8c86ed", "#e7968f", "#f2f2f2", "#e7685d", "#5652a3"])

norm = plt.Normalize(vmin=-2, vmax=2)

for ax in axes.flatten():

    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)


# low_supersat = np.load('/Volumes/2025/80x320_EFF_3S_GROWTH/-6.95/2025-10-25-17:00_0/lattice_final.npy')
# lattice = low_supersat.copy()
# lattice[:, 50:] = 0
# lattice[:, 50:320] = np.random.choice([0,1,2],p=[0.99,0.005,0.005], size=lattice[:, 50:320].shape)
# axes[0,0].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
# axes[0,0].set_xlim(0,320)
# lattice = low_supersat.copy()
# lattice[:, 150:] = 0
# lattice[:, 150:320] = np.random.choice([0,1,2],p=[0.99,0.005,0.005], size=lattice[:, 150:320].shape)
# axes[1,0].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
# axes[1,0].set_xlim(0,320)
# lattice = low_supersat[:,0:320]
# axes[2,0].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
# axes[2,0].set_xlim(0,320)


# high_supersat = np.load('/Volumes/2025/80x320_EFF_3S_GROWTH/-6.45/2025-10-25-17:02_0/lattice_final.npy')
# lattice = high_supersat.copy()
# lattice[:, 90:] = 0
# lattice[:, 90:320] = np.random.choice([0,1,2],p=[0.98,0.01,0.01], size=lattice[:, 90:320].shape)

# axes[0,1].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
# axes[0,1].set_xlim(0,320)
# lattice = high_supersat.copy()
# lattice[:, 190:] = 0
# lattice[:, 190:320] = np.random.choice([0,1,2],p=[0.98,0.01,0.01], size=lattice[:, 190:320].shape)
# axes[1,1].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
# axes[1,1].set_xlim(0,320)
# lattice = high_supersat.copy()
# lattice[:, 320:] = 0
# axes[2,1].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
# axes[2,1].set_xlim(0,320)


for i, growth in enumerate([50, 150, 280]):
    lattice = np.load(f'/Users/moritzobenauer/Projects/nesspy_analysis/2025/PAPER_ADDIDITIONS/s1_low_supersat/2026-04-02-10:09_0/{growth}_snapshot.npy')
    axes[i,0].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
    axes[i,0].set_xlim(10,320)
    time = np.round(458598.710, 0)
print(f"{time:.2e}")

# elapsed time: 
for i, growth in enumerate([50, 150, 280]):
    lattice = np.load(f'/Users/moritzobenauer/Projects/nesspy_analysis/2025/PAPER_ADDIDITIONS/s1_high_supersat/2026-04-02-09:59_0/{growth}_snapshot.npy')
    axes[i,1].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
    axes[i,1].set_xlim(10,320)
    time = np.round(458598.710, 0)
print(f"{time:.2e}")

# elapsed time: 716488.800
for i, growth in enumerate([50, 150, 280]):
    lattice = np.load(f'/Users/moritzobenauer/Projects/nesspy_analysis/2025/PAPER_ADDIDITIONS/s6_driven/2026-04-02-10:05_0/{growth}_snapshot.npy')
    axes[i,2].imshow(lattice, cmap=cmap, norm=norm, interpolation="none")
    axes[i,2].set_xlim(10,320)
    time = np.round(716488.800, 0)
print(f"{time:.2e}")

plt.subplots_adjust(wspace=0.1, hspace=-0.9)


axes[0,0].text(-0.02, 1.75, 'A', transform=axes[0,0].transAxes, 
         fontsize=14, fontweight='bold', va='top', ha='right')

axes[0,1].text(-0.01, 1.75, 'B', transform=axes[0,1].transAxes, 
         fontsize=14, fontweight='bold', va='top', ha='right')

axes[0,2].text(-0.01, 1.75, 'C', transform=axes[0,2].transAxes, 
         fontsize=14, fontweight='bold', va='top', ha='right')

axes[0,0].set_title(r'Low Supersaturation $\beta \Delta \Phi$,' + '\n' + r'No Chemical Drive $\beta \Delta \mu$,' + '\n Leading to Ordered and Slow Growth', fontsize=FS, fontweight='bold')
axes[0,1].set_title(r'High Supersaturation $\beta \Delta \Phi$,' + '\n' + r'No Chemical Drive $\beta \Delta \mu$,' + '\n Leading to Disordered and Fast Growth', fontsize=FS, fontweight='bold')
axes[0,2].set_title(r'High Supersaturation $\beta \Delta \Phi$,' + '\n' + r'High Chemical Drive $\beta \Delta \mu$,' + '\n Leading to Ordered and Fast Growth', fontsize=FS, fontweight='bold')


axes[0,0].arrow(300, 10, 0, 50, head_width=5, head_length=5, fc='k', ec='k', lw=1.5)
axes[0,1].arrow(300, 10, 0, 50, head_width=5, head_length=5, fc='k', ec='k', lw=1.5)
axes[0,2].arrow(300, 10, 0, 50, head_width=5, head_length=5, fc='k', ec='k', lw=1.5)

axes[0,0].text(295, 35, 'Time', fontsize=8, rotation=90, va='center', ha='right')  
axes[0,1].text(295, 35, 'Time', fontsize=8, rotation=90, va='center', ha='right')  
axes[0,2].text(295, 35, 'Time', fontsize=8, rotation=90, va='center', ha='right')  


axes[2,0].arrow(10, 70, 50, 0, head_width=5, head_length=5, fc='w', ec='w', lw=1.5)
axes[2,1].arrow(10, 70, 50, 0, head_width=5, head_length=5, fc='w', ec='w', lw=1.5)
axes[2,2].arrow(10, 70, 50, 0, head_width=5, head_length=5, fc='w', ec='w', lw=1.5)
# Add a transparent box around the text
axes[2,0].text(
    15, 55, 'Growth', fontsize=8, va='center', ha='left', color='w',
    bbox=dict(facecolor='k', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2')
)


axes[2,1].text(15, 55, 'Growth', fontsize=8, va='center', ha='left', color='w', 
    bbox=dict(facecolor='k', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2')
)  
axes[2,2].text(15, 55, 'Growth', fontsize=8, va='center', ha='left', color='w', 
    bbox=dict(facecolor='k', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2')
)  


# axes[0,0].text(200, 30, r'$\beta \Delta \mu = 0.0$', fontsize=10, va='center', ha='right', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))  
# axes[0,0].text(200, 50, r'$\beta \Delta \Phi \approx 0.0$', fontsize=10, va='center', ha='right', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))  

# axes[0,1].text(220, 30, r'$\beta \Delta \mu = 0.0$', fontsize=10, va='center', ha='right', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))  
# axes[0,1].text(220, 50, r'$\beta \Delta \Phi \gg 0.0$', fontsize=10, va='center', ha='right', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))  

# axes[0,2].text(220, 30, r'$\beta \Delta \mu \gg 0.0$', fontsize=10, va='center', ha='right', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))  
# axes[0,2].text(220, 50, r'$\beta \Delta \Phi \gg 0.0$', fontsize=10, va='center', ha='right', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))  

plt.savefig('growth_images.pdf', bbox_inches='tight', dpi=300)


