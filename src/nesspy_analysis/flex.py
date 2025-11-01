import numpy as np
from .classes import Thermos

def calculate_dphi(mu: np.array, thermos: Thermos, 
                              drivetype: str="NODRIVE") -> np.array:
    jhom = thermos.jhom
    dmu = thermos.dmu
    fres = thermos.fres
    beta = thermos.beta
    if drivetype == "NODRIVE":
        return np.zeros_like(mu)
    elif drivetype == "HOMO":
        return np.zeros_like(mu)
    elif drivetype == "SCHEME_7":
        return np.zeros_like(mu)
    else:
        raise ValueError(f"Unknown drivetype: {drivetype}")