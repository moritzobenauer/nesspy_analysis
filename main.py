from pathlib import Path
import src.nesspy_analysis as npa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

if __name__ == "__main__":
    # name = "test"
    # base_path = Path("/Volumes/2025/smatch_2025/different_dfs/SL_F2_D0_K10_GROWTH")
    # analysis = npa.DynamicalOrderDisorder(name, base_path)
    # analysis.analysis(bootstrap=True, n_bootstrap=10, type="growth_speed", n_samples=8)
    # results_fit_speed = analysis.growth_speed_fit_results

    # analysis.analysis(bootstrap=True, n_bootstrap=10, type="mu", n_samples=8)
    # results_fit_mu = analysis.mu_fit_results

    # print(results_fit_speed["v_c_mean"], results_fit_speed["v_c_std"])
    # print(results_fit_mu["mu_c_mean"], results_fit_mu["mu_c_std"])

    # mu0, dmu0 = analysis.calculate_zero_growth_speed(
    #     bootstrap=True, n_bootstrap=16, n_samples=8
    # )
    # print(f"Zero growth speed mu_0: {mu0} ± {dmu0}")

    # analysis.analysis(bootstrap=False, type="full")
    # print(analysis.data)

    # plt.plot(
    #     results_fit_speed["growth_speed_cont"],
    #     results_fit_speed["lorentzian_fit"],
    #     label="Lorentzian Fit",
    # )
    # plt.scatter(
    #     analysis.data["growth_speed"],
    #     analysis.data["susc"],
    #     color="tab:red",
    #     label="Data",
    #     s=50,
    # )
    # plt.axvline(results_fit_speed["v_c_mean"], lw=3)
    # plt.xscale("log")
    # plt.legend()

    # plt.clf()

     base_path = Path(
         f"/Volumes/2025/2026_FIXED_DT/ML_F-20.0_D0.0_K1.0_SCHEME_0.0"
     )

     thermo = npa.Thermos(jhom=-3.5,
                                 jhet=-2.0,
                                 beta=1.0,
                                 fres=-20.0,
                                 k=1.0,
                                 dmu=0.0,
                                 method="NODRIVE",)

     analysis = npa.DynamicalOrderDisorder('test', base_path)
     df = analysis.get_data()
     df = df.sort_values(by='mu')

     plt.errorbar(df['mu'], df['growth_speed'], yerr=df['dgrowth_speed'], fmt='o', label='Data with error bars')

     mu_0, mu_0_std = analysis.calculate_zero_growth_speed()
     plt.axvline(mu_0, color='r', linestyle='--', label=f'Zero Growth Speed μ₀ = {mu_0:.2f} ± {mu_0_std:.2f}')
     plt.grid()
     plt.show()


