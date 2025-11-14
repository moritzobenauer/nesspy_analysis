from pathlib import Path
import pandas as pd
from .iterdir import iterdirs
from .read_csv import read_csv, get_m_vals
from .fitting import fit_lorentzian, lorentzian, polynomial, fit_polynomial
import numpy as np
from scipy.stats import sem
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True)
class Thermos:
    jhom: float = -3.5
    jhet: float = -2.0
    beta: float = 1.0
    fres: float = -20.0
    k: float = 1.0
    dmu: float = 0.0
    method: str = "NODRIVE"

    # In the future it might be even more useful to provide an interaction matrix
    # for more complex systems.

    epsilon_matrix: np.array = field(default_factory=lambda: np.array([[-3.5, -2.0], [-2.0, -3.5]]))


@dataclass(kw_only=True)
class Lattice2D:
    x_size: int = 100
    y_size: int = 100
    pbc: str = "periodic"
    restricted_sampling: bool = False
    rs_width: int = 0

    def __post_init__(self):
        self.volume = self.x_size * self.y_size


class MultipleSimulations:
    def __init__(self, name: str, base_paths: list[Path]):
        self.name = name
        self.base_paths = base_paths
        self.data = pd.DataFrame()
        self.files = []
        self.csv_file_number = 0

        for base_path in self.base_paths:
            files, csv_file_number = iterdirs(base_path)
            self.files.extend(files)
            self.csv_file_number += csv_file_number

        logging.info(
            "Initialized MultipleSimulations analysis for %s with %d CSV files",
            self.name,
            self.csv_file_number,
        )

    def get_raw_data(self) -> pd.DataFrame:
        _df = pd.DataFrame()
        for f in self.files:
            _local = pd.read_csv(f, comment="#", skip_blank_lines=True)
            _df = pd.concat([_df, _local], ignore_index=True)
        self.data = _df
        logging.info("# Data points loaded: %d", len(self.data))
        return _df


class DynamicalOrderDisorder:
    def __init__(self, name: str, base_path: Path):
        self.name = name
        self.base_path = base_path
        self.data = None

        self.data = pd.DataFrame()
        self.files, self.csv_file_number = iterdirs(self.base_path)

        logging.info("Initialized DynamicalOrderDisorder analysis for", self.name)

    def extract_thermos_from_file(self) -> Thermos:
        raise NotImplementedError(
            "This method is not implemented yet. Please implement it to extract thermodynamic parameters from the files."
        )

    def get_raw_data(self) -> pd.DataFrame:
        _df = pd.DataFrame()
        for f in self.files:
            _local = pd.read_csv(f, comment="#", skip_blank_lines=True)
            _df = pd.concat([_df, _local], ignore_index=True)
        _df = _df.sort_values(by=["mu"])
        self.data = _df
        return _df

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

    def get_precise_doodt(
        self, n_repeats: int = 100, fraction_data: float = 0.9
    ) -> list[float, float, float, float]:

        speed_results = []
        mu_results = []
        for i in range(n_repeats):
            self.data = pd.DataFrame()
            for f in self.files:
                self.df, header = read_csv(f, n_samples=fraction_data, bootstrap=True)
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
            self.df, header = read_csv(f, n_samples=1.0, bootstrap=False)
            self.data = pd.concat([self.data, self.df], ignore_index=True)
        self.data = self.data.sort_values(by=["growth_speed"])
        pop_speed = fit_lorentzian(self.data["growth_speed"], self.data["susc"])

        self.data = self.data.sort_values(by=["mu"])
        pop_mu = fit_lorentzian(self.data["mu"], self.data["susc"])

        return [pop_speed, pop_mu]

    def get_data(self) -> pd.DataFrame:
        for f in self.files:
            self.df, header = read_csv(f, n_samples=1.0, bootstrap=False)
            self.data = pd.concat([self.data, self.df], ignore_index=True)
        return self.data
