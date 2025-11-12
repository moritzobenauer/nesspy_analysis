import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

n_bootstrap = 1
n_samples = 0.98

fig, ax = plt.subplots(figsize=(8, 6))
ax2 = ax.twinx()


base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
results = analysis_2.get_oder_parameters()

for mu, ms in results.items():
    sns.histplot(x=ms, ax=ax, label=f"mu={mu}", kde=True, stat="density", element="step")
ax.legend()
plt.show()