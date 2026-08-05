This file is the markdown lookup table for the heterogeneous driving schemes. There used to be a
general mismatch of nomenclature between `nesspy` and the analysis code; the naming below is now the
single convention used by both.

Based on the scheme, the local rate $k$ or $\Delta \mu$ changes as a function of the nearest
neighbors. This is important for any supersaturation calculations, e.g.

**Naming.** Every scheme is called $\mathcal{S}0$ ... $\mathcal{S}6$, in plots and in text, and the
canonical strings in the code are `"S0"` ... `"S6"` (see `src/nesspy_analysis/schemes.py`). The
pre-rename spellings (`NODRIVE`, `HOMO`, `SCHEME91`, `SCHEME_3`, ...) are still accepted as aliases
and normalised on the way in, so old scripts and notebooks keep working.

**Reading a scheme out of an `out.csv`.** A scheme is encoded by the pair (`hrc`, `hrc_method`).
`nesspy 1.9.0` (released 2026-08-03) renamed the schemes, which **changed the meaning of the
`hrc_method` number**: legacy `6.0` is $\mathcal{S}5$ while modern `6.0` is $\mathcal{S}6$.
`nesspy_analysis` therefore reads the `# nesspy Version ...` banner of each file and picks the
matching catalogue; a folder written by a pre-1.9.0 nesspy is announced on stdout together with the
remapping that was applied.

# $\mathcal{S}0$ — No Driving

The undriven / equilibrium reference: $k = 0$, $\Delta \mu = 0$, solved exactly rather than through
FLEX. This is an analysis-only concept — it has no `hrc_method` number, since a nesspy run without a
drive is simply a run with $k = 0$. Refer to it as $\mathcal{S}0$ or "undriven" in text.

# $\mathcal{S}1$ — Homogeneous Driving

This is the easiest case, where $k \neq 0$, $\Delta \mu \neq 0$. This corresponds to a
non-equilibrium steady state, but the values read from the data set for $k$ and $\Delta \mu$ can be
used as is. In the data sets this is indicated by having the `hrc` entry in the `out.csv` files set
to `False` (any `hrc_method` float), or by `hrc = True` with the modern `hrc_method = 1.0`, which is
the identity perturbation. Whenever you refer to this scheme, call it $\mathcal{S}1$ in plots or
"homogeneous driving" in text.

# $\mathcal{S}2$ — modern `hrc_method` 2.0, legacy 91.0

This changes the base rate $k$ as a function of the sum of local nearest neighbors. It leaves
$\Delta \mu$ unchanged.

```
k = k * np.exp(-(n_red + n_blue))
```

# $\mathcal{S}3$ — modern `hrc_method` 3.0, legacy 93.0

This changes the base rate $k$ as a function of the absolute difference of local nearest neighbors.
It leaves $\Delta \mu$ unchanged.

```
k = k * np.exp(-np.abs(n_red - n_blue))
```

# $\mathcal{S}4$ — modern `hrc_method` 4.0, legacy 3.0

This changes the chemical drive $\Delta \mu$ as a function of the absolute sum of local nearest
neighbors. It leaves $k$ unchanged.

```
dmu = dmu_0 * np.exp(-np.abs(n_red + n_blue))
```

# $\mathcal{S}5$ — modern `hrc_method` 5.0, legacy 6.0

This changes the chemical drive $\Delta \mu$ as a function of the absolute difference of local
nearest neighbors. It leaves $k$ unchanged.

```
dmu = dmu_0 * np.exp(-np.abs(n_red - n_blue))
```

# $\mathcal{S}6$ — modern `hrc_method` 6.0, legacy 7.0

This changes the chemical drive $\Delta \mu$ as a function of the likewise-neighbour count
$\mathcal{N}'$, i.e. conditioned on the color of the lattice site in question. It leaves $k$
unchanged.

```
dmu_blue = dmu_0 * np.exp(-np.abs(n_red)) # if the particle is blue
dmu_red  = dmu_0 * np.exp(-np.abs(n_blue)) # if the particle is red
```

The exponential form is the definition of $\mathcal{S}6$ — it is what both `flex.py` (as
$\Delta \mu \exp\{-2\}$ at the mean-field $\mathcal{N}' = 2$) and
`get_steady_state_probabilities_numerical()` use.

> [!NOTE]
> `nesspy` itself used the linear form $\Delta \mu_0 (1 - \mathcal{N}'/4)$ for $\mathcal{S}6$ until
> **2026-08-04** (nesspy 1.9.1), so $\mathcal{S}6$ runs written before that date — i.e. all legacy
> `hrc_method = 7.0` data — were *generated* with the linear kernel while the theory here models the
> exponential. The linear form was wrong, so this is the right comparison to make, but it is worth
> remembering when an old $\mathcal{S}6$ data set and the theory curve disagree.

Summary:

Nomenclature in the `out.csv` file --> New nomenclature

| `hrc` | `hrc_method` (nesspy >= 1.9.0) | `hrc_method` (nesspy < 1.9.0) | scheme |
|---|---|---|---|
| `False` | any | any | $\mathcal{S}1$ |
| `True` | `1.0` | — (was allosteric, no equivalent) | $\mathcal{S}1$ |
| `True` | `2.0` | `91.0` | $\mathcal{S}2$ |
| `True` | `3.0` | `93.0` | $\mathcal{S}3$ |
| `True` | `4.0` | `3.0` | $\mathcal{S}4$ |
| `True` | `5.0` | `6.0` | $\mathcal{S}5$ |
| `True` | `6.0` | `7.0` | $\mathcal{S}6$ |

`nesspy >= 1.9.0` also kept every pre-rename scheme alive behind a `99` prefix (old `3.0` →
`993.0`, old `93.0` → `9993.0`, ...). Those that coincide with one of the schemes above are mapped
too: `990.0`/`9990.0` → $\mathcal{S}1$, `9991.0` → $\mathcal{S}2$, `9993.0` → $\mathcal{S}3$,
`993.0` → $\mathcal{S}4$, `996.0` → $\mathcal{S}5$, `997.0` → $\mathcal{S}6$ (linear). Anything
else raises `NotImplementedError` rather than guessing.
