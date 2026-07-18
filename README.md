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