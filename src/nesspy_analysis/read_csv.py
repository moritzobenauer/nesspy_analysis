from pathlib import Path
import pandas as pd
import numpy as np


def get_data_point_from_out_file(file: Path, n_samples: int, bootstrap: bool=True) -> pd.DataFrame:

    df = pd.read_csv(file, comment="#", header=0)
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(how="all")

    if bootstrap:
        df = df.sample(n_samples, random_state=np.random.randint(0, 10000), replace=True)
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


def read_csv(file: Path, n_samples: int=6, bootstrap: bool=True) -> tuple[pd.DataFrame, dict]:
    if not file.exists():
        raise ValueError(f"File {file} does not exist.")

    # Get the header information from the CSV file

    lattice = get_lattice_dimensions(file)
    epsilon = get_epsilon(file)
    fres = get_df(file)
    k = get_k(file)
    dmu = get_dmu(file)

    # Read the CSV file into a DataFrame


    data_points = get_data_point_from_out_file(file, n_samples, bootstrap=bootstrap)
    


    data_points['growth_speed'] = (1./data_points['t'])*0.5*lattice[0]

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
        "epsilon": epsilon,
    }

    return (data_points, header_info)
