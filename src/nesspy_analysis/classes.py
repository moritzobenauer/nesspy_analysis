from pathlib import Path
import pandas as pd
from .iterdir import iterdirs
from .read_csv import read_csv
from .fitting import fit_lorentzian, lorentzian, polynomial, fit_polynomial
import numpy as np
from scipy.stats import sem
import json



class Thermos:
    def __init__(
        self,
        jhom: float = -3.5,
        jhet: float = -2.0,
        beta: float = 1.0,
        fres: float = -20.0,
        k: float = 1.0,
        dmu: float = 0.0,
    ):
        self.jhom = jhom
        self.jhet = jhet
        self.beta = beta
        self.fres = fres
        self.k = k
        self.dmu = dmu



class DynamicalOrderDisorder:
    def __init__(self, name: str, base_path: Path):
        self.name = name
        self.base_path = base_path
        self.data = None

        self.data = pd.DataFrame()
        self.files, self.csv_file_number = iterdirs(self.base_path)

    def calculate_zero_growth_speed(
        self, bootstrap: bool = True, n_bootstrap: int = 16, n_samples: int = 6
    ) -> list[float, float]:
        if bootstrap:
            bootstrap_results = []
            for i in range(n_bootstrap):
                for f in self.files:
                    self.df, header = read_csv(f, n_samples=n_samples, bootstrap=True)
                    self.data = pd.concat([self.data, self.df], ignore_index=True)
                self.data = self.data.sort_values(by=["mu"])
                popt = fit_polynomial(self.data["mu"], self.data["growth_speed"])
                a, b, c, x0 = popt
                bootstrap_results.append(x0)
            mu_0_mean = np.mean(bootstrap_results)
            mu_0_std = sem(bootstrap_results)
            return [mu_0_mean, mu_0_std]
        
    def save_to_json(self, filename: str='fit_results.json'):
       
        output_file = self.base_path / filename
        to_save = {'v_c_fit_results': self.growth_speed_fit_results,
                   'mu_c_fit_results': self.mu_fit_results}

        with open(output_file, "w") as json_file:
            json.dump(to_save, json_file, indent=4)

    def analysis(
        self,
        bootstrap: bool = False,
        n_bootstrap: int = 16,
        type: str = "growth_speed",
        n_samples: int = 6,
        n_continous_data_points: int = 5000,
        plot_results: bool = False,
        save_results: bool = False,
    ):
        if bootstrap:
            if type == "growth_speed":
                bootstrap_results = {"v_c": [], "gamma_v_c": [], "A_v_c": []}
                for i in range(n_bootstrap):
                    for f in self.files:
                        self.df, header = read_csv(f, n_samples=n_samples, bootstrap=True)
                        self.data = pd.concat([self.data, self.df], ignore_index=True)
                    self.data = self.data.sort_values(by=["growth_speed"])
                    self.speed_cont = np.linspace(
                        self.data["growth_speed"].min(),
                        self.data["growth_speed"].max(),
                        n_continous_data_points,
                    )
                    popt = fit_lorentzian(self.data["growth_speed"], self.data["susc"])
                    x0, gamma, A = popt
                    bootstrap_results["v_c"].append(x0)
                    bootstrap_results["gamma_v_c"].append(gamma)
                    bootstrap_results["A_v_c"].append(A)
                v_c_mean = np.mean(bootstrap_results["v_c"])
                v_c_std = sem(bootstrap_results["v_c"])
                gamma_v_c_mean = np.mean(bootstrap_results["gamma_v_c"])
                gamma_v_c_std = sem(bootstrap_results["gamma_v_c"])
                A_v_c_mean = np.mean(bootstrap_results["A_v_c"])
                A_v_c_std = sem(bootstrap_results["A_v_c"])

                lorentzian_fit = lorentzian(
                    self.speed_cont, v_c_mean, gamma_v_c_mean, A_v_c_mean
                )

                self.growth_speed_fit_results = {
                    "v_c_mean": v_c_mean,
                    "v_c_std": v_c_std,
                    "gamma_v_c_mean": gamma_v_c_mean,
                    "gamma_v_c_std": gamma_v_c_std,
                    "A_v_c_mean": A_v_c_mean,
                    "A_v_c_std": A_v_c_std,
                    "growth_speed_cont": self.speed_cont,
                    "lorentzian_fit": lorentzian_fit,
                }
            if type == "mu":
                bootstrap_results = {"mu_c": [], "gamma_mu_c": [], "A_mu_c": []}
                for i in range(n_bootstrap):
                    for f in self.files:
                        self.df, header = read_csv(f, n_samples=n_samples, bootstrap=True)
                        self.data = pd.concat([self.data, self.df], ignore_index=True)
                    self.data = self.data.sort_values(by=["mu"])
                    self.mu_cont = np.linspace(
                        self.data["mu"].min(),
                        self.data["mu"].max(),
                        n_continous_data_points,
                    )
                    popt = fit_lorentzian(self.data["mu"], self.data["susc"])
                    x0, gamma, A = popt
                    bootstrap_results["mu_c"].append(x0)
                    bootstrap_results["gamma_mu_c"].append(gamma)
                    bootstrap_results["A_mu_c"].append(A)
                mu_c_mean = np.mean(bootstrap_results["mu_c"])
                mu_c_std = sem(bootstrap_results["mu_c"])
                gamma_mu_c_mean = np.mean(bootstrap_results["gamma_mu_c"])
                gamma_mu_c_std = sem(bootstrap_results["gamma_mu_c"])
                A_mu_c_mean = np.mean(bootstrap_results["A_mu_c"])
                A_mu_c_std = sem(bootstrap_results["A_mu_c"])

                lorentzian_fit = lorentzian(
                    self.mu_cont, mu_c_mean, gamma_mu_c_mean, A_mu_c_mean
                )

                self.mu_fit_results = {
                    "mu_c_mean": mu_c_mean,
                    "mu_c_std": mu_c_std,
                    "gamma_mu_c_mean": gamma_mu_c_mean,
                    "gamma_mu_c_std": gamma_mu_c_std,
                    "A_mu_c_mean": A_mu_c_mean,
                    "A_mu_c_std": A_mu_c_std,
                    "mu_cont": self.mu_cont,
                    "lorentzian_fit": lorentzian_fit,
                }

        if not bootstrap and type == "full":
            for f in self.files:
                self.df, header = read_csv(f, n_samples=n_samples)
                self.data = pd.concat([self.data, self.df], ignore_index=True)
                self.data = self.data.sort_values(by=["mu"])
