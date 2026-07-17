import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pickle

# base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D8_K1_SCHEME_6_BJ_RSW40/-4.1")
# base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D0_K1/-6.3")
# base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D8_K1_SCHEME_6_BJ/-6.2")
base_path = Path("/Volumes/2025/research_nov_2025_data/SL_F0_SCHEME_93_D3_K10_GROWTH/-4.14")



confs = npa.find_all_final_configs(base_path)
average_cluster_sizes = []
order_parameters = []
for conf in confs:
    lattice = np.load(conf)
    oparam_full = np.round(npa.calculate_order_parameter(lattice, method="MLO2024", lb_trr=0.3, ub_trr=0.8),4)

    q = npa.calculate_average_cluster_size(lattice, lb_trr=0.3, ub_trr=0.8, min_size=4)
    normalized_q = q[1]/ (lattice.shape[0] * lattice.shape[1])
    
    average_cluster_sizes.append(normalized_q)
    order_parameters.append(oparam_full)
npa.plot_all_configurations(confs)

print("q values mean/median:")
print(np.mean(average_cluster_sizes))
print(np.median(average_cluster_sizes))
print("m values mean/median:")
print(np.mean(order_parameters))
print(np.median(order_parameters))
plt.show()