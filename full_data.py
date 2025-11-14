import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

base_path = Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0")
# analysis = npa.DynamicalOrderDisorder("no_inert_states", base_path)
# df = analysis.get_raw_data()
# print(df.head())



# plt.show()

base_paths = [
    Path("/Users/moritzobenauer/Desktop/ML_F-20_D0_K0"),
    Path("/Users/moritzobenauer/Downloads/ML_F0_D0_K1"),
    Path("/Users/moritzobenauer/Downloads/ML_F0_D5_K1_SCHEME_6")
]
         
multiples = npa.MultipleSimulations('multiple_simulations', base_paths)
raw_data = multiples.get_raw_data()
print(len(raw_data))
g = sns.relplot(
    data=raw_data,
    x="mu", y="m",
    hue="t",
    palette='rocket', sizes=(10, 200),
)
plt.show()
