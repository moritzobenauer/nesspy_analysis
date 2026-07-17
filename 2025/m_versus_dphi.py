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

base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos()

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)

if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="no-inert-states", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="No Inert States",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D0_K1")
analysis_2 = npa.DynamicalOrderDisorder("nodrive", base_path)
thermos_for_inert = npa.Thermos(fres=0.0, dmu=0.0, k=1.0)

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)

if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="inert-states", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="No Inert States",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=1.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu1", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu1",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu2", base_path)
thermos_for_mu2 = npa.Thermos(fres=0.0, dmu=2.0, k=1.0, method="SCHEME6")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu2)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu2", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu2",
        fmt="o",
    )


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu4", base_path)
thermos_for_mu4 = npa.Thermos(fres=0.0, dmu=4.0, k=1.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu4)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu4", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu4",
        fmt="o",
    )


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6_BJ")
analysis_2 = npa.DynamicalOrderDisorder("mu4", base_path)
thermos_for_mu4 = npa.Thermos(fres=0.0, dmu=4.0, k=1.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu4)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu4", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu4",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu5", base_path)
thermos_for_mu5 = npa.Thermos(fres=0.0, dmu=5.0, k=1.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu5)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu5", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu5",
        fmt="o",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D6_K1_SCHEME_6_BJ")
analysis_2 = npa.DynamicalOrderDisorder("mu6", base_path)
thermos_for_mu6 = npa.Thermos(fres=0.0, dmu=6.0, k=1.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu6)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu6", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu6",
        fmt="s--",
    )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D8_K1_SCHEME_6_BJ")

analysis_2 = npa.DynamicalOrderDisorder("mu8", base_path)
thermos_for_mu8 = npa.Thermos(fres=0.0, dmu=8.0, k=1.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu8)
if PLOT:
    plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu8", linestyle="solid", ms=2, marker="o")
else:
    plt.errorbar(
        data['dphi'],
        data["m"],
        yerr=data["dm"],
        label="mu8",
        fmt="o--",
    )






plt.xlabel(r"$\beta \Delta \phi$")
plt.ylabel(r"$\vert m \vert$")
if PLOT:
    plt.xscale("log")
    plt.xlabel(r"Growth Speed")
plt.legend()
plt.show()