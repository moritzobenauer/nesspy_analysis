# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`nesspy_analysis` is a Python package for post-processing output from `nesspy`, a
lattice Monte Carlo simulator of driven, non-equilibrium 2D systems (order/disorder
transitions, coexistence, growth speeds). The package reads simulation `out.csv`
files and final lattice configurations (`.npy`), computes physical observables
(order parameter `m`, susceptibility, growth speed, critical points), and provides
plotting and theory (FLEX) utilities. Analysis scripts and notebooks that consume
the package live in dated top-level directories (`2025/`, `2026/`,
`3sm_correlation_functions/`).

## Environment & Commands

The project uses [`uv`](https://docs.astral.sh/uv/) (see `uv.lock`, `pyproject.toml`)
with Python >= 3.12.

```bash
uv sync                 # install deps + the package (editable) into .venv
uv run python main.py   # run the scratch/driver script
uv run python testing.py
```

There is **no test suite, linter, or CI configured** — `testing.py` and `main.py`
are ad-hoc driver scripts, not automated tests. Verify changes by running them (or a
notebook) against real data.

### Import path caveat

The package is under `src/nesspy_analysis/`. Two import styles coexist in the repo:
- `import nesspy_analysis as npa` — works when the package is installed via `uv sync`
  (used by `testing.py`, notebooks).
- `import src.nesspy_analysis as npa` — used by `main.py`, works only from repo root.

Prefer the installed-package form (`nesspy_analysis`) for new code.

## Data model

Simulation output lives on an external volume (e.g. `/Volumes/2025/...`), organized
as a parent run directory whose subfolders each contain an `out.csv`. Each `out.csv`:
- Has a `#`-prefixed header block with simulation params (`# jhom`, `# jhet`,
  `# fres`, `# rate`, `# drive`, `# xsize`, `# ysize`) parsed by the `get_*` helpers
  in `read_csv.py`.
- Has CSV rows of per-sample measurements (`m`, `msquared`, `mu`, `gspeed`, `fres`,
  `k`, `dmu`, `rs_width`).

One `out.csv` = measurements at one chemical potential `mu`. Final lattice states are
`lattice_final.npy` files (values in {-2,-1,0,1,2} encoding species/spin).

## Architecture (`src/nesspy_analysis/`)

`__init__.py` re-exports everything via `from .module import *`, so all public
functions are available as `npa.<name>`.

- **`iterdir.py`** — filesystem discovery. `iterdirs()` recursively finds `out.csv`
  files under a run directory; `find_all_final_configs()` finds `lattice_final.npy`.
- **`read_csv.py`** — the core data-loading layer. `read_csv()` parses one `out.csv`
  into a single-row `DataFrame` (means + SEMs of observables), supporting
  **bootstrap resampling** (`bootstrap=True`, `n_samples` as a *fraction*). It also
  derives `growth_speed = L_y^2 * 2 / <t>` with Gaussian-propagated error, and
  cross-checks per-row params against the header. `get_m_vals()` returns raw `m`
  arrays; `get_data_point_from_out_file()` does the aggregation.
- **`classes.py`** — the top-level analysis API.
  - `Thermos` (frozen dataclass) — thermodynamic params for a system (`jhom`, `jhet`,
    `beta`, `fres`, `k`, `dmu`, `method`); consumed by FLEX theory.
  - `Lattice2D` — lattice geometry / PBC / restricted-sampling metadata.
  - `DynamicalOrderDisorder(name, base_path)` — the main workhorse. Loads all
    `out.csv` under `base_path` and computes: raw data (`get_data`, `get_raw_data`),
    per-mu order parameters (`get_oder_parameters`), Lorentzian susceptibility
    critical points (`get_precise_doodt`, `get_susc_curves`), and the zero-growth-
    speed chemical potential (`calculate_zero_growth_speed`). Many methods bootstrap
    and report mean ± SEM.
  - `MultipleSimulations` — concatenates raw data across several run directories.
- **`fitting.py`** — curve fits used by the analysis. `fit_lorentzian()` (susc peaks,
  supports `scipy.odr` when y-errors given), `lorentzian()`, `polynomial()` /
  `fit_polynomial()` (cubic about an offset `x0`).
- **`flex.py`** — FLEX / mean-field theory. `calculate_dphi(mu, thermos)` returns the
  density-difference order parameter; branches on `thermos.method`
  (`NODRIVE` = exact undriven solution, `HOMO`/`SCHEME_*` = driven FLEX solutions,
  each scheme rescaling `dmu` or `k` differently).
- **`plots.py`** — lattice visualization and config-based observables.
  `plot_lattice_clean()` and `plot_all_configurations()` render `.npy` lattices with a
  fixed 5-value colormap; `calculate_order_parameter(method="MLO2024")` and
  `calculate_average_cluster_size()` (scipy `ndimage.label`, 4-connectivity) compute
  observables from a lattice slice (`lb_trr`/`ub_trr` select a column band).

## Conventions

- "Driving schemes" (`SCHEME_3`, `SCHEME_6`, `SCHEME_7`, `SCHEME_91`, `SCHEME_93`,
  `HOMO`, `NODRIVE`) recur across both `flex.py` and the data directory names — a
  scheme identifies how the non-equilibrium drive is applied. Keep the string names
  consistent when adding new ones.
- Order-parameter extraction (`MLO2024` method, the `lb_trr`/`ub_trr` column band, the
  {-2..2} lattice encoding) mirrors `nesspy`'s own definitions — changing it changes
  comparability with the simulator's output.
- Statistical results are reported as **SEM** (`scipy.stats.sem`), not std, and error
  bars come from bootstrap resampling of the per-sample rows.
- `plot_defaults.py` (top-level, duplicated into `2025/`) holds shared matplotlib
  styling for figures.
