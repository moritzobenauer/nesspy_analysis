from pathlib import Path
import pandas as pd
from .iterdir import iterdirs, find_all_final_configs
from .read_csv import (
    read_csv, get_m_vals, get_epsilon, get_epsilon_het,
    get_nesspy_version, report_legacy_run,
)
from .schemes import (
    SCHEMES, SCHEME_LABELS, SCHEME_ALIASES, canonical_scheme, scheme_from_hrc,
    scheme_short_label, scheme_math_label, scheme_description,
)
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

    # Driving scheme, named S0-S6 (see schemes.py). The pre-rename spellings
    # ("NODRIVE", "HOMO", "SCHEME91", ...) are accepted and normalised in
    # __post_init__, so `Thermos(method="HOMO").method` reads back as "S1".
    method: str = "S0"

    # In the future it might be even more useful to provide an interaction matrix
    # for more complex systems. By default it is derived from jhom/jhet in
    # __post_init__ (diagonal = jhom, off-diagonal = jhet); pass it explicitly to
    # override.
    epsilon_matrix: np.array = None

    def __post_init__(self):
        # frozen dataclass -> assign via object.__setattr__. Normalise the
        # scheme name so every consumer sees the canonical S0-S6 spelling; an
        # unknown name raises here rather than silently reaching the physics.
        object.__setattr__(self, "method", canonical_scheme(self.method))

        # Only build the matrix from jhom/jhet when the caller didn't supply
        # one, so the interaction matrix stays consistent with the detected
        # couplings.
        if self.epsilon_matrix is None:
            object.__setattr__(
                self,
                "epsilon_matrix",
                np.array([[self.jhom, self.jhet], [self.jhet, self.jhom]]),
            )


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
# Driving schemes.
#
# The registry itself lives in schemes.py (it is needed by read_csv.py too, and
# that module cannot import from here). The names are re-exported so that
# `npa.scheme_from_hrc(...)` and `from nesspy_analysis.classes import
# SCHEME_LABELS` keep working. Schemes are named S0-S6 throughout; the old
# spellings ("HOMO", "SCHEME91", ...) are still accepted as aliases.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Nearest-neighbour correlation weights w(q) and the corrected supersaturation.
# These module-level helpers back DynamicalOrderDisorder.get_wq() and
# .get_logarithmic_supersat_corrected(). They are kept at module scope (rather
# than as methods) so the Pool worker below stays picklable.
# ---------------------------------------------------------------------------


def scheme_rescaled_drive_and_rate(scheme, M, k, environment):
    """Apply a driving scheme's local perturbation to the drive and the rate.

    Returns ``(M_red, M_blue, k)`` for the local environment
    ``(n_red, n_blue)``, where ``M = exp(dmu)`` is the drive as read from the
    data and ``M_red``/``M_blue`` are the drives seen by the red-active and
    blue-active states. They differ only for the colour-conditioned S6. See
    dealing_with_different_schemes.md for the definition of each ``scheme``,
    which is one of S0-S6 (legacy aliases accepted).

    This mirrors ``spatial_dmu()``/``spatial_baserate()`` in ``nesspy/src/hrc.py``
    -- nesspy is authoritative for what each scheme does, since it generated the
    data being analyzed.
    """
    scheme = canonical_scheme(scheme)
    n_red, n_blue = environment

    M_red = M
    M_blue = M

    if scheme in ("S0", "S1"):
        # S1 / homogeneous driving: base rate is unity, drive used as read.
        # S0 is the undriven reference and behaves the same here (M = 1).
        k = 1.0
    elif scheme == "S2":
        # S2: rate rescaled by the total number of neighbours.
        k = k * np.exp(-(n_red + n_blue))
    elif scheme == "S3":
        # S3: rate rescaled by the neighbour difference.
        k = k * np.exp(-np.abs(n_red - n_blue))
    elif scheme == "S4":
        # S4: drive dmu rescaled by |n_red + n_blue|; k unchanged.
        dmu0 = np.log(M)
        M_red = M_blue = np.exp(dmu0 * np.exp(-np.abs(n_red + n_blue)))
    elif scheme == "S5":
        # S5: drive dmu rescaled by |n_red - n_blue|; k unchanged.
        dmu0 = np.log(M)
        M_red = M_blue = np.exp(dmu0 * np.exp(-np.abs(n_red - n_blue)))
    elif scheme == "S6":
        # S6: colour-conditioned drive, exponential in the *likewise*-neighbour
        # count n' (n_red for a red site, n_blue for a blue site), so the drive
        # decreases monotonically as a site gains neighbours of its own colour.
        # k is unchanged.
        #
        # BUGFIX 2026-08-05 the two drives were conditioned on the *unlike*
        # neighbours (M_red damped by n_blue and vice versa), following
        # dealing_with_different_schemes.md. nesspy conditions on the likewise
        # count -- `nhat = nred if current_state == 1 else nblue` in
        # nesspy/src/hrc.py with RED = 1 in nesspy/src/kmc.py -- and nesspy is
        # authoritative, so red is damped by n_red and blue by n_blue.
        dmu0 = np.log(M)
        M_red = np.exp(dmu0 * np.exp(-n_red))
        M_blue = np.exp(dmu0 * np.exp(-n_blue))
    else:
        raise ValueError(f"Unknown driving scheme: {scheme}")

    return (M_red, M_blue, k)


def get_steady_state_probabilities_numerical(
    epsilon_homo, epsilon_hetero, mu, F, M, k, environment, scheme="S1"
):
    """Stationary occupancy probabilities of the 5-state single-site model.

    Returns ``(p_active, p_non_bonding)`` for the given local environment
    ``(n_red, n_blue)``. The driving scheme rescales the rate constant ``k`` or
    the drive ``M`` as a function of the environment via
    :func:`scheme_rescaled_drive_and_rate`. ``scheme`` is one of S0-S6 (legacy
    aliases accepted).
    """
    n_red, n_blue = environment

    U_red = np.exp(n_red * epsilon_homo + n_blue * epsilon_hetero)
    U_blue = np.exp(n_red * epsilon_hetero + n_blue * epsilon_homo)
    z = np.exp(mu)

    # The drive enters the generator separately for the red-active and
    # blue-active states, so we track M_red / M_blue independently. For every
    # scheme except the colour-conditioned S6 the two are equal.
    M_red, M_blue, k = scheme_rescaled_drive_and_rate(scheme, M, k, environment)

    # Set up the generator matrix. The red-active row uses M_red and the
    # blue-active row uses M_blue (identical except for S6).
    L = np.array(
        [
            [-2 * (z + z * F), z, z * F, z, z * F],
            [U_red, -U_red - U_red * k * F * M_red, U_red * k * F * M_red, 0, 0],
            [1.0, k, -(k + 1), 0, 0],
            [U_blue, 0.0, 0.0, -U_blue * (1 + F * M_blue * k), U_blue * F * M_blue * k],
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


def _process_cluster_observables_file(args):
    """Pool worker: per-lattice wrong-bond fraction q and blue cluster size r.

    Must be a top-level (picklable) function taking a single argument. Returns
    ``(mu_value, q_frac, r_norm)`` for one lattice_final.npy, both measured over
    the column band ``[lb_frac, ub_frac] * Lx``:

    * ``q_frac`` -- fraction of 1-2 ("wrong") bonds over all counted bonds; NaN
      if the cropped lattice has no bonds at all.
    * ``r_norm`` -- mean size of blue (value 2) 4-connected clusters with
      cardinality ``>= min_size``, normalized by the cropped lattice area; 0.0
      when no cluster clears the threshold.
    """
    from scipy.ndimage import label

    mu_value, filex, lb_frac, ub_frac, min_size = args
    lattice = np.load(filex)
    Lx = lattice.shape[1]
    cropped = lattice[:, int(lb_frac * Lx):int(ub_frac * Lx)]

    # q: fraction of wrong (1-2) bonds. Same bond counting as get_wq(), but kept
    # per-lattice so the caller can report a mean and SEM across lattices.
    p11, p22, p12, _, _ = _count_lattice_pairs(cropped)
    total_bonds = p11 + p22 + p12
    q_frac = p12 / total_bonds if total_bonds > 0 else np.nan

    # r: normalized mean blue cluster size (4-connectivity).
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    labeled, num = label(cropped == 2, structure)
    sizes = [s for s in (np.sum(labeled == idx) for idx in range(1, num + 1)) if s >= min_size]
    area = cropped.shape[0] * cropped.shape[1]
    r_norm = (np.mean(sizes) / area) if sizes else 0.0

    return mu_value, q_frac, r_norm


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
        self.cluster_data = None
        self.sigmoid_params = None
        self.critical_supersat = None
        self.critical_supersat_err = None
        self.critical_supersat_cov_err = None
        self.files, self.csv_file_number = iterdirs(self.base_path)

        logging.info(
            f"Initialized DynamicalOrderDisorder analysis for {self.name} with {self.csv_file_number} CSV files"
        )

        # If this run was written by a pre-1.9.0 nesspy, say so once here for the
        # whole run directory. Doing it at construction keeps the per-mu notices
        # from read_csv() quiet no matter which method is called first.
        report_legacy_run(self.base_path, self.files)

    def get_thermos_from_file(self) -> Thermos:
        """Auto-detect the Thermos parameters from the simulation output.

        Verifies that the driving parameters are identical across every out.csv
        under ``base_path`` and returns the matching :class:`Thermos`. The
        homogeneous/heterogeneous couplings ``jhom``/``jhet`` are read from the
        ``# jhom``/``# jhet`` header comments; ``fres`` (Δf), ``dmu`` (Δμ), ``k``,
        ``hrc`` and ``hrc_method`` are read from the data rows. Any inconsistency
        across files raises ``ValueError``.

        The ``(hrc, hrc_method)`` pair of each file is mapped onto its canonical
        driving scheme (S0-S6) via :func:`scheme_from_hrc`: ``hrc`` inactive →
        ``'S1'`` (homogeneous driving), and each active ``hrc_method`` → its
        heterogeneous scheme (S2..S6). Because nesspy 1.9.0 (2026-08-03) renamed
        the schemes, the mapping is done **per file** with the catalogue matching
        that file's own nesspy version banner; a folder written by a pre-1.9.0
        nesspy is reported on stdout together with the remapping applied. An
        ``hrc_method`` with no counterpart here raises ``NotImplementedError``.
        """

        def _as_bool(v):
            if isinstance(v, str):
                return v.strip().lower() == "true"
            return bool(v)

        fres_vals, dmu_vals, k_vals = set(), set(), set()
        jhom_vals, jhet_vals = set(), set()

        # Scheme detection is per file: the same physical scheme is numbered
        # differently before and after the nesspy 1.9.0 renaming, so a folder may
        # legitimately mix hrc_method=6.0 (legacy) and 5.0 (modern) and still be
        # one single scheme (S5). We therefore compare the *resolved* schemes.
        schemes: set[str] = set()
        legacy_examples: list[tuple] = []

        for f in self.files:
            _df = pd.read_csv(f, comment="#", skip_blank_lines=True)
            fres_vals.update(np.round(_df["fres"].unique(), 8))
            dmu_vals.update(np.round(_df["dmu"].unique(), 8))
            k_vals.update(np.round(_df["k"].unique(), 8))
            jhom_vals.add(round(get_epsilon(f), 8))
            jhet_vals.add(round(get_epsilon_het(f), 8))

            hrc_file = {_as_bool(v) for v in _df["hrc"].unique()}
            if len(hrc_file) != 1:
                raise ValueError(f"Inconsistent 'hrc' within {f}: {sorted(hrc_file)}")
            hrc = next(iter(hrc_file))

            # hrc_method only selects a scheme when hrc is active. For
            # homogeneous driving (hrc inactive) the note says it "can be any
            # float value", so we don't require consistency in that case.
            method_file = {
                float(v) for v in np.round(_df["hrc_method"].unique(), 8)
            }
            if hrc and len(method_file) != 1:
                raise ValueError(
                    f"Inconsistent 'hrc_method' within {f}: {sorted(method_file)}"
                )
            hrc_method = (
                next(iter(method_file)) if method_file else float("nan")
            )

            version = get_nesspy_version(f)
            scheme = scheme_from_hrc(
                hrc, hrc_method, legacy=version.legacy_schemes
            )
            schemes.add(scheme)
            if version.legacy_schemes:
                legacy_examples.append((version, hrc, hrc_method, scheme))

        for name, vals in [
            ("fres", fres_vals),
            ("dmu", dmu_vals),
            ("k", k_vals),
            ("jhom", jhom_vals),
            ("jhet", jhet_vals),
        ]:
            if len(vals) != 1:
                raise ValueError(
                    f"Inconsistent '{name}' across the {len(self.files)} out.csv "
                    f"files: {sorted(vals)}"
                )
        if len(schemes) != 1:
            raise ValueError(
                f"Inconsistent driving scheme across the {len(self.files)} "
                f"out.csv files: {sorted(schemes)}"
            )

        fres = float(next(iter(fres_vals)))
        dmu = float(next(iter(dmu_vals)))
        k = float(next(iter(k_vals)))
        jhom = float(next(iter(jhom_vals)))
        jhet = float(next(iter(jhet_vals)))
        method = next(iter(schemes))

        # Report the legacy remapping once for the whole run directory, in case
        # __init__ could not (an hrc_method it cannot map is only resolvable
        # here). Already-reported directories stay quiet.
        if legacy_examples:
            report_legacy_run(self.base_path, self.files)

        thermos = Thermos(
            jhom=jhom, jhet=jhet, fres=fres, dmu=dmu, k=k, method=method
        )
        logger.info(
            "Detected Thermos from files: jhom=%s, jhet=%s, fres=%s, dmu=%s, "
            "k=%s, method=%s (%s)",
            jhom, jhet, fres, dmu, k, method, scheme_description(method),
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
            try:
                self.df, header = read_csv(f, n_samples=1.0, bootstrap=False)
            except ValueError as e:
                # e.g. an out.csv for some mu that contains no measurement rows;
                # skip that mu and keep going so the run still analyzes.
                logger.warning("Skipping %s: %s", f, e)
                continue
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

    def get_cluster_observables(
        self,
        lb_frac: float = 0.2,
        ub_frac: float = 0.7,
        min_size: int = 8,
        tolerance: float = 0.01,
    ) -> pd.DataFrame:
        """Per-mu wrong-bond fraction <q> and normalized blue cluster size <r>.

        Walks every ``lattice_final.npy`` under each mu-named subfolder of
        ``base_path`` (in parallel) and computes two per-lattice observables over
        the column band ``[lb_frac, ub_frac] * Lx``:

        * ``q`` -- the fraction of 1-2 ("wrong") bonds, and
        * ``r`` -- the mean size of blue (value 2) 4-connected clusters with
          cardinality ``>= min_size``, normalized by the cropped lattice area.

        For each mu it reports the mean and SEM across lattices, so ``q``/``r``
        carry error bars (unlike the pooled fraction returned by :meth:`get_wq`).
        This disambiguates the ``m = 0`` regime: a truly mixed state has high
        ``q`` and small ``r``, whereas flopping finite domains keep ``q`` lower
        and ``r`` large. The ``q_mean``/``q_sem``/``r_mean``/``r_sem`` columns are
        merged onto ``self.data`` with a nearest-mu join (guarded by
        ``tolerance``) so they line up with ``dphi`` for q(log(S)) / r(log(S))
        plots.

        ``min_size`` is the minimum cluster cardinality kept (default 8; set to 5
        to reproduce the "larger than four" rule). Populates ``self.data``
        (running :meth:`get_data` first if needed) and caches the per-mu table on
        ``self.cluster_data``. Returns ``self.data``.
        """
        if self.data.empty:
            self.get_data()

        tasks = []
        for mu_folder in self.base_path.glob("*"):
            if not mu_folder.is_dir():
                continue
            try:
                mu_value = float(mu_folder.name)
            except ValueError:
                continue
            for filex in mu_folder.glob("**/lattice_final.npy"):
                tasks.append((mu_value, filex, lb_frac, ub_frac, min_size))

        if not tasks:
            raise ValueError(
                f"No lattice_final.npy files found under {self.base_path}"
            )

        logger.info(
            "Processing %d lattice files for cluster observables (min_size=%d)...",
            len(tasks), min_size,
        )
        with Pool() as pool:
            results = pool.map(_process_cluster_observables_file, tasks)

        # Group per-lattice values back by mu so we can average with a SEM.
        per_mu = {}  # mu_value -> ([q...], [r...])
        for mu_value, q_frac, r_norm in results:
            q_list, r_list = per_mu.setdefault(mu_value, ([], []))
            if not np.isnan(q_frac):
                q_list.append(q_frac)
            r_list.append(r_norm)

        records = []
        for mu_value in sorted(per_mu):
            q_vals, r_vals = per_mu[mu_value]
            records.append(
                {
                    "mu_value": mu_value,
                    "q_mean": np.mean(q_vals) if q_vals else np.nan,
                    "q_sem": sem(q_vals) if len(q_vals) > 1 else 0.0,
                    "r_mean": np.mean(r_vals) if r_vals else np.nan,
                    "r_sem": sem(r_vals) if len(r_vals) > 1 else 0.0,
                }
            )

        self.cluster_data = pd.DataFrame(records).sort_values(by="mu_value")

        self.data = pd.merge_asof(
            self.data.sort_values(by="mu"),
            self.cluster_data,
            left_on="mu",
            right_on="mu_value",
            direction="nearest",
            tolerance=tolerance,
        )
        self.data.drop(columns=["mu_value"], inplace=True)

        unmatched = self.data[self.data["q_mean"].isna()]
        if not unmatched.empty:
            logger.warning(
                "%d row(s) had no cluster-observable match within tolerance %s:\n%s",
                len(unmatched), tolerance, unmatched[["mu"]],
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

    def get_critical_supersat(self) -> list[float, float]:
        """Critical supersaturation (± error) from a sigmoidal fit of m vs log(S).

        Fits the order parameter ``m`` against the corrected logarithmic
        supersaturation ``dphi`` to a four-parameter logistic and returns its
        inflection point (the critical supersaturation) together with an error
        estimate. Requires :meth:`get_logarithmic_supersat_corrected` to have
        been run first.

        The reported error is a *sampling-resolution* estimate: the average of
        the distances from the inflection point ``x0`` to the nearest sampled
        ``dphi`` point above and below it. When ``x0`` lies between two sampled
        points this equals half the width of the bracketing interval, so densely
        sampled sweeps get a small error and sparse sweeps a large one. It
        captures how finely the transition was sampled, not the statistical
        scatter of the fit. If ``x0`` falls outside the sampled range (an
        extrapolated fit) only the one available side is used and a warning is
        logged.

        The complementary *statistical* error -- the standard error on x0 from
        ``curve_fit``'s covariance matrix (``sqrt(pcov[1, 1])``), which shrinks
        with clean/plentiful data rather than with grid density -- is also
        computed and cached on ``self.critical_supersat_cov_err`` (NaN if the fit
        is unconstrained), but is not the returned value.

        Caches the fit on ``self.sigmoid_params``, the value on
        ``self.critical_supersat``, the resolution error on
        ``self.critical_supersat_err`` and the covariance error on
        ``self.critical_supersat_cov_err``. Returns
        ``[value, resolution_error]``.
        """
        required = {"dphi", "m"}
        if self.data.empty or not required.issubset(self.data.columns):
            raise RuntimeError(
                "Run get_logarithmic_supersat_corrected() before get_critical_supersat()."
            )

        _df = self.data.dropna(subset=["dphi", "m"]).sort_values(by="dphi")
        popt, pcov = fit_sigmoid(_df["dphi"].values, _df["m"].values, return_cov=True)

        # popt = [L, x0, k, b]; the inflection point of the logistic is x0.
        self.sigmoid_params = popt
        x0 = float(popt[1])
        self.critical_supersat = x0

        # Statistical error on x0 from the fit covariance matrix (variance is the
        # [1, 1] entry). Guard against the unconstrained-fit case where curve_fit
        # returns inf/negative variances.
        var_x0 = pcov[1, 1]
        self.critical_supersat_cov_err = (
            float(np.sqrt(var_x0)) if np.isfinite(var_x0) and var_x0 >= 0
            else float("nan")
        )

        # Sampling-resolution error: mean distance from x0 to the nearest
        # sampled dphi on each side (strict </> so an x0 landing exactly on a
        # data point still measures the spacing to its neighbours).
        dphi_sorted = np.unique(_df["dphi"].values)
        below = dphi_sorted[dphi_sorted < x0]
        above = dphi_sorted[dphi_sorted > x0]
        if below.size and above.size:
            # x0 brackets two data points -> average of both gaps
            # (= half the bracketing interval width).
            err = 0.5 * ((above[0] - x0) + (x0 - below[-1]))
        elif above.size:
            # x0 sits below the sampled range: only an upper neighbour exists.
            logger.warning(
                "Inflection point %.6f is below the sampled dphi range; "
                "using one-sided (upper) spacing as its error.", x0
            )
            err = float(above[0] - x0)
        elif below.size:
            # x0 sits above the sampled range: only a lower neighbour exists.
            logger.warning(
                "Inflection point %.6f is above the sampled dphi range; "
                "using one-sided (lower) spacing as its error.", x0
            )
            err = float(x0 - below[-1])
        else:
            # Degenerate: a single unique dphi value, no spacing to measure.
            logger.warning("Only one unique dphi value; cannot estimate an error.")
            err = float("nan")
        self.critical_supersat_err = float(err)

        logger.info(
            "Critical supersaturation (inflection point): %.6f +- %.6f "
            "(resolution); +- %.6f (fit covariance)",
            self.critical_supersat, self.critical_supersat_err,
            self.critical_supersat_cov_err,
        )
        return [self.critical_supersat, self.critical_supersat_err]
