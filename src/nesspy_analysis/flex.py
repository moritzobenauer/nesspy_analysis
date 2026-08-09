import numpy as np
from .classes import Thermos
from .schemes import canonical_scheme


def calculate_dphi(
    mu: np.array, thermos: Thermos
) -> np.array:
    jhom = thermos.jhom
    jhet = thermos.jhet
    dmu = thermos.dmu
    fres = thermos.fres
    k = thermos.k
    beta = thermos.beta
    # Canonical scheme name (S0-S6); Thermos already normalises this, but accept
    # a hand-built object carrying a legacy spelling too.
    drivetype = canonical_scheme(thermos.method)

    def exact_phi(
        mu: np.array, jhom, jhet, dmu, fres, k, beta: float = 1.0
    ) -> np.array:
        """
        🔎 Exact solution for the undriven case
        """

        mu_coex = 2*jhom
        F = np.exp(fres)
        z = np.exp(mu)
        z_holes = np.exp(-mu+4*jhom)

        return ((mu - mu_coex) + np.log((1+2*z_holes+2*F*np.exp(4*jhom))/(1+2*z+2*z*F)))

    def flex_phi(mu: np.array, jhom, jhet, dmu, fres, k, beta: float = 1.0) -> np.array:
        """
        🚀 FLEX solution for the driven case
        """

        z = np.exp(mu)
        F = np.exp(fres)
        M = np.exp(dmu)
        return (mu-2*jhom)+np.log((1+k+k*F)/(1+k+2*z*F+k*F*M+2*F**2*M*k*z+2*F*M*k*z))

    # The FLEX branches evaluate each scheme's perturbation at the mean-field
    # environment of two nearest neighbours, which is why the rescalings below
    # are plain numbers rather than functions of (n_red, n_blue).
    if drivetype == "S0":
        # Undriven / equilibrium reference: exact solution, no drive.
        return exact_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "S1":
        # Homogeneous driving: k and dmu used as read.
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype in ("S2", "S3"):
        # k-family schemes: k -> k * exp(-2) at two neighbours.
        k = k * np.exp(-2.0)
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype in ("S4", "S5", "S6"):
        # dmu-family schemes: dmu -> dmu * exp(-2) at two neighbours. All three
        # are the same exponential suppression driven by a different neighbour
        # count (N, |n_red - n_blue| and the likewise count n' respectively),
        # and those counts coincide at this mean-field environment.
        #
        # BUGFIX 2026-08-05 S6 was evaluated with the linear form
        # dmu_0 * (1 - n'/4), i.e. dmu / 2 at n' = 2. That form is wrong: S6 is
        # exponential in n' (nesspy/src/hrc.py, hrc_method 6.0), which is what
        # classes.get_steady_state_probabilities_numerical() also implements.
        dmu = dmu * np.exp(-2.0)
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    else:
        raise ValueError(f"Unknown driving scheme: {drivetype}")
