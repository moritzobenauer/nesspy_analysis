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

## Analyzing a single run (`2026/analyzing_order_disorder.py`)

The same pipeline for one run directory (the folder holding the per-mu subfolders):

```bash
uv run python 2026/analyzing_order_disorder.py -i <run_dir> --vis
```

Besides `-m/--min_size`, `--speed`, `--wq/--no-wq` and `-v` (as above) it takes two
independent switches, so a caller can ask for exactly the part of the suite that is
missing from a run:

| Argument | Default | Description |
|----------|---------|-------------|
| `-i`, `--run_dir` | required | A single run directory. |
| `--analysis` / `--no-analysis` | on | Run the order-disorder analysis. `--no-analysis --vis` makes this a lattice-plot-only invocation. |
| `--vis` / `--no-vis` | off | Render the (slow) lattice-overview grids. |

## The research-data pipeline (`database/`)

Turns "the jobs finished on della" into "analyzed data on disk". **Set `DELLA_DIR` and
`LOCAL_DIR` in `database/config.sh` before the first run**, then:

```bash
bash database/run_pipeline.sh        # sync -> catalog -> analyze
bash database/run_pipeline.sh -f     # same, but redo everything from scratch
```

The three stages are also runnable on their own (`sync_from_della.sh`, `catalog.sh`,
`analyze_new.sh`). Each stage only does the work that is actually outstanding, so
re-running the pipeline after a partial sync is cheap and safe.

To keep collecting while jobs are still finishing on della, leave the watcher running
in the background — it repeats the cycle every `PIPELINE_INTERVAL_MIN` minutes:

```bash
nohup bash database/watch_pipeline.sh > /dev/null 2>&1 &   # start
tail -f "$LOCAL_DIR/_logs/watch.log"                       # follow
kill "$(cat "$LOCAL_DIR/_logs/watch.pid")"                 # stop
```

The interval is measured from the end of each cycle, so cycles never overlap however
long the analysis takes, and a failed cycle is logged rather than fatal. A lock
directory allows only one watcher per `LOCAL_DIR`; if a watcher is ever killed with
`kill -9` the lock survives, and `_logs/watch.lock` has to be removed by hand before a
new one will start.

Cataloging writes three kinds of file into each run directory:

| File | Written | Contents |
|------|---------|----------|
| `run_catalog.md` | always | Timestamp, source path on della, header parameters, the resolved driving scheme, and a per-mu table of trajectory counts / replicate folders / `lattice_final.npy` counts. Ends with an *advisory* comparison of the folder name against the header — folder names use several encodings and some drop the decimal point, so the header is always the authority. |
| `<version>.version` | always | Empty marker naming the nesspy version that produced the run (one per distinct version found). |
| `analysis_failed.md` | only on a failed analysis | Written by `analyze_new.sh`, not the catalog. Timestamp, log path and the tail of the traceback for a run whose analysis raised. While it exists the run is skipped, so a permanently broken run is not re-analyzed every cycle; it is removed automatically on the next successful analysis, and `-f` ignores it. |
| `flagged_warning.md` | only on problems | A mu folder with no `out.csv` or no data rows, a trajectory count below the run's modal value (what an out-of-memory kill looks like on disk), replicates missing `lattice_final.npy`, parameters disagreeing between mu folders, several nesspy versions in one run, or errors found in a Slurm log sitting next to the data. |

Run directories are discovered as the grandparent of an `out.csv`, so trees of
different depth are handled by the same code. Nothing is moved or renamed — the local
directory stays a verbatim mirror of della, and the sync is strictly additive.

## Viewing and comparing analyzed runs (`webapp/`)

A read-only Streamlit viewer over the same cached pipeline output:

```bash
uv run streamlit run webapp/app.py
```

Three tabs: **Load data** (browse to a run directory and name it — blocked
unless `order_disorder_analysis.csv` exists and is up to date), **Overview**
(w(q)/lattice-plot status for one dataset plus the four interactive
order-parameter/susceptibility/growth-speed/cluster-observable plots), and
**Compare** (the same four plots overlaid across several datasets, plus a
summary table). It never runs the analysis itself — run the pipeline above
first. The loaded dataset list persists in `webapp/datasets.json` (gitignored,
since it holds machine-local paths).

## Inspecting a run directory from the shell

For simple questions about an `out.csv` — which nesspy version wrote it, how many
trajectories it holds — these one-liners answer faster than starting Python. They are
also what `database/catalog.sh` uses internally, so the numbers in `run_catalog.md`
and the numbers you get here always agree.

```bash
# nesspy version that produced this out.csv — prints just the version string
grep -oE 'nesspy Version [^,]+' out.csv | awk '{print $3}'

# number of independent trajectories: data rows, skipping the '#' header block
# and the CSV column-name line
awk '!/^[[:space:]]*#/ && NF {if (header) rows++; else header=1} END {print rows+0}' out.csv
```

### Reading Slurm logs

`tail {SLURM_ID}.err` and `tail {SLURM_ID}.out` give a quick verdict on whether a job
finished cleanly. A line such as

```
srun: error: della-h17n1: task 0: Out Of Memory
```

in `slurm_report.out` means the process was killed for lack of memory. That is not
fatal for the analysis — the rows already written are still usable — but it always
deserves flagging, because the trajectory count will be short. This is one of the
conditions `flagged_warning.md` reports automatically.

Which `SLURM_ID` belongs to which dataset is not obvious from the filename. The
directory it worked on is printed at the *top* of the error file, so read both ends:

```bash
head -n 20 {SLURM_ID}.err   # names the subdirectory this job ran on
tail {SLURM_ID}.err         # shows how it ended
```

Pairing `head` with `tail` this way is what lets you attribute an error to a specific
dataset.

## Changelog

### 0.13.2

- **Dark gradient background** for the viewer: `.streamlit/config.toml` pins a
  dark theme, `webapp/app.py` paints a navy → slate gradient (`.stApp`, CSS,
  since config.toml only takes flat colours). Figures follow with the
  `plotly_dark` template, a transparent paper so the gradient shows through,
  and `theme=None` on both `st.plotly_chart` calls so Streamlit's own template
  doesn't overwrite that. `_complementary()` now brightens (rather than darkens)
  its result, which is what reads on the dark panel.
- **Compare tab**: summary table gained a `color` column painted with each
  dataset's curve colour; a two-position slider switches panel (c) between
  absolute growth speeds and `v / v_min`, where `v_min` is the smallest positive
  growth speed across all compared datasets (`minimum_growth_speed()`), which
  also adds a `growth_speed_at_critical_rel` column to the table.

### 0.13.1

- **Compact directory browser** (`webapp/directory_browser.py`): one toolbar row
  (up / path / "Use this folder"), a filter box above 8 subfolders, and the
  folder list in a fixed-height scroll box, so any directory costs the same
  screen height. Run directories (📊) get a `＋` that picks them without
  navigating in; hidden (dot) folders are no longer listed.
- **Streamlined adding** (`webapp/tabs/tab_load_data.py`): browser and add panel
  side by side, dataset name pre-filled from the folder name (suffixed `-2`,
  `-3`, ... if taken) — adding is now ＋ then Add. The four `st.metric` status
  tiles became one row of green/red badges.
- **Plot fixes** (`webapp/plots_interactive.py`): all panels draw
  `lines+markers` (panel (a)'s sigmoid fit is dotted to stay distinct); axis
  titles are Unicode, not LaTeX — Streamlit serves Plotly without MathJax, so
  `$\Delta\phi$` rendered as literal text; panel (d) draws ⟨r⟩ in the run's
  colour hue-rotated 180° (`_complementary()`), y-axis titles tinted to match
  for a single run; growth-speed log axis labels 1/2/5 per decade.

### 0.13.0

- **New Streamlit viewer** (`webapp/`, `uv run streamlit run webapp/app.py`):
  read-only web UI over the existing analysis cache, three tabs -- load named
  datasets via an in-app directory browser (gated on
  `order_disorder_analysis.csv` being present and not stale), a per-dataset
  overview (w(q)/lattice-plot status checkboxes + the 4-panel order
  parameter/susceptibility/growth speed/cluster observables plot), and a
  multi-dataset comparison (same 4 panels overlaid + a summary table). Plots
  are interactive (Plotly, zoom/pan/legend-toggle per dataset). Never triggers
  analysis itself. Dataset list persists in `webapp/datasets.json` (gitignored).
- Added `streamlit`, `plotly` as dependencies.

### 0.12.3

- Tightened every changelog entry below to state the essential fact rather than
  the full narrative. No functional changes.

### 0.12.2

- **Locked down stage 4 of `run_pipeline.sh`.** Its `claude -p` call had edited
  `pyproject.toml`, `uv.lock` and `README.md` on its first watcher run. The
  prompt now forbids any change outside `database/results.xlsx`, backed by a
  `--settings` deny-list (`Edit`/`Write`/`NotebookEdit`, `uv add|remove|sync`,
  `git add|commit|rm|mv`).

### 0.12.1

- **`database/results.xlsx` filled in** from the first fully-analyzed
  `MANUSCRIPT_2026` batch (S3/S6, Δμ = 0 and 0.5, `jhom=-3.5`), transcribed from
  each run's `run_catalog.md` / `critical_supersat.txt` /
  `order_disorder_analysis.csv`. `CRITICAL_V` = growth speed at the analysis row
  nearest `critical_supersat`. `MLO CHECK` untouched; `SYMLINK` gets a `file://`
  link to the run directory.
- Added `openpyxl` — needed for style-preserving in-place `.xlsx` writes, which
  `pandas.read_excel`/`to_excel` can't do.

### 0.12.0

- **`run_pipeline.sh` gained a fourth stage**: `claude -p` (`claude-sonnet-5`)
  transcribes newly analyzed data into `database/results.xlsx`, leaving
  `MLO_CHECK` untouched.
- Stage 3's exit status is now captured and re-raised after stage 4, so a run
  that fails to analyze no longer blocks the successful runs from being
  recorded.

### 0.11.3

- **Failed analyses are no longer retried every cycle.** A failed run wrote
  neither output file, so `analyze_new.sh` saw it as outstanding forever. It now
  drops an `analysis_failed.md` marker (timestamp, log path, last 20 lines,
  retry command) and skips the run until a new `out.csv` arrives or `-f` is
  passed; the marker is removed on the next success. The summary reports
  known-failing runs separately, and only new failures set a non-zero exit
  status.

### 0.11.2

- New README section, "Inspecting a run directory from the shell," folding in
  `useful_bash_commands.md`'s one-liners: nesspy version, trajectory count, and
  reading an OOM kill or job/dataset pairing out of Slurm logs.

### 0.11.1

- **Bugfix: sync no longer treats vanishing source files as fatal.** Della jobs
  still writing while `rsync` scans cause spurious "vanished" errors that
  aborted every watcher cycle. A `run_rsync` helper now tolerates GNU rsync's
  exit 24 and openrsync's vanished-file complaints; anything else still fails.
- The transfer's `--stats` summary is now logged and echoed as a short block
  instead of streamed through `tee`.

### 0.11.0

- **New `database/watch_pipeline.sh`**: repeats the pipeline every
  `PIPELINE_INTERVAL_MIN` minutes (default 30) so data collects while jobs are
  still running on della. The interval is measured from cycle *end* (no
  overlap); a failed cycle is logged, not fatal (no `set -e`); a lock directory
  limits to one watcher per `LOCAL_DIR`; an interruptible sleep means `kill`
  stops it immediately.

### 0.10.0

- **New `database/` pipeline** (`run_pipeline.sh`): `sync_from_della.sh`
  (dry-run then additive rsync), `catalog.sh` (writes `run_catalog.md`,
  `<version>.version`, and `flagged_warning.md` on problems), `analyze_new.sh`
  (runs the order-disorder suite only where needed). `config.sh` holds
  `DELLA_DIR`/`LOCAL_DIR`. Runs are discovered as the grandparent of an
  `out.csv`, so mixed-depth trees work unmodified.
- New `database/resolve_scheme.py`: resolves `(hrc, hrc_method, nesspy version)`
  to a canonical scheme name via `schemes.py`.
- `2026/analyzing_order_disorder.py` gained a single-run CLI (`-i/--run_dir`,
  `--analysis/--no-analysis`, `--vis/--no-vis`).
- Bugfix: its `__main__` block called `analyze_directory` on a hard-coded path
  and raised `NameError`; replaced by the CLI above.
- Refactor: `plot_lattice_overviews()` moved into `analyzing_order_disorder.py`
  to avoid a circular import from `parent_sweeper.py`.

### 0.9.1

- Documented the shell one-liners for reading an `out.csv`'s nesspy version,
  trajectory count, and Slurm OOM checks in `CLAUDE.md`. No code changes.

### 0.9.0

- **Bugfix: a single unfinished µ no longer breaks the whole run.**
  `get_thermos_from_file()` read header-only `out.csv` files (no measurement
  rows) and raised a misleading `ValueError` on the `hrc` consistency check.
  Such files are now logged and skipped, matching what `get_data()` already
  did.
- `compare_order_disorder_runs.py` gained a `COMPARISONS` registry, so each
  figure regenerates by name instead of by editing `__main__`.
- Analyzed S3 Δμ=0.5 vs Δμ=0 (`X_320_Y_80_3.0_D{0.5,0.0}_JHOM_-3.50`, 320×80,
  `jhom=-3.5`, `jhet=-2.0`): turning on the drive shifts the critical
  supersaturation from Δφ_c = 0.290±0.018 to 0.347±0.018 (+0.058, 7.4σ against
  the fit covariance), stabilizes the ordered phase at fixed µ (e.g. m: 0.53→
  0.96 at µ=-6.70), and slows growth 25-45% at fixed µ but +18% at the
  (shifted) critical point. The Δμ=0.5 run has fewer seeds (≤16 vs 64-80) and
  2 of 16 µ points produced no data at all (hit `max_time`), so its Δφ_c rests
  on 14 points.

### 0.8.0

- New `compare_order_disorder_runs.py`: overlays two analyzed runs in one
  four-panel figure (order parameter, susceptibility, growth speed, cluster
  observables) built only from cached `order_disorder_analysis.csv` /
  `critical_supersat.txt` — never re-runs w(q), and raises if the cache is
  missing.
- Analyzed S3 Δμ=0 (nesspy 1.9.1) against the legacy S1 baseline
  (`BASELINE_JHOM_35`, nesspy 1.4.1): Δφ_c = 0.290±0.018 vs 0.304±0.018,
  consistent, as expected for two undriven systems.

### 0.7.0

- **Reads the inverse (backward) chemical drive** nesspy 1.10.1 records as
  `inverse_drive`/`inverse_scheme` columns. `Thermos` gained
  `drive_reverse`/`drive_scheme_reverse`; new readers `get_inverse_drive()`,
  `get_inverse_drive_and_scheme()`, `inverse_scheme_from_hrc()`. Data without
  these columns (everything pre-1.10.1) reads as `(0.0, "S0")` — a no-op, so no
  existing analysis changes. Stored for provenance only; no theory or analysis
  consumes it yet.

### 0.6.2

- **BUGFIX** 2026-08-05: S6's drive was damped by each site's *unlike*
  neighbour count; nesspy's `hrc.py` damps by the *likewise* count. Fixed to
  `exp(-n_red)`/`exp(-n_blue)`. **Changes every cached S6 `w(q)`-corrected
  result** (dphi, critical supersaturations, sweep summaries); S0-S5 and
  `flex.py` are unaffected.
- Scheme perturbation extracted into `scheme_rescaled_drive_and_rate()`, making
  each scheme's effective drive directly testable.
- `2026/wq.py`'s own drifted copy of the steady-state function (missing S4/S6)
  replaced by the package version.

### 0.6.1

- **BUGFIX** 2026-08-05: `flex.py` evaluated S6 with a linear form instead of
  the correct exponential; now matches S4/S5 at mean-field. **Changes S6 FLEX
  curves.** S6 data written before 2026-08-04 was generated by the
  then-correct linear kernel, so it isn't directly comparable to the new
  theory curve.

### 0.6.0

- **Driving schemes renamed to S0-S6 everywhere**, matching the manuscript and
  nesspy 1.9.0. Registry moved to new `schemes.py`; old spellings
  (`NODRIVE`, `HOMO`, `SCHEME91`, ...) kept as aliases via `canonical_scheme()`.
- **Legacy `out.csv` support**: nesspy 1.9.0 renumbered `hrc_method` (legacy
  `6.0`=S5, modern `6.0`=S6). `get_nesspy_version()` reads the file's version
  banner and `scheme_from_hrc(..., legacy=...)` picks the right catalogue;
  files with no banner are assumed legacy. One info line is printed per
  directory the first time a legacy remap happens.
- `get_thermos_from_file()` now compares resolved scheme names across a run
  directory rather than raw `hrc_method` numbers, so mixed pre-/post-rename
  data of the same scheme analyzes correctly.
- Bugfix: `properly_fitting_a_curve.py` passed a nonexistent `drivetype` kwarg;
  fixed to `Thermos(method="S0")`.

### 0.5.1

- **BUGFIX**: the per-dataset order-parameter figure in
  `read_summary_and_plot_overviews.py` had lost its sigmoid fit and critical
  line; restored.

### 0.5.0

- **Heterogeneous driving schemes**: `get_thermos_from_file()` maps
  `(hrc, hrc_method)` to a scheme via `scheme_from_hrc()` instead of raising;
  unknown values raise `NotImplementedError`.
- `get_steady_state_probabilities_numerical()` gained SCHEME3 and the
  colour-conditioned SCHEME7.
- New labelling helpers: `scheme_short_label()`, `scheme_math_label()`,
  `scheme_description()`.
- Analysis outputs (`sweep_summary.csv`, `order_disorder_analysis.csv`,
  `critical_supersat.txt`, figures) now record the scheme.

### 0.4.2

- `read_summary_and_plot_overviews.py` now checks stdin is a tty before opening
  the `questionary` checkbox, exiting with a message pointing to `--all`
  instead of crashing.

### 0.4.1

- Growth speed at each dataset's critical supersaturation is now starred on the
  per-dataset and combined growth-speed figures.

### 0.4.0

- **New `read_summary_and_plot_overviews.py`**: interactive (`questionary`)
  selection of analyzed datasets, plotting growth speed and order parameter vs
  log-supersaturation per-dataset and combined.

### 0.3.0

- `parent_sweeper.py` gained `--speed` (adds growth speed at the critical
  supersaturation to `sweep_summary.csv` plus a bar chart) and `--no-wq`
  (skip the w(q) scan, reuse the cached analysis instead).
- Lattice-overview rendering now requires `--vis` instead of running by
  default.

### 0.2.0

- `get_critical_supersat()` now returns `[value, error]`, where the error is
  the sampling-resolution estimate (distance to the nearest sampled `dphi`).
- `fit_sigmoid` gained a complementary covariance-based error (cached, not
  returned).
- New tests for both errors; CI added (`.github/workflows/tests.yml`).
- `critical_supersat.txt` gains a second line for the error; the sweep summary
  and bar chart show error bars.

### 0.1.5

- Bugfix: an `out.csv` with no measurement rows crashed the run; `read_csv` now
  raises a clear `ValueError` and the mu is skipped and logged.

### 0.1.4

- Bugfix: `Thermos.epsilon_matrix` is now derived from `jhom`/`jhet` instead of
  a hardcoded default.

### 0.1.3

- `parent_sweeper.py` gained `--skip`/`-s` to skip already-analyzed runs while
  still including them in the summary.

### 0.1.2

- **Corrected supersaturation pipeline** on `DynamicalOrderDisorder`: `get_wq()`
  (w(q) from final lattices), `get_logarithmic_supersat_corrected()`,
  `get_critical_supersat()` (sigmoid inflection point), `get_thermos_from_file()`
  (auto-detects and cross-checks `Thermos` params).
- New `sigmoid`/`fit_sigmoid` fit; `hatchling` build backend (src layout now
  importable as `nesspy_analysis`).
- New scripts: `analyzing_order_disorder.py`, `parent_sweeper.py` (with
  lattice-overview rendering).