from pathlib import Path
import pandas as pd
from .iterdir import iterdirs
from .read_csv import read_csv, get_m_vals
from .fitting import fit_lorentzian, lorentzian, polynomial, fit_polynomial
import numpy as np
from scipy.stats import sem
import json

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Thermos:
    jhom: float = -3.5
    jhet: float = -2.0
    beta: float = 1.0
    fres: float = -20.0
    k: float = 1.0
    dmu: float = 0.0


@dataclass(frozen=True, kw_only=True)
class LatticeDimensions:
    x_size: int = 100
    y_size: int = 100

    def __post_init__(self):
        self.volume = self.x_size * self.y_size


class DynamicalOrderDisorder:
    def __init__(self, name: str, base_path: Path):
        self.name = name
        self.base_path = base_path
        self.data = None

        self.data = pd.DataFrame()
        self.files, self.csv_file_number = iterdirs(self.base_path)

        print("Initialized DynamicalOrderDisorder analysis for", self.name)

    def extract_thermos_from_file(self) -> Thermos:
        pass  # Placeholder

    def get_oder_parameters(self) -> dict[float, pd.DataFrame]:
        results = {}
        for f in self.files:
            _mu, _df = get_m_vals(f)
            results[_mu] = _df
        return results

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

    def save_to_json(self, filename: str = "fit_results.json"):

        output_file = self.base_path / filename
        to_save = {
            "v_c_fit_results": self.growth_speed_fit_results,
            "mu_c_fit_results": self.mu_fit_results,
        }

        with open(output_file, "w") as json_file:
            json.dump(to_save, json_file, indent=4)


    def get_precise_doodt(self, n_repeats: int = 100, fraction_data: float = 0.9) -> list[float, float, float, float]:

        speed_results = []
        mu_results = []
        for i in range(n_repeats):
            self.data = pd.DataFrame()
            for f in self.files:
                self.df, header = read_csv(
                    f, n_samples=fraction_data, bootstrap=True
                )
                self.data = pd.concat([self.data, self.df], ignore_index=True)
            self.data = self.data.sort_values(by=["growth_speed"])
            popt = fit_lorentzian(self.data["growth_speed"], self.data["susc"])
            x0, _, _ = popt
            speed_results.append(x0)

            self.data = self.data.sort_values(by=["mu"])
            popt = fit_lorentzian(self.data["mu"], self.data["susc"])
            x0, _, _ = popt
            mu_results.append(x0)

        v_c_mean = np.mean(speed_results)
        v_c_sem = sem(speed_results)

        mu_c_mean = np.mean(mu_results)
        mu_c_sem = sem(mu_results)

        return [v_c_mean, v_c_sem, mu_c_mean, mu_c_sem]


    def get_susc_curves(self) -> list[list, list]:

        for f in self.files:
            self.df, header = read_csv(
                f, n_samples=1.0, bootstrap=False
            )
            self.data = pd.concat([self.data, self.df], ignore_index=True)
        self.data = self.data.sort_values(by=["growth_speed"])
        pop_speed = fit_lorentzian(self.data["growth_speed"], self.data["susc"])

        self.data = self.data.sort_values(by=["mu"])
        pop_mu = fit_lorentzian(self.data["mu"], self.data["susc"])

        return [pop_speed, pop_mu]


    def get_data(self) -> pd.DataFrame:
        for f in self.files:
            self.df, header = read_csv(
                    f, n_samples=1.0, bootstrap=False
                )
            self.data = pd.concat([self.data, self.df], ignore_index=True)
        return self.data


    # Should be depracated lol
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
        raise DeprecationWarning("analysis() is deprecated.")
        if bootstrap:
            if type == "growth_speed":
                bootstrap_results = {"v_c": [], "gamma_v_c": [], "A_v_c": []}
                for i in range(n_bootstrap):
                    self.data = pd.DataFrame()
                    for f in self.files:
                        self.df, header = read_csv(
                            f, n_samples=n_samples, bootstrap=True
                        )
                        self.data = pd.concat([self.data, self.df], ignore_index=True)
                    # self.data["susc"] = self.data["susc"].astype(float) / np.max(self.data["susc"])
                    self.data = self.data.sort_values(by=["growth_speed"])
                    self.speed_cont = np.linspace(
                        self.data["growth_speed"].min(),
                        self.data["growth_speed"].max(),
                        n_continous_data_points,
                    )
                    # print(self.data["susc"])
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
                        self.df, header = read_csv(
                            f, n_samples=n_samples, bootstrap=True
                        )
                        self.data = pd.concat([self.data, self.df], ignore_index=True)
                    self.data = self.data.sort_values(by=["mu"])
                    self.mu_cont = np.linspace(
                        self.data["mu"].min(),
                        self.data["mu"].max(),
                        n_continous_data_points,
                    )
                    # self.data["susc"] = self.data["susc"].astype(float) / np.max(self.data["susc"])
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
            self.data = pd.DataFrame()
            for f in self.files:
                self.df, header = read_csv(f, n_samples=n_samples)
                self.data = pd.concat([self.data, self.df], ignore_index=True)
            self.data = self.data.sort_values(by=["mu"])
