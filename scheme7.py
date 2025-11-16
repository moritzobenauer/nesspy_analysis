import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
thermos_for_inert = npa.Thermos()

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_inert)

# plt.errorbar(
#     data['dphi'],
#     data["m"],
#     yerr=data["dm"],
#     label="No Inert States",
#     fmt="o",
# )

plt.plot(data['growth_speed'], data["m"], label="no-inert-states", linestyle="none", ms=10, marker="v")

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D1_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu1", base_path)
thermos_for_mu1 = npa.Thermos(fres=0.0, dmu=1.0, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu1)
# plt.errorbar(
#     data['dphi'],
#     data["m"],
#     yerr=data["dm"],
#     label="mu1",
#     fmt="o",
# )
plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu1", linestyle="none", ms=10, marker="s")

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D2_K1_SCHEME_7")
analysis_2 = npa.DynamicalOrderDisorder("mu2", base_path)
thermos_for_mu2 = npa.Thermos(fres=0.0, dmu=2.0, k=1.0, method="SCHEME7")

data = analysis_2.get_data()
data = data.sort_values(by=["mu"])

data["dphi"] = npa.calculate_dphi(data["mu"], thermos_for_mu2)
# plt.errorbar(
#     data['dphi'],
#     data["m"],
#     yerr=data["dm"],
#     label="mu2",
#     fmt="o",
# )
plt.plot(data['growth_speed'], data["m"], label="Growth Speed mu2", linestyle="none", ms=10, marker="o")

print(data['growth_speed'])

plt.xscale("log")
plt.legend()
plt.show()
