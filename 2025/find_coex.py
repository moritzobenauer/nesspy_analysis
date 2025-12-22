import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


flex_coex = {1: -6.9508, 2:-6.8992, 3:-6.8432,4: -6.7826, 5: -6.7175, 6: -6.6478, 8: -6.4945}
for mu in [1,2,3,4,5,6,8]:
    base_path = Path(f"/Users/moritzobenauer/Downloads/20x80_F0_D{mu}_K1_SCHEME_6")
    analysis = npa.DynamicalOrderDisorder(f"mu{mu}", base_path)
    coex, dcoex = analysis.calculate_zero_growth_speed()
    plt.plot(mu, coex, "o", label=f"mu{mu}", color="blue", ms=8)
    print(f"mu{mu} coex difference: {np.round(coex - flex_coex[mu], 4)}")
plt.plot([1,2,3,4,5,6,8], [flex_coex[mu] for mu in [1,2,3,4,5,6,8]], "o--", label="flex", color="red", ms=8)
plt.legend()
plt.title("Coexistence chemical potential vs mu")
plt.xlabel(r"$\beta \Delta \mu$")
plt.ylabel(r"$\beta \mu_\mathrm{coex}$")
plt.show()