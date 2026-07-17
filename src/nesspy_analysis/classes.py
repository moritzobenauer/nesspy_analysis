from pathlib import Path
import pandas as pd
from .iterdir import iterdirs, find_all_final_configs
from .read_csv import read_csv, get_m_vals, get_epsilon, get_epsilon_het
from .fitting import fit_lorentzian, lorentzian, polynomial, fit_polynomial, sigmoid, fit_sigmoid
import numpy as np
from scipy.stats import sem
from multiprocessing import Pool
import json
import logging
import matplotlib.pyplot as plt
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


# ---------------------------------------------------------------------------
# Nearest-neighbour correlation weights w(q) and the corrected supersaturation.
# These module-level helpers back DynamicalOrderDisorder.get_wq() and
# .get_logarithmic_supersat_corrected(). They are kept at module scope (rather
# than as methods) so the Pool worker below stays picklable.
# ---------------------------------------------------------------------------


def get_steady_state_probabilities_numerical(
    epsilon_homo, epsilon_hetero, mu, F, M, k, environment, scheme="HOMO"
):
    """Stationary occupancy probabilities of the 5-state single-site model.

    Returns ``(p_active, p_non_bonding)`` for the given local environment
    ``(n_red, n_blue)``. The driving scheme rescales the rate constant ``k`` or
    the drive ``M`` as a function of the environment.
    """
    n_red, n_blue = environment

    U_red = np.exp(n_red * epsilon_homo + n_blue * epsilon_hetero)
    U_blue = np.exp(n_red * epsilon_hetero + n_blue * epsilon_homo)
    z = np.exp(mu)

    if scheme == "HOMO":
        k = 1.0
    elif scheme == "SCHEME91":
        k = k * np.exp(-(n_red + n_blue))
    elif scheme == "SCHEME93":
        k = k * np.exp(-np.abs(n_red - n_blue))
    elif scheme == "SCHEME6":
        dmu0 = np.log(M)
        M = np.exp(dmu0 * np.exp(-np.abs(n_red - n_blue)))

    # Set up the generator matrix
    L = np.array(
        [
            [-2 * (z + z * F), z, z * F, z, z * F],
            [U_red, -U_red - U_red * k * F * M, U_red * k * F * M, 0, 0],
            [1.0, k, -(k + 1), 0, 0],
            [U_blue, 0.0, 0.0, -U_blue * (1 + F * M * k), U_blue * F * M * k],
            [1.0, 0.0, 0.0, k, -(1 + k)],
        ],
        dtype=np.float64,
    )
    Q = L.T
    evals, evecs = np.linalg.eig(Q)
    evals = np.round(evals, decimals=10)
    evecs = np.round(evecs, decimals=10)

    # Sort eigenvalues/vectors so the stationary state (eigenvalue 0) is first.
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]

    if evecs[0, 0] < 0:
        evecs[:, 0] = -evecs[:, 0]
    pi = evecs[:, 0] / np.sum(evecs[:, 0])

    p_empty, p_red_active, p_red_inactive, p_blue_active, p_blue_inactive = (
        pi[0], pi[1], pi[2], pi[3], pi[4]
    )

    p_active = p_red_active + p_blue_active
    p_non_bonding = p_blue_inactive + p_red_inactive + p_empty

    return p_active, p_non_bonding


def _get_nns(lattice: np.array, x: int, y: int):
    """Count the 1-1, 2-2 and 1-2 bonds around site (x, y) under PBC."""
    NY, NX = lattice.shape

    nnl = [[(y + 1) % NY, x], [(y - 1) % NY, x], [y, (x + 1) % NX], [y, (x - 1) % NX]]
    nns = np.array([lattice[index[0], index[1]] for index in nnl])

    active_site = lattice[y, x]

    pairs_11 = np.sum((nns == 1) & (active_site == 1))
    pairs_22 = np.sum((nns == 2) & (active_site == 2))
    pairs_12 = np.sum((nns == 1) & (active_site == 2)) + np.sum(
        (nns == 2) & (active_site == 1)
    )

    return (pairs_11, pairs_22, pairs_12)


def _count_lattice_pairs(lattice: np.array):
    """Sum bond counts over every site of a lattice.

    Returns ``(pairs_11, pairs_22, pairs_12, number_ones, number_twos)``.
    """
    pairs_11_total = 0
    pairs_22_total = 0
    pairs_12_total = 0
    number_ones_total = 0
    number_twos_total = 0

    for y in range(lattice.shape[0]):
        for x in range(lattice.shape[1]):
            pairs_11, pairs_22, pairs_12 = _get_nns(lattice, x, y)
            pairs_11_total += pairs_11
            pairs_22_total += pairs_22
            pairs_12_total += pairs_12
            number_ones_total += np.sum(lattice[y, x] == 1)
            number_twos_total += np.sum(lattice[y, x] == 2)

    return (
        pairs_11_total,
        pairs_22_total,
        pairs_12_total,
        number_ones_total,
        number_twos_total,
    )


def _process_lattice_file(args):
    """Pool worker: load one lattice_final.npy and return its w(q) contributions.

    Must be a top-level (picklable) function taking a single argument. Returns
    ``(mu_value, pairs_11, pairs_22, pairs_12, number_ones, number_twos)``.
    """
    mu_value, filex, lb_frac, ub_frac = args
    lattice = np.load(filex)
    Lx = lattice.shape[1]
    lattice_cropped = lattice[:, int(lb_frac * Lx):int(ub_frac * Lx)]
    p11, p22, p12, n_ones, n_twos = _count_lattice_pairs(lattice_cropped)
    return mu_value, p11, p22, p12, n_ones, n_twos


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

        print(self.csv_file_number)

        logging.info(
            f"Initialized MultipleSimulations analysis for {self.name} with {self.csv_file_number} CSV files"
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
        self.wq_data = None
        self.sigmoid_params = None
        self.critical_supersat = None
        self.files, self.csv_file_number = iterdirs(self.base_path)

        logging.info(
            f"Initialized DynamicalOrderDisorder analysis for {self.name} with {self.csv_file_number} CSV files"
        )

    def get_thermos_from_file(self) -> Thermos:
        """Auto-detect the Thermos parameters from the simulation output.

        Verifies that the driving parameters are identical across every out.csv
        under ``base_path`` and returns the matching :class:`Thermos`. The
        homogeneous/heterogeneous couplings ``jhom``/``jhet`` are read from the
        ``# jhom``/``# jhet`` header comments; ``fres`` (Δf), ``dmu`` (Δμ), ``k``,
        ``hrc`` and ``hrc_method`` are read from the data rows. Any inconsistency
        across files raises ``ValueError``.

        Only the homogeneous case (``hrc`` inactive → ``'HOMO'``) is supported;
        an active ``hrc`` raises ``NotImplementedError`` until its scheme mapping
        is added.
        """

        def _as_bool(v):
            if isinstance(v, str):
                return v.strip().lower() == "true"
            return bool(v)

        fres_vals, dmu_vals, k_vals = set(), set(), set()
        hrc_vals, hrc_method_vals = set(), set()
        jhom_vals, jhet_vals = set(), set()

        for f in self.files:
            _df = pd.read_csv(f, comment="#", skip_blank_lines=True)
            fres_vals.update(np.round(_df["fres"].unique(), 8))
            dmu_vals.update(np.round(_df["dmu"].unique(), 8))
            k_vals.update(np.round(_df["k"].unique(), 8))
            hrc_vals.update(_as_bool(v) for v in _df["hrc"].unique())
            hrc_method_vals.update(np.round(_df["hrc_method"].unique(), 8))
            jhom_vals.add(round(get_epsilon(f), 8))
            jhet_vals.add(round(get_epsilon_het(f), 8))

        for name, vals in [
            ("fres", fres_vals),
            ("dmu", dmu_vals),
            ("k", k_vals),
            ("hrc", hrc_vals),
            ("hrc_method", hrc_method_vals),
            ("jhom", jhom_vals),
            ("jhet", jhet_vals),
        ]:
            if len(vals) != 1:
                raise ValueError(
                    f"Inconsistent '{name}' across the {len(self.files)} out.csv "
                    f"files: {sorted(vals)}"
                )

        fres = float(next(iter(fres_vals)))
        dmu = float(next(iter(dmu_vals)))
        k = float(next(iter(k_vals)))
        hrc = next(iter(hrc_vals))
        hrc_method = float(next(iter(hrc_method_vals)))
        jhom = float(next(iter(jhom_vals)))
        jhet = float(next(iter(jhet_vals)))

        if hrc:
            raise NotImplementedError(
                f"Active hrc (hrc_method={hrc_method}) is not mapped to a driving "
                "scheme yet; only the homogeneous case (hrc inactive -> 'HOMO') "
                "is supported."
            )
        method = "HOMO"

        thermos = Thermos(
            jhom=jhom, jhet=jhet, fres=fres, dmu=dmu, k=k, method=method
        )
        logger.info(
            "Detected Thermos from files: jhom=%s, jhet=%s, fres=%s, dmu=%s, "
            "k=%s, method=%s",
            jhom, jhet, fres, dmu, k, method,
        )
        return thermos

    def get_raw_data(self) -> pd.DataFrame:
        _df = pd.DataFrame()
        for f in self.files:
            _local = pd.read_csv(f, comment="#", skip_blank_lines=True)
            _df = pd.concat([_df, _local], ignore_index=True)
        _df = _df.sort_values(by=["mu"])
        self.data = _df

        # Check if all RSW values are the same
        rsw_values = self.data["RSW"].unique()
        if len(rsw_values) > 1:
            logger.warning(
                "Multiple RSW values found in the data: %s. This may indicate inconsistent data.",
                rsw_values,
            )
        else:
            logger.info("All RSW values are consistent: %s", rsw_values[0])

        return _df

    def get_oder_parameters(self) -> dict[float, pd.DataFrame]:
        results = {}
        for f in self.files:
            _mu, _df = get_m_vals(f)
            results[_mu] = _df
        return results

    def calculate_zero_growth_speed(
        self, bootstrap: bool = True, n_bootstrap: int = 5, fraction: float = 0.9
    ) -> list[float, float]:
        bootstrap_results = []
        for _ in range(n_bootstrap):
            for f in self.files:
                self.df, header = read_csv(f, n_samples=fraction, bootstrap=True)
                self.data = pd.concat([self.data, self.df], ignore_index=True)
            self.data = self.data.sort_values(by=["mu"])
            mu_min = self.data["mu"].min()
            self.data = self.data[self.data["mu"] < mu_min + 0.3]

            m,b =np.polyfit(self.data["mu"], self.data["growth_speed"], 1)
            x0 = -b/m
            bootstrap_results.append(x0)
        mu_0_mean = np.mean(bootstrap_results)
        mu_0_std = sem(bootstrap_results)
        return [mu_0_mean, mu_0_std]

    def get_precise_doodt(
        self, n_repeats: int = 25, fraction_data: float = 0.9
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

    def get_wq(
        self,
        lb_frac: float = 0.2,
        ub_frac: float = 0.7,
        tolerance: float = 0.01,
    ) -> pd.DataFrame:
        """Compute nearest-neighbour correlation weights w(q) per chemical potential.

        Scans ``lattice_final.npy`` files under each mu-named subfolder of
        ``base_path`` (in parallel), counts 1-1 / 2-2 / 1-2 bonds over the column
        band ``[lb_frac, ub_frac] * Lx`` of each lattice, and normalises them into
        a w(q) distribution per mu. The resulting ``wq_11``/``wq_22``/``wq_12``
        columns are merged onto ``self.data`` with a nearest-mu join (``tolerance``
        guards against matching the wrong mu bucket, since ``self.data['mu']`` is a
        per-run mean that can drift from the folder-derived value).

        Populates ``self.data`` (running :meth:`get_data` first if needed) and
        caches the per-mu table on ``self.wq_data``. Returns ``self.data``.
        """
        if self.data.empty:
            self.get_data()

        # Build a flat (mu_value, file, crop) task list so one pool balances the
        # work across mu folders evenly.
        tasks = []
        for mu_folder in self.base_path.glob("*"):
            if not mu_folder.is_dir():
                continue
            try:
                mu_value = float(mu_folder.name)
            except ValueError:
                continue
            for filex in mu_folder.glob("**/lattice_final.npy"):
                tasks.append((mu_value, filex, lb_frac, ub_frac))

        if not tasks:
            raise ValueError(
                f"No lattice_final.npy files found under {self.base_path}"
            )

        logger.info("Processing %d lattice files for w(q)...", len(tasks))
        with Pool() as pool:
            results = pool.map(_process_lattice_file, tasks)

        # Aggregate per-file counts back by mu_value.
        totals = {}  # mu_value -> [p11, p22, p12, n_ones, n_twos]
        for mu_value, p11, p22, p12, n_ones, n_twos in results:
            acc = totals.setdefault(mu_value, [0, 0, 0, 0, 0])
            acc[0] += p11
            acc[1] += p22
            acc[2] += p12
            acc[3] += n_ones
            acc[4] += n_twos

        records = []
        for mu_value in sorted(totals):
            p11, p22, p12, _, _ = totals[mu_value]
            total_bonds = p11 + p22 + p12
            if total_bonds == 0:
                logger.warning("No bonds found at mu=%s; skipping.", mu_value)
                continue
            records.append(
                {
                    "mu_value": mu_value,
                    "wq_11": p11 / total_bonds,
                    "wq_22": p22 / total_bonds,
                    "wq_12": p12 / total_bonds,
                }
            )

        self.wq_data = pd.DataFrame(records).sort_values(by="mu_value")

        self.data = pd.merge_asof(
            self.data.sort_values(by="mu"),
            self.wq_data,
            left_on="mu",
            right_on="mu_value",
            direction="nearest",
            tolerance=tolerance,
        )
        self.data.drop(columns=["mu_value"], inplace=True)

        unmatched = self.data[self.data["wq_11"].isna()]
        if not unmatched.empty:
            logger.warning(
                "%d row(s) had no w(q) match within tolerance %s:\n%s",
                len(unmatched),
                tolerance,
                unmatched[["mu"]],
            )

        return self.data

    def get_logarithmic_supersat_corrected(self, thermos: Thermos) -> pd.DataFrame:
        """Corrected logarithmic supersaturation dphi = log(S) using w(q) weights.

        For each mu, weights the single-site steady-state active/non-bonding
        occupancies by the measured w(q) distribution over local environments
        ``(2,0), (1,1), (0,2)`` and returns ``log(Z_active / Z_inactive)``.

        Requires :meth:`get_wq` to have been run first (it reads the cached
        ``wq_11``/``wq_22``/``wq_12`` columns). Adds a ``dphi`` column to
        ``self.data`` and returns it.
        """
        required = {"wq_11", "wq_22", "wq_12"}
        if self.data.empty or not required.issubset(self.data.columns):
            raise RuntimeError(
                "Run get_wq() before get_logarithmic_supersat_corrected()."
            )

        epsilon_homo = thermos.jhom
        epsilon_hetero = thermos.jhet
        k = thermos.k
        scheme = thermos.method
        F = np.exp(thermos.fres)
        M = np.exp(thermos.dmu)

        environments = [(2, 0), (1, 1), (0, 2)]

        dphi_by_mu = {}
        for mu in self.data["mu"].unique():
            row = self.data[self.data["mu"] == mu].iloc[0]
            # Order matches `environments`: (red-red, red-blue, blue-blue).
            w_q_vector = [row["wq_11"], row["wq_12"], row["wq_22"]]

            partition_function_active = 0.0
            partition_function_inactive = 0.0
            for env, wq in zip(environments, w_q_vector):
                p_a, p_n = get_steady_state_probabilities_numerical(
                    epsilon_homo, epsilon_hetero, mu, F, M, k, env, scheme=scheme
                )
                partition_function_active += wq * p_a
                partition_function_inactive += wq * p_n

            dphi_by_mu[mu] = np.log(
                partition_function_active / partition_function_inactive
            )

        self.data["dphi"] = self.data["mu"].map(dphi_by_mu)
        return self.data

    def get_critical_supersat(self) -> float:
        """Critical supersaturation from a sigmoidal fit of m vs log(S).

        Fits the order parameter ``m`` against the corrected logarithmic
        supersaturation ``dphi`` to a four-parameter logistic and returns its
        inflection point (the critical supersaturation). Requires
        :meth:`get_logarithmic_supersat_corrected` to have been run first.

        Caches the fit on ``self.sigmoid_params`` and the result on
        ``self.critical_supersat``.
        """
        required = {"dphi", "m"}
        if self.data.empty or not required.issubset(self.data.columns):
            raise RuntimeError(
                "Run get_logarithmic_supersat_corrected() before get_critical_supersat()."
            )

        _df = self.data.dropna(subset=["dphi", "m"]).sort_values(by="dphi")
        popt = fit_sigmoid(_df["dphi"].values, _df["m"].values)

        # popt = [L, x0, k, b]; the inflection point of the logistic is x0.
        self.sigmoid_params = popt
        self.critical_supersat = float(popt[1])

        logger.info("Critical supersaturation (inflection point): %.6f", self.critical_supersat)
        return self.critical_supersat
