import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import argparse 

argparser = argparse.ArgumentParser(description="Plot m versus dphi for different datasets.")
argparser.add_argument("-v", action="store_true", help="Enable velocity plotting")
args = argparser.parse_args()
PLOT = args.v

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D0_K1")
analysis_2 = npa.DynamicalOrderDisorder("nodrive", base_path)
thermos_for_inert = npa.Thermos(fres=0.0, dmu=0.0, k=1.0)

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)

if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=0.0$", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=0.0$",
        fmt="o",
    )


# base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D05_K1_SCHEME6")
# analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
# thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=0.5, k=1.0, method="SCHEME6")

# data = analysis_2.get_data()
# data = data.sort_values(by=["mu"])

# data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
# if PLOT:
#     plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=0.5$", linestyle="solid", ms=2, marker="o")
# else:
#     plt.errorbar(
#         data['dphi'],
#         data["m"],
#         yerr=data["dm"],
#         label=r"$\Delta \mu=0.5$",
#         fmt="o",
#     )



base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=4.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=4.0$", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=4.0$",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6_BJ")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=4.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=4.0$ BJ", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=4.0$ BJ",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=5.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=5.0$", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=5.0$",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=5.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=5.0$ BJ RSW40", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=5.0$ BJ RSW40",
        fmt="o",
    )


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D6_K1_SCHEME6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=6.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=6.0$", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=6.0$",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D6_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=6.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label=r"$\Delta \mu=6.0$ BJ RSW40", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label=r"$\Delta \mu=6.0$ BJ RSW40",
        fmt="o",
    )

if PLOT:
    plt.xscale("log")
    plt.xlabel("Growth Speed")
else:
    plt.xscale("linear")
    plt.xlabel(r"$\beta \Delta \phi$")
    plt.xlim(-0.05, 2.55)


plt.ylim(-0.05,1.05)

plt.ylabel("m")
plt.title("m versus dphi for SCHEME 6")
plt.legend()

plt.legend()
plt.show()