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

base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos()
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[5e-4, 20])
vx0, _, _, _ = analysis_2.get_precise_doodt()

if SPEEDS:
    data_ref = data.copy()
    data_ref = data_ref.sort_values(by=["growth_speed"])
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o",
             color=palette[0], alpha=1.)
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[0], alpha=.2 )
    

vxs_s6 = []



base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D05_K1_SCHEME6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_inert = npa.Thermos(dmu=0.5, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[10e-4, 20])
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="2", linestyle="none", ms=10, marker="^",
             color=palette[2])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[2], alpha=.2 )


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu4", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)
if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )
    

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme6/ML_F0_D5_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu5", base_path)
thermos_for_inert = npa.Thermos(dmu=5.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)
if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="5", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D6_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu6", base_path)
thermos_for_inert = npa.Thermos(dmu=6.0, method="SCHEME6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s6.append(vx)
if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="5", linestyle="none", ms=10, marker="^",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )

palette = sns.color_palette("mako", n_colors=4)

vxs_s7 = []

base_path = Path("/Volumes/2025/research_nov_2025_data/scheme7/ML_F0_D05_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu057", base_path)
thermos_for_inert = npa.Thermos(dmu=0.5, method="SCHEME7", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s7.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s7.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s7.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s7.append(vx)

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
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_s7.append(vx)

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="4 s7", linestyle="none", ms=10, marker="h",
             color=palette[3])
    plt.plot(data['growth_speed'], data["m"], linestyle="solid", lw=3, marker="none",
             color=palette[3], alpha=.2 )
    # plt.axvline(vx, color="black", linestyle="dashed", lw=4)



##### HOMOS

vxs_homo = []

base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D1_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo1", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_homo.append(vx)


base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D2_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo2", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_homo.append(vx)

base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D3_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo3", base_path)
thermos_for_inert = npa.Thermos(dmu=3.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_homo.append(vx)

base_path = Path("/Volumes/2025/research_nov_2025_data/homo/ML_F0_D4_K1")
analysis_2 = npa.DynamicalOrderDisorder("homo4", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="HOMO", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
vx, _, _, _ = analysis_2.get_precise_doodt()
vxs_homo.append(vx)

plt.xscale("log")
plt.legend()

plt.clf()


mus_s7 = np.array([0.5, 1,1.5, 2,4])
mus_s6 = np.array([0.5, 1,1.5, 2,4, 5, 6])
mus_homo = np.array([1, 2, 3, 4])

vxs_s7 = np.array(vxs_s7)
vxs_s6 = np.array(vxs_s6)
vxs_homo = np.array(vxs_homo)

vxs_homo /= vx0
vxs_s7 /= vx0
vxs_s6 /= vx0

efficiency_homo = vxs_homo / mus_homo
efficiency_s7 = vxs_s7 / mus_s7
efficiency_s6 = vxs_s6 / mus_s6


print("S6 speeds:", vxs_s6)
print("S7 speeds:", vxs_s7)
print("HOMO speeds:", vxs_homo)
plt.plot([0, 0.5, 1,1.5, 2,4, 5, 6], [1, vxs_s6[0], vxs_s6[1], vxs_s6[2], vxs_s6[3], vxs_s6[4], vxs_s6[5], vxs_s6[6]], marker="^", label="Inhomogeneous Fuel Distribution",
         color=sns.color_palette("rocket_r", n_colors=1)[0], ms=10)
plt.plot([0, 0.5, 1,1.5, 2,4], [1, vxs_s7[0], vxs_s7[1], vxs_s7[2], vxs_s7[3], vxs_s7[4]], marker="h", label="Self-Healing Scheme",
         color=sns.color_palette("mako", n_colors=1)[0], ms=10)
plt.plot([0, 1, 2, 3, 4], [1, vxs_homo[0], vxs_homo[1], vxs_homo[2], vxs_homo[3]], marker="h", label="Homogeneous Fuel Distribution",
         color=sns.color_palette("viridis", n_colors=1)[0], ms=10)
plt.yscale("log")
plt.legend()
plt.xlabel(r"$\beta \Delta \mu$")
plt.ylabel("Speed Relative to System without Inert States")
# plt.savefig("comparing_schemes_speed.pdf", dpi=600)
plt.show()

plt.clf()
print(efficiency_homo)
print(efficiency_s6)
print(efficiency_s7)

plt.plot(mus_homo, efficiency_homo, label="Homogeneous Fuel Distribution")
plt.plot(mus_s6, efficiency_s6, label="Inhomogeneous Fuel Distribution")
plt.plot(mus_s7, efficiency_s7, label="Self-Healing Scheme")
plt.legend()
plt.xlabel(r"$\beta \Delta \mu$")
plt.yscale("log")
plt.ylabel("Efficiency (Speed / $\Delta \mu$)")
plt.savefig("comparing_schemes_efficiency.pdf", dpi=600)
plt.show()