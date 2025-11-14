import numpy as np
from .classes import Thermos


def calculate_dphi(
    mu: np.array, thermos: Thermos
) -> np.array:
    jhom = thermos.jhom
    jhet = thermos.jhet
    dmu = thermos.dmu
    fres = thermos.fres
    k = thermos.k
    beta = thermos.beta
    drivetype = thermos.method  

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

    if drivetype == "NODRIVE":
        return exact_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "HOMO":
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "SCHEME_3" or drivetype == "SCHEME3":
        dmu = dmu * np.exp(-2.0)
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "SCHEME_6" or drivetype == "SCHEME6":
        dmu = dmu * np.exp(-2.0)
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "SCHEME_7" or drivetype == "SCHEME7":
        dmu = dmu / 2.0
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "SCHEME_91" or drivetype == "SCHEME91":
        k = k * np.exp(-2.0)
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    elif drivetype == "SCHEME_93" or drivetype == "SCHEME93":
        k = k * np.exp(-2.0)
        return flex_phi(mu, jhom, jhet, dmu, fres, k, beta)
    else:
        raise ValueError(f"Unknown driving scheme: {drivetype}")
