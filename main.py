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

    for i in [1]:
        base_path = Path(
            f"/Volumes/2025/smatch_2025/different_dfs/SL_F2_D0_K{i}_GROWTH"
        )

        thermo = npa.Thermodynamics(jhom=-3.5,
                                    jhet=-2.0,
                                    beta=1.0,
                                    fres=0.0,
                                    k=1.0,
                                    dmu=0.0)

        analysis = npa.DynamicalOrderDisorder(i, base_path)
        analysis.analysis(
            bootstrap=True, n_bootstrap=10, type="mu", n_samples=8
        )
        results_fit_mu = analysis.mu_fit_results
        plt.plot(
            results_fit_mu["mu_cont"],
            results_fit_mu["lorentzian_fit"],
            label=f"K={i}",
        )
        plt.scatter(
            analysis.data["mu"],
            analysis.data["m"],
        )

    # plt.xscale("log")
    plt.legend()
    plt.show()
