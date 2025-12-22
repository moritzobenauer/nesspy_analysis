import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import argparse 

argparser = argparse.ArgumentParser(description="Plot m versus dphi for different datasets.")
argparser.add_argument("-v", action="store_true", help="Enable velocity plotting")
args = argparser.parse_args()
PLOT = args.v

colormap = sns.color_palette("mako_r", n_colors=6)
out_data = pd.DataFrame()

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D0_K1")
analysis_2 = npa.DynamicalOrderDisorder("nodrive", base_path)
thermos_for_inert = npa.Thermos(fres=0.0, dmu=0.0, k=1.0)

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)

if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=0.0$", linestyle="none", ms=5, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=0.0$",
        fmt="o--",
        color=colormap[0]
    )

data['drive'] = 0.0
out_data = pd.concat([out_data, data], ignore_index=True)

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D05_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu05", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=0.5, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=0.5$", linestyle="none", ms=5, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=0.5$",
        fmt="o--",
        color=colormap[1]
    )
data['drive'] = 0.5
out_data = pd.concat([out_data, data], ignore_index=True)


base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D1_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=1.0, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=1.0$", linestyle="none", ms=5, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=1.0$",
        fmt="o--",
        color=colormap[2]
    )

data['drive'] = 1.0
out_data = pd.concat([out_data, data], ignore_index=True)

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D15_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu15", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=1.5, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=1.5$", linestyle="none", ms=5, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=1.5$",
        fmt="o-",
        color=colormap[3]
    )

data['drive'] = 1.5
out_data = pd.concat([out_data, data], ignore_index=True)

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=2.0, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=2.0$", linestyle="none", ms=5, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=2.0$",
        fmt="o-",
        color=colormap[4]
    )

data['drive'] = 2.0
out_data = pd.concat([out_data, data], ignore_index=True)

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D4_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=4.0, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

print(data["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=4.0$", linestyle="none", ms=5, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=4.0$",
        fmt="o--",
        color=colormap[5]
    )

data['drive'] = 4.0
out_data = pd.concat([out_data, data], ignore_index=True)

plt.legend()
plt.ylim(-0.05,1.05)
plt.ylabel("m")

if PLOT:
    plt.xlabel("Growth Speed")
    plt.xscale("log")
    plt.savefig("m_vs_speed_scheme7.png", dpi=300)


else:
    
    plt.xlim(-0.05, 2.55)
    plt.xlabel(r"$\beta \Delta \phi$")
    plt.savefig("m_vs_dphi_scheme7.png", dpi=300)

plt.title("m versus dphi for SCHEME 7")
out_data.to_csv("m_vs_dphi_scheme7_data.csv", index=False)
    
plt.show()