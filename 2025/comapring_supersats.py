import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

from scipy.optimize import curve_fit
from scipy.integrate import simpson as simps

import seaborn as sns

palette = sns.color_palette("rocket_r", n_colors=4)

argparser = argparse.ArgumentParser(description="Calculate the integral of the difference between two sigmoid fits.")
argparser.add_argument("-p", action="store_true")
argparser.add_argument("-v", action="store_true", help="speeds")

args = argparser.parse_args()
PLOT = args.p
SPEEDS = args.v

def sigmoid(x, x0, a):
    c = a*(x - x0)
    y = -np.exp(c)/(1+np.exp(c)) + 1
    return y

supersats = []
supersats7 = []
vx = []

base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos()
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[5e-4, 20])
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
# sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
supersats7.append(sx0)
vx.append(vx0)

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D05_K1_SCHEME6")
analysis_2 = npa.DynamicalOrderDisorder("mu05", base_path)
thermos_for_inert = npa.Thermos(dmu=0.5, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[10e-4, 20])
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="1", linestyle="none", ms=10, marker="^",
             color=palette[1])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[1], alpha=.2 )


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[10e-4, 20])
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="1", linestyle="none", ms=10, marker="^",
             color=palette[1])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[1], alpha=.2 )
    


base_path = Path("/Volumes/2025/research_nov_2025_data/scheme6/ML_F0_D15_K1_SCHEME6_SJ")
analysis_2 = npa.DynamicalOrderDisorder("mu15", base_path)
thermos_for_inert = npa.Thermos(dmu=1.5, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[5e-3, 20])
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[5e-2, 0.1])
    plt.plot(data['growth_speed'], data["m"], label="2", linestyle="none", ms=10, marker="^",
             color=palette[2])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[2], alpha=.2 )
    

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu2", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[10e-4, 20])
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="2", linestyle="none", ms=10, marker="^",
             color=palette[2])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[2], alpha=.2 )


base_path = Path("/Volumes/2025/research_nov_2025_data/scheme6/ML_F0_D3_K1_SCHEME6")
analysis_2 = npa.DynamicalOrderDisorder("mu3", base_path)
thermos_for_inert = npa.Thermos(dmu=3.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[10e-4, 20])
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="3", linestyle="none", ms=10, marker="^",
             color=palette[2])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[2], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu4", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu5", base_path)
thermos_for_inert = npa.Thermos(dmu=5.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D6_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu6", base_path)
thermos_for_inert = npa.Thermos(dmu=6.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D8_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu8", base_path)
thermos_for_inert = npa.Thermos(dmu=8.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
#sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats.append(sx0)
vx.append(vx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )


# 
# 
# 
palette = sns.color_palette("mako", n_colors=4)

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D05_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu057", base_path)
thermos_for_inert = npa.Thermos(dmu=0.5, method="SCHEME7", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats7.append(sx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="05 s7", linestyle="none", ms=10, marker="h",
             color=palette[1])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[1], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D1_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu17", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="SCHEME7", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats7.append(sx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="1 s7", linestyle="none", ms=10, marker="h",
             color=palette[1])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[1], alpha=.2 )
    
base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D15_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu157", base_path)
thermos_for_inert = npa.Thermos(dmu=1.5, method="SCHEME7", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats7.append(sx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="1.5 s7", linestyle="none", ms=10, marker="h",
             color=palette[1])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[1], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu27", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="SCHEME7", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats7.append(sx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="2 s7", linestyle="none", ms=10, marker="h",
             color=palette[2])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[2], alpha=.2 )


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_7_BJ")
analysis_2 = npa.DynamicalOrderDisorder("mu47", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="SCHEME7", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats7.append(sx0)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4 s7", linestyle="none", ms=10, marker="h",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )
    # plt.axvline(vx, color="black", linestyle="dashed", lw=4)


# ### HOMO
supersats_homo = []


supersats_homo = []
base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D1_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo1", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats_homo.append(sx0)

base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D2_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo2", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats_homo.append(sx0)

base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D3_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo3", base_path)
thermos_for_inert = npa.Thermos(dmu=3.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats_homo.append(sx0)

base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D4_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo4", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx0, _, sx0, _ = analysis_2.get_precise_doodt()
sx0 = npa.calculate_dphi(sx0, thermos_for_inert)
supersats_homo.append(sx0)


mus = [0, 0.5, 1.0, 1.5, 2.0, 4.0, 5.0, 6.0, 8.0]
plt.plot(mus, supersats, label="Scheme 6", marker="o")

mus = [0, 0.5, 1.0, 1.5, 2.0, 4.0]
plt.plot(mus, supersats7, label="Scheme 7", marker="s")

mus = [1,2,3,4.0]
plt.plot(mus, supersats_homo, label="HOMO", marker="^")
plt.legend()
print(supersats)
print(supersats7)
print(supersats_homo)
# plt.savefig("supersaturation_comparison.png")
plt.show()