This file is supposed to be a markdown lookup table to implement the functionality to analyze heterogeneous driving scheme. There is a general missmatch of nomenclature and we need to be sure to be consistent:


Based on the scheme, the local rate $k$ or $\Delta \mu$ changes as a function of the nearest neighbors. This is important for any supersaturation calculations, e.g.

Here is an overview:

# Homogeneous Driving

This is the easiest case, where $k \neq 0$, $\Delta \mu \neq 0$. This corresponds to a non-equilibrium steady state, but the values read from the data set for $k$ and $\Delta \mu$ can be used as is. In the data sets this is indicated by having the `HRC` entry in the `out.csv` files set to `False`. The `hrc_method` can be any float value. Whenever you refer to this scheme, call it $\mathcal{S}1$ in plots or "homogeneous driving" in text. 

# HRC Method 91.0

This changes the base rate $k$ as a function of the sum of local nearest neighbors. It leaves $\Delta \mu$ unchanged. In the `out.csv` files this is indicated with the `hrc` column set to `True` and `hrc_method` set to `91.0`. Refer to this scheme as $\mathcal{S}2$.

```
elif scheme == "SCHEME91":
        k = k * np.exp(-(n_red + n_blue))
```


# HRC Method 93.0

This changes the base rate $k$ as a function of the absolute difference of local nearest neighbors. It leaves $\Delta \mu$ unchanged. In the `out.csv` files this is indicated with the `hrc` column set to `True` and `hrc_method` set to `93.0`. Refer to this scheme as $\mathcal{S}3$.

```
elif scheme == "SCHEME93":
        k = k * np.exp(-np.abs(n_red - n_blue))
```
# HRC Method 3.0

This changes the chemical drive $\Delta \mu$ as a function of the absolute sum of local nearest neighbors. It leaves $k$ unchanged. In the `out.csv` files this is indicated with the `hrc` column set to `True` and `hrc_method` set to `3.0`. Refer to this scheme as $\mathcal{S}4$.

```
elif scheme == "SCHEME3":
        dmu = dmu_0 * np.exp(-np.abs(n_red + n_blue))
```

# HRC Method 6.0

This changes the chemical drive $\Delta \mu$ as a function of the absolute difference of local nearest neighbors. It leaves $k$ unchanged. In the `out.csv` files this is indicated with the `hrc` column set to `True` and `hrc_method` set to `6.0`. Refer to this scheme as $\mathcal{S}5$.

```
elif scheme == "SCHEME6":
        dmu = dmu_0 * np.exp(-np.abs(n_red - n_blue))
```

# HRC Method 7.0

This changes the chemical drive $\Delta \mu$ as a function of the absolute difference of local nearest neighbors but conditioned on the color of the lattice site in question. It leaves $k$ unchanged. In the `out.csv` files this is indicated with the `hrc` column set to `True` and `hrc_method` set to `7.0`. Refer to this scheme as $\mathcal{S}6$.

```
elif scheme == "SCHEME7":
        dmu_blue = dmu_0 * np.exp(-np.abs(n_red)) # if the particle is blue
        dmu_red  = dmu_0 * np.exp(-np.abs(n_blue)) # if the particle is red
```


Summary:

Nomenclature in the `out.csv` file --> New nomenclature

`hrc=False` --> $\mathcal{S}1$
`hrc=True, hrc_method=91.0` --> $\mathcal{S}2$
`hrc=True, hrc_method=93.0` --> $\mathcal{S}3$
`hrc=True, hrc_method=3.0` --> $\mathcal{S}4$
`hrc=True, hrc_method=6.0` --> $\mathcal{S}5$
`hrc=True, hrc_method=7.0` --> $\mathcal{S}6$