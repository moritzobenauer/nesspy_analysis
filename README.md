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
| `--speed` | flag | off | Also report the interface growth speed at the critical supersaturation (`growth_speed_at_critical` / `dgrowth_speed_at_critical` columns + a `sweep_growth_speed.png` bar chart). |
| `--wq` / `--no-wq` | flag | on | Run the expensive $w(q)$ lattice scan (default). Use `--no-wq` to skip it and instead reuse cached $w(q)$ results (`order_disorder_analysis.csv` / `critical_supersat.txt`) to locate the critical supersaturation; a warning is logged for runs with no cache. |
| `--vis` | flag | off | Render the (slow) lattice-overview grids for each run. Off by default so a sweep skips the tiling of every `lattice_final.npy` unless requested. |
| `-v`, `--verbose` | flag | off | Print verbose (`INFO`-level) output during analysis. |

## Changelog

### 0.6.2

- **BUGFIX** 2026-08-05: S6's colour-conditioned drive was damped by each site's
  *unlike* neighbours (`M_red` by `n_blue` and vice versa), following an earlier
  revision of `dealing_with_different_schemes.md`. `nesspy` conditions on the
  **likewise** count — `nhat = nred if current_state == 1 else nblue` in
  `nesspy/src/hrc.py`, with `RED = 1` in `nesspy/src/kmc.py` — and it is
  authoritative, since it generated the data. A red site is now damped by
  `exp(-n_red)` and a blue site by `exp(-n_blue)`, so **the drive decreases
  monotonically as a site gains neighbours of its own colour**, which is the
  defining property of S6. **This changes every S6 `w(q)`-corrected
  supersaturation** (`get_logarithmic_supersat_corrected()` and everything
  downstream: `dphi`, critical supersaturations, the sweep summaries), so cached
  S6 results need recomputing. Unaffected: S0-S5, and `flex.py`, which evaluates
  S6 at the mean-field `n' = 2` either way.
- The scheme perturbation moved out of `get_steady_state_probabilities_numerical()`
  into a new `scheme_rescaled_drive_and_rate(scheme, M, k, environment)` that
  returns `(M_red, M_blue, k)`. Same numerics, but the effective drive of each
  scheme is now directly inspectable and unit-testable instead of only being
  observable through a 5x5 eigenproblem.
- New tests pin the S6 monotonicity requirement (for a positive drive, and as a
  magnitude for a negative one), that a red site's drive is independent of its
  blue neighbours, that S4/S5 fall off in their own neighbour count, that S2/S3
  perturb `k` and leave the drive alone, and that S0/S1 perturb neither.

### 0.6.1

- **BUGFIX** 2026-08-05: `flex.py` evaluated S6 with the linear form
  `dmu_0 * (1 - n'/4)`, i.e. `dmu / 2` at the mean-field `n' = 2`. The linear form
  is wrong — S6 is exponential in the likewise-neighbour count `n'`
  (`nesspy/src/hrc.py`, `hrc_method` 6.0) — so S6 now rescales `dmu` by
  `exp(-2)`, the same as S4/S5. All three dmu-family schemes are the same
  exponential suppression driven by a different neighbour count (`N`,
  `|n_red - n_blue|`, `n'`), and those counts coincide at two neighbours, so the
  three FLEX branches now agree at mean-field level (pinned by a test).
  `get_steady_state_probabilities_numerical()` was already exponential and is
  unchanged; the two S6 implementations no longer disagree about the functional
  form. **This changes S6 FLEX curves** — any saved S6 theory comparison needs
  regenerating.
- Note that S6 runs written before 2026-08-04 (all legacy `hrc_method = 7.0`
  data) were *generated* by nesspy's linear kernel, so an old S6 data set and the
  exponential theory curve are not the same model.

### 0.6.0

- **Driving schemes are now named S0-S6 everywhere.** The canonical scheme
  strings are `"S0"` ... `"S6"` (`S0` = undriven reference, `S1` = homogeneous
  driving, `S2`-`S6` = the heterogeneous schemes), matching the manuscript and
  the numbering `nesspy` itself adopted in its 1.9.0 release. The registry moved
  into a new module `nesspy_analysis/schemes.py` (`read_csv.py` needs it too, and
  cannot import from `classes.py`); everything is still re-exported, so
  `npa.scheme_from_hrc`, `npa.SCHEME_LABELS` etc. keep working.
  The pre-rename spellings (`NODRIVE`, `HOMO`, `SCHEME91`, `SCHEME_3`, ...) remain
  accepted as aliases and are normalised by the new `canonical_scheme()`, which
  raises on anything unrecognised instead of letting a typo reach the physics.
  `Thermos.method` normalises itself, so `Thermos(method="HOMO").method == "S1"`,
  and its default is now `"S0"` (same scheme as the old `"NODRIVE"` default).
  Bare numbers are deliberately rejected by `canonical_scheme()`: `3` is
  ambiguous between the scheme name S3 and the `hrc_method` value 3.0.
- **Backward compatibility for legacy `out.csv` files.** `nesspy 1.9.0`
  (2026-08-03) renamed the schemes, which changed what the `hrc_method` number in
  an `out.csv` *means* — legacy `6.0` is S5 while modern `6.0` is S6, and legacy
  `3.0` is S4 while modern `3.0` is S3. `read_csv.get_nesspy_version()` now reads
  the `# nesspy Version ..., Release Date: ...` banner of each file and
  `is_legacy_output()` decides which catalogue applies, so
  `scheme_from_hrc(hrc, hrc_method, legacy=...)` maps legacy `91.0/93.0/3.0/6.0/7.0`
  → `S2/S3/S4/S5/S6` and modern `1.0`-`6.0` → `S1`-`S6` (plus nesspy's frozen
  `99`-prefixed legacy band). The version is the primary discriminator and the
  release date only a fallback, because nesspy 1.8.0 shares the 2026-08-03
  release date with the renaming 1.9.0 but still used the old numbering. Files
  with no banner at all are assumed legacy.
- Reading a legacy folder **prints one info line to stdout** stating that the
  files are legacy and which remapping was applied, e.g. `[nesspy_analysis]
  Legacy nesspy output in <dir> (13/13 out.csv files): written by nesspy 1.4.1,
  released 2025/11/02, ... Remapped legacy hrc=True, hrc_method=6.0 -> S5
  (previously called 'SCHEME6').` It is printed once per directory subtree, so a
  sweep reports one line per run rather than one per `mu` subfolder
  (`reset_legacy_notices()` clears the cache).
- `DynamicalOrderDisorder.get_thermos_from_file()` resolves the scheme **per
  file** and then requires the resolved schemes to agree, instead of requiring the
  raw `hrc_method` numbers to agree. A folder that mixes pre- and post-rename
  output of the same physical scheme now analyses correctly, and a folder that
  genuinely mixes schemes still raises `ValueError`.
- `read_csv()`'s `header_info` gained `nesspy_version`, `legacy_schemes` and
  `scheme`, so every loaded data point carries its own scheme provenance.
- **BUGFIX** 2026-08-05: `properly_fitting_a_curve.py` called
  `npa.calculate_dphi(..., drivetype="NODRIVE")`, but `calculate_dphi()` has no
  `drivetype` argument — the scheme comes from `Thermos.method`. The script now
  passes `method="S0"` to `Thermos`.
- Note on S6: `nesspy` changed S6 from the linear form `dmu_0 * (1 - n'/4)` to the
  exponential `dmu_0 * exp(-n')` on 2026-08-04, so legacy `hrc_method=7.0` refers
  to the linear one. This package's two S6 implementations disagree on that
  (`get_steady_state_probabilities_numerical()` is exponential, `flex.py` uses
  `dmu/2`, the linear form at `n'=2`); both are documented at their call sites and
  the numerics are unchanged by this release.

### 0.5.1

- **BUGFIX**: The per-dataset order-parameter figure written by
  `2026/read_summary_and_plot_overviews.py` (`order_parameter_vs_supersat.png`)
  lost its sigmoidal fit and its critical-supersaturation line, so running the
  overview script overwrote the complete figure produced by `analyze_directory`
  with a bare scatter. `_plot_single_dataset()` now refits the logistic from the
  cached `(dphi, m, dm)` and overlays the sigmoidal fit plus a dashed
  transition line (with a shaded error band from `critical_supersat_err`),
  matching `analyze_directory`'s figure.

### 0.5.0

- **Heterogeneous driving schemes**: `DynamicalOrderDisorder.get_thermos_from_file()`
  no longer raises on an active `hrc`. The `(hrc, hrc_method)` pair read from the
  `out.csv` data rows is now mapped onto a driving scheme via the new
  `scheme_from_hrc()` helper: `hrc=False` → `HOMO` (S1, homogeneous driving);
  `hrc=True` with `hrc_method` `91.0` → `SCHEME91` (S2), `93.0` → `SCHEME93` (S3),
  `3.0` → `SCHEME3` (S4), `6.0` → `SCHEME6` (S5), `7.0` → `SCHEME7` (S6). Unknown
  active `hrc_method` values raise `NotImplementedError`. When `hrc` is inactive
  the `hrc_method` float is treated as free (no longer required to be consistent
  across files). See `dealing_with_different_schemes.md`.
- **Two missing schemes in the numerical steady state**:
  `get_steady_state_probabilities_numerical()` gained `SCHEME3` (drive rescaled by
  `exp(-|n_red + n_blue|)`) and the colour-conditioned `SCHEME7` (a blue
  particle's drive damped by its red neighbours and vice versa, so the red- and
  blue-active states use independent `M_red`/`M_blue`). It now raises on an
  unknown scheme string.
- **Scheme labelling helpers**: new `scheme_short_label()` (`S1`..`S6`),
  `scheme_math_label()` (`$\mathcal{S}n$`, for plots) and `scheme_description()`.
- **Analysis outputs state the scheme**: `sweep_summary.csv` and the skipped-run
  summaries gain a `scheme` column; `order_disorder_analysis.csv` gains `method`
  and `scheme` columns; `critical_supersat.txt` gains a `scheme:` line; and the
  per-dataset / overview figures (`analyzing_order_disorder.py`,
  `read_summary_and_plot_overviews.py`) carry the scheme in their titles/legends.

### 0.4.2

- **Graceful non-interactive fallback**: `2026/read_summary_and_plot_overviews.py`
  now checks that stdin is a terminal before opening the `questionary` checkbox
  (which crashes under a piped/non-tty stdin) and exits with a message pointing to
  `--all` instead of a traceback.

### 0.4.1

- **Star the transition-point growth speed**: `2026/read_summary_and_plot_overviews.py`
  now marks the growth speed at each dataset's critical supersaturation (read from
  `sweep_summary.csv`'s `critical_supersat`) with a star on both the per-dataset
  and combined growth-speed figures. The starred value reuses
  `analyzing_order_disorder.growth_speed_at_critical` (nearest sampled raw point),
  so it matches `sweep_summary.csv`. Datasets with no critical value simply omit
  the star.

### 0.4.0

- **Overview plotting (`2026/read_summary_and_plot_overviews.py`)**: a new script
  that reads a parent sweep's `sweep_summary.csv`, lets the user pick which
  analyzed datasets to include via an interactive `questionary` checkbox
  (`--all` skips the menu), and plots the growth speed and order parameter as a
  function of the logarithmic supersaturation `dphi = log S`. For each selected
  dataset it saves per-dataset figures (`growth_speed_vs_supersat.png`,
  `order_parameter_vs_supersat.png`, growth speed on a log y axis) next to that
  dataset, plus combined overlay figures across all selections
  (`overview_growth_speed_vs_supersat.png`,
  `overview_order_parameter_vs_supersat.png`) in the parent directory. Adds
  `questionary` as a dependency.

### 0.3.0

- **Growth speed in the sweep summary (`--speed`)**: `2026/parent_sweeper.py`
  gained a `--speed` flag that adds `growth_speed_at_critical` /
  `dgrowth_speed_at_critical` columns to `sweep_summary.csv` (and a companion
  `sweep_growth_speed.png` bar chart). The reported value is the per-mu interface
  growth speed (`2·L_y²/⟨t⟩`, computed in `read_csv.py`) at the sampled point
  whose `dphi` is closest to the critical supersaturation — the nearest raw data
  point, not an interpolation. `analyze_directory` grew a `compute_speed`
  argument and a `growth_speed_at_critical()` helper.
- **Separable w(q) (`--no-wq`)**: the expensive w(q) lattice scan now runs by
  default but can be skipped with `--no-wq`. In that mode `analyze_directory`
  reuses the cached `order_disorder_analysis.csv` / `critical_supersat.txt`
  (leaving them untouched) to place the critical supersaturation and report the
  growth speed there; if no cache exists it warns that w(q) needs to be run.
  `_read_critical_supersat` moved into `2026/analyzing_order_disorder.py` as
  `read_critical_supersat` (single source of truth, imported by the sweeper).
- **Optional lattice overviews (`--vis`)**: the slow lattice-overview rendering
  (`plot_lattice_overviews`) is now off by default and only runs with `--vis`.

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