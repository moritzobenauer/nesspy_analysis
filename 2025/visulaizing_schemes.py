# visulaizing_schemes.py

import numpy as np
import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


from plot_defaults import *
set_plot_defaults()
whiteout()


def gaussian(x):
    return -0.8*np.exp(-(x-64)**2/360)+0.4

def tanh(x, x0=64):
    return 0.4*(np.tanh(-(x-x0)/10) )

from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

cmap = ListedColormap(["#8c86ed", "#e7968f", "#f2f2f2", "#e7685d", "#5652a3"])

colors = ["#e7685d","#e7685d", "#5652a3", "#5652a3"] 
cmap_red_to_blue = LinearSegmentedColormap.from_list("my_gradient", colors, N=256)

colors = ["#e7685d","#e7685d", "#f2f2f2", "#f2f2f2"] 
cmap_red_to_gray = LinearSegmentedColormap.from_list("my_gradient", colors, N=256)

colors = ["#e7685d","#e7685d","#5652a3", "#5652a3", "#f2f2f2","#f2f2f2"] 
cmap_red_to_gray_to_blue = LinearSegmentedColormap.from_list("my_gradient", colors, N=256)

colors = ["#e7685d","#e7685d","#e7685d", "#5652a3", "#e7685d", "#e7685d","#e7685d",] 
cmap_red_to_blue_to_red = LinearSegmentedColormap.from_list("my_gradient", colors, N=256)


colors = ["#f2f2f2","#f2f2f2", "#e7685d","#e7685d", "#5652a3","#5652a3", "#f2f2f2","#f2f2f2",] 
cmap_wrbw = LinearSegmentedColormap.from_list("my_gradient", colors, N=256)


green = "#539074"
orange = "#f39c12"
dark_gray = "#0e1319"

fig, axes = plt.subplots(1,6, figsize=(10,2.25), sharey=True)

axes[0].set_ylabel('Extent of \n Local Perturbation', fontsize=12)

fig.text(0.5, -0.05, r'Cross Section Along the Growth Direction $\rightarrow$', ha='center', fontsize=12)
# fig.text(0.5, 1.01, 'Spatial Dependence of Chemical Reaction Schemes', ha='center', fontsize=12)


fig.text(0.01, 1.0, 'D', 
         fontsize=16, fontweight='bold', va='top', ha='right')

gradient = np.linspace(-1, 1, 128).reshape(1, -1)
# axes[0].imshow(gradient, aspect='auto', cmap=cmap_red_to_gray_to_blue)

axes[0].axhline(0.4, color=dark_gray, linewidth=2)
axes[3].axhline(0.4, color=dark_gray, linewidth=2)
axes[4].axhline(0.4, color=dark_gray, linewidth=2)
axes[5].axhline(0.4, color=dark_gray, linewidth=2)


axes[0].axhline(0.35, color=orange, linewidth=2)
axes[1].axhline(0.35, color=orange, linewidth=2)
axes[2].axhline(0.35, color=orange, linewidth=2)


# axes[1].imshow(gradient, aspect='auto', cmap=cmap_red_to_gray)
# axes[3].imshow(gradient, aspect='auto', cmap=cmap_red_to_gray)

axes[0].imshow(gradient, aspect='auto', cmap=cmap_wrbw)
axes[1].imshow(gradient, aspect='auto', cmap=cmap_wrbw)
axes[2].imshow(gradient, aspect='auto', cmap=cmap_wrbw)
axes[3].imshow(gradient, aspect='auto', cmap=cmap_wrbw)
axes[4].imshow(gradient, aspect='auto', cmap=cmap_wrbw)


x = np.linspace(0, 64, 128)
axes[1].plot(x, -tanh(x, x0=20), color=dark_gray, linewidth=2)
print(tanh(0, x0=32))
x = np.linspace(64, 127, 128)
axes[1].plot(x, tanh(x, x0=104), color=dark_gray, linewidth=2)

print(gaussian(0))

x = np.linspace(0, 64, 128)
axes[3].plot(x, -tanh(x, x0=20)-0.05, color=orange, linewidth=2)
print(tanh(0, x0=32))
x = np.linspace(64, 127, 128)
axes[3].plot(x, tanh(x, x0=104)-0.05, color=orange, linewidth=2)

# axes[3].plot(x, tanh(x, x0=96)-0.05, color=orange, linewidth=2)

x = np.linspace(0, 127, 128)
axes[2].plot(x, gaussian(x), color=dark_gray, linewidth=2)
axes[4].plot(x, gaussian(x)-0.05, color=orange, linewidth=2)

# axes[2].imshow(gradient, aspect='auto', cmap=cmap_red_to_blue)
# axes[4].imshow(gradient, aspect='auto', cmap=cmap_red_to_blue)

axes[5].imshow(gradient, aspect='auto', cmap=cmap_red_to_blue_to_red)
axes[5].plot(x, gaussian(x)-0.05, color=orange, linewidth=2)
axes[5].plot(x, 0.2*gaussian(x)+0.26, color=orange, linewidth=1, ls='--')



axes[0].set_title(r'Scheme $\mathcal{S}1$', fontsize=12, fontweight='bold')
axes[1].set_title(r'Scheme $\mathcal{S}2$', fontsize=12, fontweight='bold')
axes[2].set_title(r'Scheme $\mathcal{S}3$', fontsize=12, fontweight='bold')
axes[3].set_title(r'Scheme $\mathcal{S}4$', fontsize=12, fontweight='bold')
axes[4].set_title(r'Scheme $\mathcal{S}5$', fontsize=12, fontweight='bold')
axes[5].set_title(r'Scheme $\mathcal{S}6$', fontsize=12, fontweight='bold')


for i in [2,4,5]:

    axes[i].spines['bottom'].set_edgecolor(green)
    axes[i].spines['top'].set_edgecolor(green)
    axes[i].spines['right'].set_edgecolor(green)
    axes[i].spines['left'].set_edgecolor(green)
    for spine in axes[i].spines.values():
        spine.set_linewidth(3)

for i in [0, 1,2,3,4]:
    axes[i].axvline(64, color=dark_gray, linestyle='--', linewidth=1)  

y=20
# axes[5].axvline(64-y, color=dark_gray, linestyle='dotted', linewidth=1)
# axes[5].axvline(64+y, color=dark_gray, linestyle='dotted', linewidth=1)

for i in [0,1,2,3,4]:

    axes[i].axvline(20, color=dark_gray, linestyle='dotted', linewidth=1)
    axes[i].axvline(104, color=dark_gray, linestyle='dotted', linewidth=1)

for ax in axes.flatten():

    ax.set_xticks([])
    ax.set_yticks([])


    legend_elements = [
        Patch(facecolor=dark_gray, label='Change in Chemical Reaction Base Rate $k$'),
        Patch(facecolor=orange, label=r'Change in Driving Strength $\beta \Delta \mu$'),
        Patch(facecolor=green, label='Composition-Altering Scheme')
    ]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False, fontsize=12)

fig.set_tight_layout(True)
plt.savefig('schemes.pdf', dpi=300, bbox_inches='tight')