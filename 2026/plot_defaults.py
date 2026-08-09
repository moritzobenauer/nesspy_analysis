# plot_defaults.py
# MLO 2024-2025
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

# Font size definitions

FS = 15
FS_LEGEND = 18
FS_TITLE = 22


# Color definitions


RED="#ce3627"
BLUE="#7894a2"
ORANGE="#f68d3d"
PURPLE="#A36565"


BLUES = sns.color_palette(palette='Blues_d')
REDS = sns.color_palette(palette='Reds_d')
GREENS = sns.color_palette(palette='Greens_d')

def set_plot_defaults():
    mpl.rcParams.update(
        {
            "figure.figsize": (8, 6),
            "axes.titlesize": FS_TITLE,
            "axes.labelsize": FS_LEGEND,
            "xtick.labelsize": FS_LEGEND,
            "ytick.labelsize": FS_LEGEND,
            "legend.fontsize": FS_LEGEND,
            "grid.linestyle": "none",
            "grid.color": "gray",
            "figure.dpi": 300,
            "axes.grid": False,
            "font.family": "sans-serif",
            "font.sans-serif": "Helvetica",
            "font.size": FS,
            "mathtext.fontset": "cm",
        }
    )

    # Set tick marks to be inside and on all axes
    mpl.rcParams["xtick.direction"] = "in"
    mpl.rcParams["ytick.direction"] = "in"
    mpl.rcParams["xtick.top"] = True
    mpl.rcParams["xtick.bottom"] = True
    mpl.rcParams["ytick.left"] = True
    mpl.rcParams["ytick.right"] = True
    # print("Plot defaults set.")


def blackout():
    mpl.rcParams.update(
        {
            "figure.facecolor": "black",
            "axes.facecolor": "black",
            "axes.edgecolor": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "text.color": "white",
            "figure.edgecolor": "black",
            "savefig.facecolor": "black",
            "savefig.edgecolor": "black",
        }
    )
    # print("Blackout mode set.")


def whiteout():
    mpl.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black",
            "text.color": "black",
            "figure.edgecolor": "white",
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
        }
    )
    # print("Whiteout mode set.")
