# Analyzing `nesspy` output data

## Static Classes

### Thermodynamic Properties of a System

Thermodynamic properties of a system that can be used in FLEX calculations or analysis can be saved in the `Thermos` class. 

### Lattice Properties

The `Lattice2D` class saves the dimensions as well as details about the periodic boundary conditions of a given simulation.

> [!NOTE]
> Note to myself: `nesspy` should output a `Thermos` and `Lattice` files in the main directory!

## Analysis Classes
### Dynamical Order Disorder Transitions

The class `DynamicalOrderDisorder` expects a parent folder with `out.csv` files in subfolders. Every `out.csv` file corresponds to measurements of an order parameter $m$ at a given $\beta \mu$. 

```python
DynamicalOrderDisorder.get_oder_parameters()
``` 

### Multiple Simulations
To easily get the raw output data from multiple simulations an instance of the class `MultipleSimulations` can be initiated and the `get_raw_data()` method returns the a combined data frame.

## Testing

Unit tests live in `tests/` and run entirely offline (they synthesise the small
lattices and `out.csv` files they need, so no external data volume is required).
`pytest` is a dev dependency installed by `uv sync`:

```bash
uv run python -m pytest        # run the whole suite
uv run python -m pytest -q     # quieter output
uv run python -m pytest tests/test_fitting.py::test_lorentzian_peaks_at_x0  # one test
```

## Sweeping a parent directory (`2026/parent_sweeper.py`)

`parent_sweeper.py` runs the order-disorder pipeline over every run subfolder of a
parent directory and writes a combined `sweep_summary.csv` plus a critical
supersaturation bar chart. It accepts the following arguments:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `-i`, `--parent_dir` | `str` (required) | — | Parent directory whose subfolders each hold one run's simulation data. |
| `-s`, `--skip` | flag | off | Skip runs already analyzed (an `order_disorder_analysis.csv` is present); print when each was analyzed and reuse its existing results in the final summary instead of recomputing. |
| `-m`, `--min_size` | `int` | `8` | Minimum blue-cluster cardinality kept for the `r(log S)` observable (use `5` for the "larger than four" rule). |
| `-v`, `--verbose` | flag | off | Print verbose (`INFO`-level) output during analysis. |

## Changelog

### 0.2.0

- **Error on the critical supersaturation**: `DynamicalOrderDisorder.get_critical_supersat()`
  now returns `[value, error]` (was a bare float) and caches the error on
  `self.critical_supersat_err`. The error is a *sampling-resolution* estimate —
  the average distance from the sigmoid inflection point to the nearest sampled
  `dphi` above and below it (equivalently, half the width of the bracketing
  interval), so dense sweeps get a small error and sparse sweeps a large one. If
  the inflection point falls outside the sampled range the one available side is
  used and a warning is logged.
- **Covariance error (complementary)**: `fit_sigmoid` gained a `return_cov`
  option, and `get_critical_supersat()` now also caches the *statistical* error
  on the inflection point from the fit covariance matrix (`sqrt(pcov[1, 1])`) on
  `self.critical_supersat_cov_err` (NaN if the fit is unconstrained). Unlike the
  resolution error, this shrinks with clean/plentiful data rather than with grid
  density; it is computed but not the returned value.
- **Tests**: `tests/test_critical_supersat.py` covers both errors on synthetic
  sigmoid data — the resolution error equals half the local grid spacing, halves
  when sampling doubles, is noise-insensitive, and goes one-sided when
  extrapolated; the covariance error is ~0 for clean data and grows monotonically
  with noise.
- **CI**: `.github/workflows/tests.yml` runs the `uv run pytest` suite on every
  push and pull request (uv-managed, Python 3.12).
- **`2026/analyzing_order_disorder.py`**: writes the error as a second line in
  `critical_supersat.txt`, adds a `critical_supersat_err` column to
  `order_disorder_analysis`'s summary dict, and shades the ±error band around
  the critical line in the order-parameter / susceptibility figure.
- **`2026/parent_sweeper.py`**: the sweep summary CSV gains a
  `critical_supersat_err` column and the bar chart draws the error bars;
  `_read_critical_supersat` now parses both lines back (older single-line files
  report the error as `NaN`).

### 0.1.5

- **Bugfix (empty `out.csv`)**: a mu folder whose `out.csv` has no usable
  measurement rows no longer crashes the whole run. `read_csv` now raises a
  clear `ValueError` (instead of an `UnboundLocalError` / `IndexError`), and
  `DynamicalOrderDisorder.get_data()` logs a `Skipping <file>` warning and
  continues, so the remaining mu values are still analyzed.

### 0.1.4

- **Bugfix (`Thermos`)**: the `epsilon_matrix` is now derived from `jhom`/`jhet`
  (diagonal = `jhom`, off-diagonal = `jhet`) instead of keeping a hardcoded
  default. Previously a `Thermos` built with detected couplings (e.g. from
  `get_thermos_from_file()`) kept a stale `[[-3.5, -2.0], [-2.0, -3.5]]` matrix
  regardless of the actual `jhom`. An explicitly-passed `epsilon_matrix` still
  overrides the derived one.

### 0.1.3

- **`parent_sweeper.py`**: added a `--skip` / `-s` flag that skips run folders
  already containing an `order_disorder_analysis.csv`. Skipped runs print when
  they were analyzed (from the CSV's modification time) and are left untouched
  (no re-analysis, no lattice-overview redraw), yet still appear as full rows in
  the final sweep summary — their thermodynamic parameters are re-parsed from the
  output headers and their critical supersaturation is read back from
  `critical_supersat.txt`.

### 0.1.2

- **Corrected supersaturation pipeline** on `DynamicalOrderDisorder`:
  - `get_wq()` — nearest-neighbour correlation weights $w(q)$ from the final lattice
    configurations, computed in parallel and merged onto the data frame per $\mu$.
  - `get_logarithmic_supersat_corrected(thermos)` — corrected logarithmic
    supersaturation $\Delta\phi = \log S$ from $w(q)$ and the single-site
    steady-state probabilities (requires `get_wq()` first).
  - `get_critical_supersat()` — critical supersaturation as the inflection point
    of a sigmoidal fit of $m$ vs $\log S$.
  - `get_thermos_from_file()` — auto-detects the `Thermos` parameters (`jhom`,
    `jhet`, `fres`, `dmu`, `k`, scheme) from the output files and verifies they
    are consistent across the whole run.
- **Fitting**: added `sigmoid` / `fit_sigmoid` (four-parameter logistic).
- **Packaging**: added a `hatchling` build backend so `uv sync` installs the
  package; the src layout is now importable as `nesspy_analysis`.
- **Misc**: `print_verbose_startup()` banner.
- **Scripts** (`2026/`): `analyzing_order_disorder.py` (single-run pipeline) and
  `parent_sweeper.py` (sweep over a parent directory with `--verbose` logging).
- **Lattice overviews** (`parent_sweeper.py`): the sweep now also renders
  `lattice_overview.png` grids of the final lattices so runs can be eyeballed —
  one grid inside every $\mu$ subfolder (tiling that folder's
  `lattice_final.npy` replicates) and one combined grid per run directory.
  Plotting runs even if the order-disorder fit for a run fails.