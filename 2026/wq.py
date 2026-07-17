import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from multiprocessing import Pool
import nesspy_analysis as npa


def get_steady_state_probabilities_numerical(epsilon_homo, epsilon_hetero, mu, F, M, k, environment,
                                             scheme='HOMO'):

    n_red, n_blue = environment

    U_red = np.exp(n_red*epsilon_homo + n_blue*epsilon_hetero)
    U_blue = np.exp(n_red*epsilon_hetero + n_blue*epsilon_homo)
    z = np.exp(mu)

    if scheme=='HOMO':
        k = 1.0
    elif scheme=='SCHEME91':
        k = k*np.exp(-(n_red+n_blue))
    elif scheme=='SCHEME93':
        k = k*np.exp(-np.abs(n_red-n_blue))

    elif scheme=='SCHEME6':
        dmu0 = np.log(M)

        M = np.exp(dmu*np.exp(-np.abs(n_red-n_blue)))

    # Set up the generator matrix

    L = np.array([
    [-2*(z + z*F), z, z*F, z, z*F],
    [U_red, -U_red-U_red*k*F*M, U_red*k*F*M, 0, 0],
    [1.0, k, -(k + 1), 0, 0],
    [U_blue, 0.0, 0.0, -U_blue*(1+F*M*k), U_blue*F*M*k],
    [1.0, 0.0, 0.0, k, -(1+k)]
], dtype=np.float64)
    Q = L.T
    evals, evecs = np.linalg.eig(Q)
    evals = np.round(evals, decimals=10)
    evecs = np.round(evecs, decimals=10)
    # Sort eigenvalues and eigenvectors by eigenvalue
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]

    # print("Eigenvalues:", evals)

    # Make sure the first eigenvector is positive
    if evecs[0, 0] < 0:
        evecs[:, 0] = -evecs[:, 0]
    # The stationary distribution is the eigenvector associated with eigenvalue 0
    pi = evecs[:, 0] / np.sum(evecs[:, 0])
    # print("Stationary distribution:", pi)


    p_empty, p_red_active, p_red_inactive, p_blue_active, p_blue_inactive = pi[0], pi[1], pi[2], pi[3], pi[4]

    p_active = p_red_active + p_blue_active
    p_non_bonding = p_blue_inactive + p_red_inactive + p_empty

    return p_active, p_non_bonding


def get_nns(lattice: np.array, x: int, y: int):
   
    NY, NX = lattice.shape

    nnl = [[(y + 1) % NY, x], [(y - 1) % NY, x], [y, (x + 1) % NX], [y, (x - 1) % NX]]
    nns = np.array([lattice[index[0], index[1]] for index in nnl])

    active_site = lattice[y, x]

    # Count how many 1-1, 2-2, 1-2 bonds there are

    neighbors_red = np.sum(nns == 1)
    neighbors_blue = np.sum(nns == 2)

    # Count the number of each type of bond
    pairs_11 = np.sum((nns == 1) & (active_site == 1))
    pairs_22 = np.sum((nns == 2) & (active_site == 2))
    pairs_12 = np.sum((nns == 1) & (active_site == 2)) + np.sum((nns == 2) & (active_site == 1))

    return (pairs_11, pairs_22, pairs_12)


def get_wq(lattice: np.array):
    pairs_11_total = 0
    pairs_22_total = 0
    pairs_12_total = 0
    number_ones_total = 0
    number_twos_total = 0

    for y in range(lattice.shape[0]):
        for x in range(lattice.shape[1]):

            pairs_11, pairs_22, pairs_12 = get_nns(lattice, x, y)
            pairs_11_total += pairs_11
            pairs_22_total += pairs_22
            pairs_12_total += pairs_12
            number_ones_total += np.sum(lattice[y, x] == 1)
            number_twos_total += np.sum(lattice[y, x] == 2)

    return pairs_11_total, pairs_22_total, pairs_12_total, number_ones_total, number_twos_total

def process_file(args):
    """Read one lattice_final.npy file and return its w(q) contributions.

    Runs in a worker process, so it must be a top-level (picklable) function
    and take a single argument. Returns (mu_value, pairs_11, pairs_22, pairs_12,
    number_ones, number_twos).
    """
    mu_value, filex = args
    lattice = np.load(filex)
    Lx = lattice.shape[1]
    lattice_cropped = lattice[:, int(0.2 * Lx):int(0.7 * Lx)]
    pairs_11, pairs_22, pairs_12, number_ones, number_twos = get_wq(lattice_cropped)
    return mu_value, pairs_11, pairs_22, pairs_12, number_ones, number_twos


data_dic = {'mu_value': [], 'wq_11': [], 'wq_22': [], 'wq_12': []}

parent_dir = Path("/Volumes/2025/2026_paper/COMPARING_SCHEMES/SCHEME6/D05")


if __name__ == "__main__":


    fres=0.0
    dmu=0.5
    epsilon_homo = -3.5
    epsilon_hetero = -2.0
    k=1.0
    SCHEME='SCHEME6'
    F = np.exp(fres)
    M = np.exp(dmu)

    analysis = npa.DynamicalOrderDisorder('test', parent_dir)
    thermos = npa.Thermos(jhom=epsilon_homo, jhet=epsilon_hetero,fres=fres, dmu=dmu, k=k, method=SCHEME)
    data = analysis.get_data()
    data["dphi_legacy"] = npa.calculate_dphi(data["mu"], thermos)

    data = data.sort_values(by=["mu"])
    print(data)

    # Build a flat list of (mu_value, file) tasks across all mu folders so a
    # single pool can balance the work evenly across CPUs.
    tasks = []
    for mu_folder in parent_dir.glob("*"):
        if mu_folder.is_dir():
            mu_value = float(mu_folder.name)
            for filex in mu_folder.glob("**/lattice_final.npy"):
                tasks.append((mu_value, filex))

    print(f"Processing {len(tasks)} lattice files in parallel...")
    with Pool() as pool:
        results = pool.map(process_file, tasks)

    # Aggregate per-file results back by mu_value.
    totals = {}  # mu_value -> [p11, p22, p12, n_ones, n_twos]
    for mu_value, p11, p22, p12, n_ones, n_twos in results:
        acc = totals.setdefault(mu_value, [0, 0, 0, 0, 0])
        acc[0] += p11
        acc[1] += p22
        acc[2] += p12
        acc[3] += n_ones
        acc[4] += n_twos

    for mu_value in sorted(totals):
        pairs_11_total_x, pairs_22_total_x, pairs_12_total_x, number_ones_total_x, number_twos_total_x = totals[mu_value]
        total_bonds_x = pairs_11_total_x + pairs_22_total_x + pairs_12_total_x

        # actually calculate a normalized probability distribution w(q)
        wq_11 = pairs_11_total_x / total_bonds_x
        wq_22 = pairs_22_total_x / total_bonds_x
        wq_12 = pairs_12_total_x / total_bonds_x
        print(f"mu: {mu_value:.2f} - w(q) for 1-1 bonds: {wq_11:.4f}, w(q) for 2-2 bonds: {wq_22:.4f}, w(q) for 1-2 bonds: {wq_12:.4f}")
        data_dic['mu_value'].append(mu_value)
        data_dic['wq_11'].append(wq_11)
        data_dic['wq_22'].append(wq_22)
        data_dic['wq_12'].append(wq_12)

    df = pd.DataFrame(data_dic)
    df.sort_values(by='mu_value', inplace=True)
    print(df)

    # Combine the calculated w(q) values with the existing data frame on mu.
    # An exact/rounded equality join is fragile: data["mu"] is the *mean* of
    # the simulation's recorded mu column, which can drift slightly from the
    # mu_folder-derived value used on the wq side. mu values are spaced 0.05
    # apart, so a nearest-match join with a much smaller tolerance is robust
    # to that drift while still refusing to match the wrong mu bucket.
    data = pd.merge_asof(
        data.sort_values(by="mu"),
        df.sort_values(by="mu_value"),
        left_on="mu",
        right_on="mu_value",
        direction="nearest",
        tolerance=0.01,
    )
    data.drop(columns=["mu_value"], inplace=True)

    unmatched = data[data["wq_11"].isna()]
    if not unmatched.empty:
        print(f"Warning: {len(unmatched)} row(s) had no wq match within tolerance:")
        print(unmatched[["mu"]])


    dphi_by_mu = {}
    for mu in data["mu"].unique():
        row = data[data["mu"] == mu].iloc[0]
        wq_red_red = row["wq_11"]
        wq_blue_blue = row["wq_22"]
        wq_red_blue = row["wq_12"]

        print(f"mu: {mu:.2f} - w(q) for 1-1 bonds: {wq_red_red:.4f}, w(q) for 2-2 bonds: {wq_blue_blue:.4f}, w(q) for 1-2 bonds: {wq_red_blue:.4f}")

        environments = [(2,0), (1,1), (0,2)]
        w_q_vector = [wq_red_red, wq_red_blue, wq_blue_blue]

        partition_function_active = 0.0
        partition_function_inactive = 0.0

        for env, wq in zip(environments, w_q_vector):

            # based on the scheme, k has to change as a function of the environment

            # get steady state probabilities for this environment
            p_a, p_n = get_steady_state_probabilities_numerical(
                epsilon_homo, epsilon_hetero, mu, F, M, k, env, scheme=SCHEME
            )
            print(p_a, p_n)

            partition_function_active += wq * p_a
            partition_function_inactive += wq * p_n

        # print(partition_function_active, partition_function_inactive)
        # dphi = log(S) = log(partition_function_active / partition_function_inactive)
        dphi = np.log(partition_function_active / partition_function_inactive)
        dphi_by_mu[mu] = dphi

    # attach dphi values (one per mu) to the data frame
    data["dphi"] = data["mu"].map(dphi_by_mu)

    data.to_csv(Path(parent_dir / "analysis_with_wq_values.csv"), index=False)

    plt.errorbar(data['dphi'], data['m'], yerr=data['dm'], fmt='o', capsize=5, label=r'Exact $w(q)$ method')
    plt.errorbar(data['dphi_legacy'], data['m'], yerr=data['dm'], fmt='s', capsize=5, label='Legacy Method')
    plt.legend()
    plt.savefig(Path(parent_dir / "dphi_plot.png"))