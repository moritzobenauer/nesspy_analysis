import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

from scipy.optimize import curve_fit
from scipy.integrate import simpson as simps

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

dphi_cont = np.linspace(0,5.5,1000)
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_0 = sigmoid(dphi_cont, *popt)

if PLOT:
    # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_0, label="Sigmoid Fit D=0", linestyle="--")

if SPEEDS:
    data_ref = data.copy()
    data_ref = data_ref.sort_values(by=["growth_speed"])
    v_cont = np.logspace(-5,0,1000)
    popt, pcov = curve_fit(sigmoid, data_ref['growth_speed'], data_ref["m"], p0=[5e-3, 20])
    m_approx_0 = sigmoid(v_cont, *popt)
    plt.plot(v_cont, m_approx_0, lw=3)
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")

    print(analysis_2.get_precise_doodt(n_repeats=10))
    plt.axvline(analysis_2.get_precise_doodt()[0], color="red", linestyle="--", label=r"$v_c$")

# base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_6")
# analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
# thermos_for_inert = npa.Thermos(dmu=1.0, method="S5")
# data = analysis_2.get_data()
# data = data.sort_values(by=["mu"])
# data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
# dphi_cont = np.linspace(0,3,1000)
# popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
# m_approx_1 = sigmoid(dphi_cont, *popt)
# fx_mu1 = np.abs(m_approx_0 - m_approx_1)
# integral_fx_1 = simps(fx_mu1, dphi_cont)
# # plt.plot(dphi_cont, fx_mu1, label="Sigmoid Fit D=1", linestyle="--")
# if PLOT:
#     plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
#     plt.plot(dphi_cont, m_approx_1, label="Sigmoid Fit D=0", linestyle="--")
# if SPEEDS:

#     plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="-", ms=10, marker="o")

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D05_K1_SCHEME6")
analysis_2 = npa.DynamicalOrderDisorder("mu05", base_path)
thermos_for_inert = npa.Thermos(dmu=0.5, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_05 = sigmoid(dphi_cont, *popt)
fx_mu05 = np.abs(m_approx_0 - m_approx_05)
integral_fx_05 = simps(fx_mu05, dphi_cont)
print(f"     integration result: {integral_fx_05}")
# plt.plot(dphi_cont, fx_mu05, label="Sigmoid Fit D=0.5", linestyle="--")
if PLOT:
    # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_05, label="Sigmoid Fit D=0.5", linestyle="--")
if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="-", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$", color='green')

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_1 = sigmoid(dphi_cont, *popt)
fx_mu1 = np.abs(m_approx_0 - m_approx_1)
integral_fx_1 = simps(fx_mu1, dphi_cont)
print(f"     integration result: {integral_fx_1}")
# plt.plot(dphi_cont, fx_mu1, label="Sigmoid Fit D=1", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="s6d1", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_1, linestyle="--")
if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="-", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$", color='green')


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu2", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_2 = sigmoid(dphi_cont, *popt)
fx_mu2 = np.abs(m_approx_0 - m_approx_2)
integral_fx_2 = simps(fx_mu2, dphi_cont)
print(f"Numerical integration result: {integral_fx_2}")
# plt.plot(dphi_cont, fx_mu2, label="Sigmoid Fit D=2", linestyle="--")
if PLOT:
    # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_2, label="Sigmoid Fit D=2", linestyle="--")
if SPEEDS:
    v_cont = np.logspace(-5,0,1000)
    popt, pcov = curve_fit(sigmoid, data['growth_speed'], data["m"], p0=[5e-2, 0.1])
    m_approx_2 = sigmoid(v_cont, *popt)
    plt.plot(v_cont, m_approx_2, lw=3)
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("mu4", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[1.3, 20])
m_approx_4 = sigmoid(dphi_cont, *popt)
fx_mu4 = np.abs(m_approx_0 - m_approx_4)
integral_fx_4 = simps(fx_mu4, dphi_cont)
print(f"Numerical integration result: {integral_fx_4}")
if PLOT:
    # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_4, label="Sigmoid Fit D=4", linestyle="--")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu5", base_path)
thermos_for_inert = npa.Thermos(dmu=5.0, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[1.7, 20])
m_approx_5 = sigmoid(dphi_cont, *popt)
fx_mu5 = np.abs(m_approx_0 - m_approx_5)
integral_fx_5 = simps(fx_mu5, dphi_cont)
print(f"Numerical integration result: {integral_fx_5}")
if PLOT:
    # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_5, label="Sigmoid Fit D=5", linestyle="--")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D6_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu6", base_path)
thermos_for_inert = npa.Thermos(dmu=6.0, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[1.3, 20])
m_approx_6 = sigmoid(dphi_cont, *popt)
fx_mu6 = np.abs(m_approx_0 - m_approx_6)
integral_fx_6 = simps(fx_mu6, dphi_cont)
print(f"Numerical integration result: {integral_fx_6}")
if PLOT:
    # plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_6, label="Sigmoid Fit D=0", linestyle="--")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D8_K1_SCHEME_6_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu8", base_path)
thermos_for_inert = npa.Thermos(dmu=8.0, method="S5", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[2.3, 20])
m_approx_8 = sigmoid(dphi_cont, *popt)
fx_mu8 = np.abs(m_approx_0 - m_approx_8)
integral_fx_8 = simps(fx_mu8, dphi_cont)
print(f"Numerical integration result: {integral_fx_8}")

# plt.plot(dphi_cont, fx_mu5, label="Sigmoid Fit D=5", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="s6d8", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_8, label="Sigmoid Fit s6d8", linestyle="solid")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$")



base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_7_BJ")
analysis_2 = npa.DynamicalOrderDisorder("mu17", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="S6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.5, 20])
m_approx_17 = sigmoid(dphi_cont, *popt)
fx_mu17 = np.abs(m_approx_0 - m_approx_17)
integral_fx_17 = simps(fx_mu17, dphi_cont)
print(f"Numerical integration result: {integral_fx_17}")

# plt.plot(dphi_cont, fx_mu5, label="Sigmoid Fit D=5", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="s7d1", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_17, linestyle="solid", color="orange")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$")

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu27", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="S6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.8, 20])
m_approx_27 = sigmoid(dphi_cont, *popt)
fx_mu27 = np.abs(m_approx_0 - m_approx_27)
integral_fx_27 = simps(fx_mu27, dphi_cont)
print(f"Numerical integration result: {integral_fx_27}")

# plt.plot(dphi_cont, fx_mu5, label="Sigmoid Fit D=5", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="s7d2", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_27, linestyle="solid", color="red")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_7_BJ")
analysis_2 = npa.DynamicalOrderDisorder("mu47", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="S6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[2.3, 20])
m_approx_47 = sigmoid(dphi_cont, *popt)
fx_mu47 = np.abs(m_approx_0 - m_approx_47)
integral_fx_47 = simps(fx_mu47, dphi_cont)
print(f"Numerical integration result: {integral_fx_47}")

# plt.plot(dphi_cont, fx_mu5, label="Sigmoid Fit D=5", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="s7d4", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_47, linestyle="--")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$")

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_7_BJ_RSW40")
analysis_2 = npa.DynamicalOrderDisorder("mu57", base_path)
thermos_for_inert = npa.Thermos(dmu=5.0, method="S6", fres=0.0, k=1.0)
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[2.3, 20])
m_approx_57 = sigmoid(dphi_cont, *popt)
fx_mu57 = np.abs(m_approx_0 - m_approx_57)
integral_fx_57 = simps(fx_mu57, dphi_cont)
print(f"Numerical integration result: {integral_fx_57}")

# plt.plot(dphi_cont, fx_mu5, label="Sigmoid Fit D=5", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="s7d5", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_57, linestyle="--")

if SPEEDS:
    plt.plot(data['growth_speed'], data["m"], label="No Inert States", linestyle="--", ms=10, marker="o")
    vc = analysis_2.get_precise_doodt(n_repeats=10, fraction_data=0.9)[0]
    plt.axvline(vc, linestyle="--", label=r"$v_c$")

if SPEEDS:
    plt.xlabel("Growth Speed")
    plt.xscale("log")
plt.legend()
plt.show()

plt.plot([0.5, 1,2,4,5,6,8], [integral_fx_05/0.5,integral_fx_1/1, integral_fx_2/2, integral_fx_4/4, integral_fx_5/5, integral_fx_6/6, integral_fx_8/8], marker="o", label="Local Homogeneity Scheme")
plt.plot([1,2,4,5], [integral_fx_17/1, integral_fx_27/2, integral_fx_47/4, integral_fx_57/5], marker="s", color="red", label="Self-Healing Scheme")
plt.ylabel(r"$\langle \Delta m \rangle_{\Delta \phi} (\Delta \mu)^{-1}$")
plt.xlabel(r"$\Delta \mu$")
plt.legend()
plt.show()


