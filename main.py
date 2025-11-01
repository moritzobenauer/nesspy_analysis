from pathlib import Path
import src.nesspy_analysis as npa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

if __name__ == "__main__":
   name = 'test'
   base_path = Path("/Volumes/2025/100x400_EFF_3S_GROWTH")
   analysis = npa.DynamicalOrderDisorder(name, base_path)
   analysis.analysis(bootstrap=True, n_bootstrap=10, type="growth_speed", n_samples=8)
   results_fit_speed = analysis.growth_speed_fit_results


   analysis.analysis(bootstrap=True, n_bootstrap=10, type="mu", n_samples=8)
   results_fit_mu = analysis.mu_fit_results

   print(results_fit_speed['v_c_mean'], results_fit_speed['v_c_std'])
   print(results_fit_mu['mu_c_mean'], results_fit_mu['mu_c_std'])

   mu0, dmu0 = analysis.calculate_zero_growth_speed(bootstrap=True, n_bootstrap=16, n_samples=8)
   print(f"Zero growth speed mu_0: {mu0} ± {dmu0}")



plt.plot(results_fit_speed['growth_speed_cont'], results_fit_speed['lorentzian_fit'], label='Lorentzian Fit')
plt.xscale('log')
plt.show()



   