import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

n_bootstrap = 1
n_samples = 0.98

fig, ax = plt.subplots(figsize=(8, 6))
ax2 = ax.twinx()


base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)

analysis_2.analysis(bootstrap=False, type="full")
mu_discrete = analysis_2.data["mu"]
m_discrete = analysis_2.data["m"]
susc = analysis_2.data["susc"]

analysis_2.analysis(
    bootstrap=True, n_bootstrap=n_bootstrap, type="mu", n_samples=n_samples
)
mus = analysis_2.mu_fit_results["mu_cont"]
fit = analysis_2.mu_fit_results["lorentzian_fit"]

thermo = npa.Thermos(jhom=-3.5, jhet=-2.0, beta=1.0, fres=-20.0, k=0.0, dmu=0.0)

dphis = npa.calculate_dphi(mus, thermo, drivetype="NODRIVE")
fit = analysis_2.mu_fit_results["lorentzian_fit"]
dphis_discrete = npa.calculate_dphi(mu_discrete, thermo, drivetype="NODRIVE")


ax.plot(dphis, fit, label="no_inert_states", ls="--", ms=5, marker="o")
ax.plot(dphis_discrete, susc, label="no_inert_states_data", ls="--", ms=5, marker="o")

print(
    analysis_2.mu_fit_results
)
plt.show()