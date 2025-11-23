import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

from scipy.optimize import curve_fit
from scipy.integrate import simpson as simps

argparser = argparse.ArgumentParser(description="Calculate the integral of the difference between two sigmoid fits.")
argparser.add_argument("-p", action="store_true", help="Path to the first dataset")
args = argparser.parse_args()
PLOT = args.p

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

dphi_cont = np.linspace(0,2,1000)
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_0 = sigmoid(dphi_cont, *popt)

if PLOT:
    plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_0, label="Sigmoid Fit D=0", linestyle="--")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos(dmu=1.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
dphi_cont = np.linspace(0,3,1000)
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_1 = sigmoid(dphi_cont, *popt)
fx_mu1 = np.abs(m_approx_0 - m_approx_1)
integral_fx_1 = simps(fx_mu1, dphi_cont)
# plt.plot(dphi_cont, fx_mu1, label="Sigmoid Fit D=1", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_1, label="Sigmoid Fit D=0", linestyle="--")

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos(dmu=2.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_2 = sigmoid(dphi_cont, *popt)
fx_mu2 = np.abs(m_approx_0 - m_approx_2)
integral_fx_2 = simps(fx_mu2, dphi_cont)
print(f"     integration result: {integral_fx_2}")
# plt.plot(dphi_cont, fx_mu2, label="Sigmoid Fit D=2", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_2, label="Sigmoid Fit D=0", linestyle="--")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D4_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos(dmu=4.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[0.3, 20])
m_approx_4 = sigmoid(dphi_cont, *popt)
fx_mu4 = np.abs(m_approx_0 - m_approx_4)
integral_fx_4 = simps(fx_mu4, dphi_cont)
print(f"Numerical integration result: {integral_fx_4}")
# plt.plot(dphi_cont, fx_mu4, label="Sigmoid Fit D=4", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_4, label="Sigmoid Fit D=0", linestyle="--")


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D5_K1_SCHEME_6")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos(dmu=5.0, method="SCHEME6")
data = analysis_2.get_data()
data = data.sort_values(by=["mu"])
data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)
# plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
popt, pcov = curve_fit(sigmoid, data['dphi'], data["m"], p0=[1.3, 20])
m_approx_5 = sigmoid(dphi_cont, *popt)
fx_mu5 = np.abs(m_approx_0 - m_approx_5)
integral_fx_5 = simps(fx_mu5, dphi_cont)
print(f"Numerical integration result: {integral_fx_5}")
# plt.plot(dphi_cont, fx_mu5, label="Sigmoid Fit D=5", linestyle="--")
if PLOT:
    plt.plot(data['dphi'], data["m"], label="No Inert States", linestyle="none", ms=10, marker="o")
    plt.plot(dphi_cont, m_approx_5, label="Sigmoid Fit D=0", linestyle="--")
plt.legend()
plt.show()

plt.plot([1,2,4,5], [integral_fx_1/1, integral_fx_2/2, integral_fx_4/4, integral_fx_5/5], marker="o")
plt.ylabel(r"$\langle \Delta m \rangle_{\Delta \phi} (\Delta \mu)^{-1}$")
plt.xlabel(r"$\Delta \mu$")
plt.show()


