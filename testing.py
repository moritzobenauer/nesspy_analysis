import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

n_bootstrap = 32
n_samples = 0.9

fig, ax = plt.subplots(figsize=(8, 6))
ax2 = ax.twinx()


base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)

results = analysis_2.get_precise_doodt(n_bootstrap, n_samples)

curve_v, curve_mu = analysis_2.get_susc_curves()

mus = np.linspace(-7,0,1000)
suscs = npa.lorentzian(mus, *curve_mu)

print(results)

plt.plot(mus, suscs, label="Fitted Susc. Curve", color="gray", linestyle="--")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

plt.scatter(
    data["mu"],
    data["susc"],
    label="Data Points",
    color="blue",
    alpha=0.5,
    s=10,
)

print(analysis_2.calculate_zero_growth_speed())