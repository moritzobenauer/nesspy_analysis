from pathlib import Path
from typing import NamedTuple
import pandas as pd
import numpy as np

import logging

from .schemes import (
    NESSPY_SCHEME_RENAME_DATE,
    NESSPY_SCHEME_RENAME_VERSION,
    is_legacy_scheme_numbering,
    legacy_scheme_name,
    parse_version_header,
    scheme_from_hrc,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_m_vals(file: Path) -> list[float, np.ndarray]:
    df = pd.read_csv(file, comment="#", header=0)
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(how="all")

    m_vals = df["m"].values

    mu = np.round(df["mu"].mean(), 4)

    return [mu, m_vals]


def get_data_point_from_out_file(file: Path, n_samples: int, bootstrap: bool=True) -> pd.DataFrame:

    df = pd.read_csv(file, comment="#", header=0)
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(how="all")

    # An out.csv with a header but no measurement rows leaves nothing to
    # aggregate; signal it so callers can skip this mu.
    if df.empty:
        raise ValueError(f"No measurement rows in {file}")

    if bootstrap:
        # df = df.sample(n_samples, random_state=np.random.randint(0, 10000), replace=True)
        df = df.sample(frac=n_samples, random_state=np.random.randint(0, 10000), replace=True)

    else:
        pass

    delta_f_value = df["fres"].mean()
    rate_constant = df["k"].mean()
    dmu = df["dmu"].mean()

    m_average = df["m"].mean()
    m_delta = df["m"].sem()

    m2_average = df["msquared"].mean()
    m2_delta = df["msquared"].sem()

    mu = df["mu"].mean()
    time_elapsed_average = df["gspeed"].mean()
    time_elapsed_delta = df["gspeed"].sem()

    rsw_values = df["rs_width"].unique()
    RSWDITH_CHECK: bool = False
    if len(rsw_values) > 1:
        logger.warning(
            "Multiple RSW values found in the data: %s. This may indicate inconsistent data.",
            rsw_values,
        )
    else:
        RSWDITH_CHECK = True
    rsw = rsw_values[0]

    # Calculate susceptibility

    # susc_rows = df["msquared"] - df["m"]**2
    # susc_error = susc_rows.sem()
    # print(susc_error)

    susc = m2_average - m_average**2

    if np.isnan(m_average):
        print(file)
        raise ValueError

    dic = {
        "m": m_average,
        "dm": m_delta,
        "mu": mu,
        "t": time_elapsed_average,
        "dt": time_elapsed_delta,
        "df": delta_f_value,
        "k": rate_constant,
        "m2": m2_average,
        "dm2": m2_delta,
        "dmu": dmu,
        "susc": susc,
        "rsw": rsw,
        "rsw_check": RSWDITH_CHECK,
        # "susc_delta": susc_error,
    }
    out = pd.DataFrame(dic, index=[0])
    return out


def get_lattice_dimensions(file: Path) -> list[int]:
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("# ysize"):
                ydim = float(line.split(":")[1].strip())
            elif line.startswith("# xsize"):
                xdim = float(line.split(":")[1].strip())
            else:
                continue
        return [int(xdim), int(ydim), int(xdim * ydim)]


def get_epsilon(file: Path) -> float:
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("# jhom"):
                epsilon = float(line.split(":")[1].strip())
                return epsilon
    return None


def get_epsilon_het(file: Path) -> float:
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("# jhet"):
                epsilon = float(line.split(":")[1].strip())
                return epsilon
    return None



def get_df(file: Path) -> float:
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("# fres"):
                epsilon = float(line.split(":")[1].strip())
                return epsilon
    return None


def get_dmu(file: Path) -> float:
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("# drive"):
                dmu = float(line.split(":")[1].strip())
                return dmu
    return None


def get_k(file: Path) -> float:
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("# rate"):
                k = float(line.split(":")[1].strip())
                return k
    return None


# ---------------------------------------------------------------------------
# nesspy version / driving-scheme provenance.
#
# The meaning of the `hrc_method` number in an out.csv changed with nesspy 1.9.0
# (2026-08-03), which renamed the driving schemes to the manuscript convention
# S1-S6. Every file states the nesspy release that wrote it in its banner, so we
# read that banner and interpret `hrc_method` with the matching catalogue. See
# schemes.py for both catalogues.
# ---------------------------------------------------------------------------


class NesspyVersion(NamedTuple):
    """The ``# nesspy Version ...`` banner of one out.csv."""

    version: str | None       # e.g. "1.4.1", None if the banner is missing
    release_date: object      # datetime.date, or None if not stated
    legacy_schemes: bool      # True -> hrc_method uses the pre-1.9.0 catalogue


def get_nesspy_version(file: Path) -> NesspyVersion:
    """Read the nesspy version banner from an out.csv header.

    Files with no banner at all (very old output) are reported as legacy, which
    is the safe assumption: the manuscript scheme numbering is newer than the
    banner itself.
    """
    with open(file, "r") as f:
        for line in f:
            if not line.startswith("#"):
                # The header block is contiguous and precedes the data rows, so
                # there is nothing left to find once it ends.
                break
            parsed = parse_version_header(line)
            if parsed is not None:
                version, release_date = parsed
                return NesspyVersion(
                    version=version,
                    release_date=release_date,
                    legacy_schemes=is_legacy_scheme_numbering(version, release_date),
                )
    return NesspyVersion(version=None, release_date=None, legacy_schemes=True)


def is_legacy_output(file: Path) -> bool:
    """Whether ``file`` was written before the nesspy 1.9.0 scheme renaming."""
    return get_nesspy_version(file).legacy_schemes


def get_hrc(file: Path) -> tuple[bool, float] | None:
    """Read the ``# hrc`` / ``# hrc_method`` header entries of an out.csv.

    Returns ``(hrc_active, hrc_method)``, or ``None`` when the header does not
    state them (output from before heterogeneous driving existed).
    """
    hrc: bool | None = None
    hrc_method: float | None = None
    with open(file, "r") as f:
        for line in f:
            if not line.startswith("#") or ":" not in line:
                continue
            # Compare the key exactly: "# hrc_method" also starts with "# hrc".
            key, _, value = line.lstrip("#").partition(":")
            key = key.strip()
            if key == "hrc" and hrc is None:
                hrc = value.strip().lower() == "true"
            elif key == "hrc_method" and hrc_method is None:
                hrc_method = float(value.strip())
    if hrc is None or hrc_method is None:
        return None
    return (hrc, hrc_method)


# Directories we have already reported as legacy, so a sweep over dozens of mu
# subfolders prints one line per run instead of one per file.
_LEGACY_NOTICES: set[Path] = set()


def reset_legacy_notices() -> None:
    """Forget which directories were already reported (used by the tests)."""
    _LEGACY_NOTICES.clear()


def notify_legacy_schemes(directory: Path, message: str) -> bool:
    """Print ``message`` to stdout once per directory subtree.

    A notice for a parent directory suppresses the notices of everything below
    it, so ``DynamicalOrderDisorder`` reporting its whole run directory keeps
    the individual per-mu folders quiet. Returns whether it printed.
    """
    directory = Path(directory).resolve()
    if directory in _LEGACY_NOTICES:
        return False
    if any(parent in _LEGACY_NOTICES for parent in directory.parents):
        return False
    _LEGACY_NOTICES.add(directory)
    print(message)
    return True


def describe_legacy_remap(
    version: NesspyVersion,
    hrc: bool | None = None,
    hrc_method: float | None = None,
    scheme: str | None = None,
) -> str:
    """One-line description of the scheme remapping applied to legacy output.

    The concrete ``(hrc, hrc_method) -> scheme`` remapping is appended when it is
    known; without it the message just states that the legacy catalogue is in use.
    """
    written_by = (
        f"nesspy {version.version}"
        + (f", released {version.release_date:%Y/%m/%d}" if version.release_date else "")
        if version.version
        else "an unversioned nesspy release"
    )
    rename = ".".join(str(v) for v in NESSPY_SCHEME_RENAME_VERSION)
    message = (
        f"written by {written_by}, i.e. before the scheme renaming in nesspy "
        f"{rename} ({NESSPY_SCHEME_RENAME_DATE:%Y/%m/%d}). "
    )
    if scheme is None:
        return message + "hrc_method is read with the legacy scheme catalogue"
    return message + (
        f"Remapped legacy hrc={hrc}, hrc_method={hrc_method} -> {scheme} "
        f"(previously called {legacy_scheme_name(scheme)!r})"
    )


def report_legacy_run(directory: Path, files) -> bool:
    """Announce once, for a whole run directory, that its out.csv files are legacy.

    Called when a :class:`DynamicalOrderDisorder` is built so that the notice is
    printed once for the run rather than once per mu subfolder (the notice for a
    directory suppresses everything below it). Returns whether it printed.

    Scheme resolution here is best-effort: an ``hrc_method`` this package cannot
    map still gets a notice, and the ``NotImplementedError`` is raised later by
    ``get_thermos_from_file()``, which is where it belongs.
    """
    legacy = [
        (f, version)
        for f, version in ((f, get_nesspy_version(f)) for f in files)
        if version.legacy_schemes
    ]
    if not legacy:
        return False

    file, version = legacy[0]
    hrc_entries = get_hrc(file)
    hrc = hrc_method = scheme = None
    if hrc_entries is not None:
        hrc, hrc_method = hrc_entries
        try:
            scheme = scheme_from_hrc(hrc, hrc_method, legacy=True)
        except NotImplementedError:
            scheme = None

    return notify_legacy_schemes(
        directory,
        f"[nesspy_analysis] Legacy nesspy output in {directory} "
        f"({len(legacy)}/{len(files)} out.csv files): "
        + describe_legacy_remap(version, hrc, hrc_method, scheme)
        + ".",
    )


def report_legacy_output(file: Path, directory: Path | None = None) -> str | None:
    """Announce, once per directory, that out.csv files there use legacy schemes.

    Returns the canonical scheme the legacy ``(hrc, hrc_method)`` pair maps onto,
    or ``None`` when ``file`` is not legacy output (or states no hrc entries, so
    there is no scheme numbering to remap).
    """
    version = get_nesspy_version(file)
    if not version.legacy_schemes:
        return None

    hrc_entries = get_hrc(file)
    if hrc_entries is None:
        return None

    hrc, hrc_method = hrc_entries
    scheme = scheme_from_hrc(hrc, hrc_method, legacy=True)
    directory = Path(directory) if directory is not None else Path(file).parent
    notify_legacy_schemes(
        directory,
        f"[nesspy_analysis] Legacy nesspy output in {directory}: "
        + describe_legacy_remap(version, hrc, hrc_method, scheme)
        + ".",
    )
    return scheme


def read_csv(file: Path, n_samples: int=6, bootstrap: bool=True) -> tuple[pd.DataFrame, dict]:
    if not file.exists():
        raise ValueError(f"File {file} does not exist.")

    # Get the header information from the CSV file

    lattice = get_lattice_dimensions(file)
    epsilon = get_epsilon(file)
    epsilon_het = get_epsilon_het(file)
    fres = get_df(file)
    k = get_k(file)
    dmu = get_dmu(file)

    # Driving-scheme provenance: legacy files (nesspy < 1.9.0) number their
    # schemes with the old catalogue, so the (hrc, hrc_method) pair is remapped
    # onto the canonical S0-S6 naming and the remapping is reported once per
    # directory.
    version = get_nesspy_version(file)
    scheme = report_legacy_output(file)
    if scheme is None:
        # Either modern output or a file that states no hrc entries at all.
        hrc_entries = get_hrc(file)
        scheme = (
            scheme_from_hrc(*hrc_entries, legacy=version.legacy_schemes)
            if hrc_entries is not None
            else None
        )

    # Read the CSV file into a DataFrame

    try:

        data_points = get_data_point_from_out_file(file, n_samples, bootstrap=bootstrap)

    except ValueError as e:
        # An empty out.csv (no measurement rows) leaves data_points unbound and
        # cannot be analyzed; re-raise with context so callers can skip this mu.
        raise ValueError(f"No usable data in file {file}: {e}") from e

    if data_points["rsw_check"].values.any() == False:
        raise ValueError(f"RSW values are not consistent in file {file}")
    

    # 2026-01-16: The growth speed per lattice site is calculated as follows
    # <v> = 1/(<t>*D) * 2 * L_y^2

    data_points['growth_speed'] =lattice[1]**2 * 2 * 1./ data_points['t']

    # Gaussian error propagation: Δ<v> = |d<v>/d<t>| * Δ<t> = (1/D) * 2 * L_y^2 * (1/t^2) * Δ<t>

    data_points['dgrowth_speed'] = lattice[1]**2 * 2 * (1./data_points['t']**2) * data_points['dt']

    # data_points['growth_speed'] = (1./data_points['t'])*0.5*lattice[0]

    # Double check that the k, df, and dmu values match those from the header

    if not np.isclose(data_points["k"].values[0], k):
        raise ValueError(f"k value in file {file} does not match header value.")
    if not np.isclose(data_points["df"].values[0], fres):
        raise ValueError(f"df value in file {file} does not match header value.")
    if not np.isclose(data_points["dmu"].values[0], dmu):
        raise ValueError(f"dmu value in file {file} does not match header value.")

    header_info = {
        "lattice_x": lattice[0],
        "lattice_y": lattice[1],
        "lattice_size": lattice[2],
        "jhom": epsilon,
        "jhet": epsilon_het,
        "fres": fres,
        "k": k,
        "dmu": dmu,
        # Provenance: which nesspy wrote the file, whether its hrc_method
        # numbering is the legacy one, and the canonical scheme it maps onto.
        "nesspy_version": version.version,
        "legacy_schemes": version.legacy_schemes,
        "scheme": scheme,
    }

    return (data_points, header_info)
