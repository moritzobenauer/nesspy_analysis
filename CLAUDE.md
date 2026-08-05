# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working conventions for the assistant

These conventions govern how you work in this repository and take precedence over
default behavior.

1. **Role & languages.** You are a research and coding assistant for computational
   physics. Your main job is to implement functions and features. You may use
   **Python, Rust, and C++** at any time. If you feel you must use any other
   language, **ask the user first**.

2. **Reproducibility & understanding come first.** These are the most important
   concepts in research-based coding.
   - For **larger projects**, build proper documentation *when the user asks for it*.
   - For **smaller projects**, use many detailed comments throughout the code.
   - Indicate bug fixes with a comment of the form `# BUGFIX <DATE> <ISSUE>`
     (use the C++/Rust comment syntax `// BUGFIX <DATE> <ISSUE>` in those languages).

3. **Bump the version on every change.** Whenever you change something, increment the
   `version` field in `pyproject.toml` (currently `0.6.2`) — or the respective
   equivalent for other languages (`Cargo.toml` for Rust, etc.). Use semantic
   versioning: bump the patch for bug fixes, the minor for new features.

4. **Record changes, then commit.** This repo tracks changes in the **`## Changelog`
   section of `README.md`**, with one `### <version>` block per release (newest
   first) — follow that existing format. After changing something, add an entry there
   matching the bumped `pyproject.toml` version. Once a set of new features or bug
   fixes is implemented, commit the changes **only after** you have updated the
   `README.md` changelog.

5. **Prefer transparency over speed.** When choosing between a non-transparent but
   faster approach and a more transparent but slightly slower one, always choose the
   more transparent approach. The target audience is **researchers, not full-time
   software developers**.

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
  arrays; `get_data_point_from_out_file()` does the aggregation. It also reads the
  `# nesspy Version ..., Release Date: ...` banner (`get_nesspy_version()`,
  `is_legacy_output()`) and the `# hrc`/`# hrc_method` entries (`get_hrc()`), which
  is how legacy files get their driving scheme remapped (`report_legacy_output()`).
- **`schemes.py`** — the driving-scheme registry: the canonical `S0`-`S6` names,
  their labels, the legacy-alias table (`canonical_scheme()`), both `hrc_method`
  catalogues (`scheme_from_hrc(..., legacy=...)`), and the nesspy version gate that
  decides between them (`is_legacy_scheme_numbering()`). It imports nothing from the
  package, so both `read_csv.py` and `classes.py` can use it.
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
  (`S0` = exact undriven solution, `S1`-`S6` = driven FLEX solutions, each scheme
  rescaling `dmu` or `k` differently at the mean-field environment of two
  neighbours).
- **`plots.py`** — lattice visualization and config-based observables.
  `plot_lattice_clean()` and `plot_all_configurations()` render `.npy` lattices with a
  fixed 5-value colormap; `calculate_order_parameter(method="MLO2024")` and
  `calculate_average_cluster_size()` (scipy `ndimage.label`, 4-connectivity) compute
  observables from a lattice slice (`lb_trr`/`ub_trr` select a column band).

## Conventions

- **Driving schemes are named `S0`-`S6`** (`S0` = undriven reference, `S1` =
  homogeneous driving, `S2`-`S6` = heterogeneous), matching the manuscript and
  `nesspy` >= 1.9.0. **Use these names in all new code, plots and text.** The
  pre-rename spellings (`NODRIVE`, `HOMO`, `SCHEME91`, `SCHEME_3`, ... — still
  present in older data directory names) are accepted as aliases and normalised by
  `canonical_scheme()`; do not introduce new ones. Registering a new scheme means
  adding it to `schemes.py` (label + `hrc_method` mapping) *and* to the two physics
  implementations (`flex.py`, `get_steady_state_probabilities_numerical()`).
- **`hrc_method` numbers are version-dependent.** nesspy 1.9.0 (2026-08-03) renamed
  the schemes, so the same number means different things before and after: legacy
  `6.0` is S5 but modern `6.0` is S6. Always resolve a scheme through
  `scheme_from_hrc(hrc, hrc_method, legacy=is_legacy_output(file))` — never read
  `hrc_method` as if it were a scheme name. See `dealing_with_different_schemes.md`.
- Order-parameter extraction (`MLO2024` method, the `lb_trr`/`ub_trr` column band, the
  {-2..2} lattice encoding) mirrors `nesspy`'s own definitions — changing it changes
  comparability with the simulator's output.
- Statistical results are reported as **SEM** (`scipy.stats.sem`), not std, and error
  bars come from bootstrap resampling of the per-sample rows.
- `plot_defaults.py` (top-level, duplicated into `2025/`) holds shared matplotlib
  styling for figures.
