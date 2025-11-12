import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from scipy.special import rel_entr

n_bootstrap = 1
n_samples = 0.98

fig, ax = plt.subplots(figsize=(8, 6))
ax2 = ax.twinx()


base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
analysis_2 = npa.DynamicalOrderDisorder("no_inert_states", base_path)
results = analysis_2.get_oder_parameters()

test_data = results[-6.35]
hist, edges = np.histogram(test_data, bins=100, range=(0, 1), density=True)
bin_centers = 0.5 * (edges[1:] + edges[:-1])
hist = hist + 1e-10


compare_data = results[-6.9]
hist2, edges2 = np.histogram(compare_data, bins=100, range=(0, 1), density=True)
bin_centers2 = 0.5 * (edges2[1:] + edges2[:-1])
hist2 = hist2+ 1e-10

rel_entr_result = rel_entr(hist, hist2)
kl_divergence = np.sum(rel_entr_result)
print(f"KL Divergence: {kl_divergence}")
print(rel_entr_result)

reference_pdf, edges = np.histogram(results[-6.9], bins=100, range=(0, 1), density=True)
bin_centers = 0.5 * (edges[1:] + edges[:-1])
reference_pdf = reference_pdf + 1e-12

kl_divergences = {}
for key in results.keys():
    current_pdf, edges = np.histogram(results[key], bins=100, range=(0, 1), density=True)
    current_pdf = current_pdf + 1e-12
    rel_entr_result = rel_entr(current_pdf, reference_pdf)
    kl_divergence = np.sum(rel_entr_result)
    kl_divergences[key] = kl_divergence

print(kl_divergences)
kl_divergences_frame = pd.DataFrame.from_dict(kl_divergences, orient='index', columns=['KL Divergence'])
normalized_df=(kl_divergences_frame-kl_divergences_frame.min())/(kl_divergences_frame.max()-kl_divergences_frame.min())
normalized_df = normalized_df.sort_index()
plt.plot(normalized_df.index, normalized_df['KL Divergence'], marker='o', color='b', label='Normalized KL Divergence')

plt.show()