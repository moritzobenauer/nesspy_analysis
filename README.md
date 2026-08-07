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
| `flagged_warning.md` | only on problems | A mu folder with no `out.csv` or no data rows, a trajectory count below the run's modal value (what an out-of-memory kill looks like on disk), replicates missing `lattice_final.npy`, parameters disagreeing between mu folders, several nesspy versions in one run, or errors found in a Slurm log sitting next to the data. |

Run directories are discovered as the grandparent of an `out.csv`, so trees of
different depth are handled by the same code. Nothing is moved or renamed — the local
directory stays a verbatim mirror of della, and the sync is strictly additive.

## Changelog

### 0.11.0

- **New: `database/watch_pipeline.sh`.** Runs the whole pipeline every
  `PIPELINE_INTERVAL_MIN` minutes (new setting in `config.sh`, default 30) so data can
  be collected and analyzed while jobs are still finishing on della. Start it with
  `nohup bash database/watch_pipeline.sh > /dev/null 2>&1 &`, follow it with
  `tail -f <LOCAL_DIR>/_logs/watch.log`, stop it with
  `kill "$(cat <LOCAL_DIR>/_logs/watch.pid)"`.

  Three details that matter for something left running unattended:
  - The interval is measured from when a cycle *finishes*, so cycles never overlap
    however long the analysis takes.
  - A failed cycle (della unreachable, one run that will not fit) is logged and the
    watcher carries on; it deliberately does not use `set -e`.
  - An atomic lock directory allows only one watcher per `LOCAL_DIR`, so two
    analyses can never write into the same run directory at once. The sleep runs as
    an interruptible background job, so `kill` stops the watcher immediately and
    releases the lock instead of leaving it behind until the interval elapses.

### 0.10.0

- **New: the research-data pipeline in `database/`.** Four short bash scripts turn
  "results finished on della" into "analyzed data on disk" in one command
  (`database/run_pipeline.sh`):
  - `sync_from_della.sh` — an `rsync` dry run decides whether there is anything new
    before a single byte is transferred, then copies it down. Strictly additive
    (never `--delete`), so the report files written below survive re-syncs.
  - `catalog.sh` — writes a `run_catalog.md` into every run directory recording the
    header parameters, the resolved driving scheme, and **how many trajectories each
    chemical potential actually has**; drops a `<version>.version` marker naming the
    nesspy version that produced the run; and writes a `flagged_warning.md` only when
    something is wrong (missing/empty `out.csv`, trajectory counts below the run's
    modal value, replicates missing `lattice_final.npy`, parameters disagreeing
    between mu folders, mixed nesspy versions, or errors in a Slurm log if one is
    present next to the data).
  - `analyze_new.sh` — runs the full order-disorder suite, including the slow lattice
    overviews, on every run that needs it and only once: a run is (re)analyzed when
    its `order_disorder_analysis.csv` is missing or older than its newest `out.csv`,
    and the lattice plots are rendered when `lattice_overview.png` is missing.
  - `config.sh` holds `DELLA_DIR` / `LOCAL_DIR` so retargeting the pipeline never
    means editing a script. **Both need filling in before first use.**

  Runs are discovered as the *grandparent of an `out.csv`*, which is what makes the
  same scripts work for both `RETHINKING_SUPERSAT/<run>/<mu>/` and the deeper
  `COMPARING_SCHEMES/SCHEME6/D05/<mu>/`. Nothing is ever moved or renamed: the local
  tree stays a verbatim mirror of della.

- **New: `database/resolve_scheme.py`.** A thin wrapper that resolves
  `(hrc, hrc_method, nesspy version)` to a canonical `S0`-`S6` name through
  `schemes.py`. It exists so the version-dependent `hrc_method` mapping is never
  re-implemented in shell — the same number means different schemes before and after
  nesspy 1.9.0. It imports only `nesspy_analysis.schemes` (no pandas), so it is cheap
  enough to call once per run directory.

- **New: a single-run CLI for `2026/analyzing_order_disorder.py`.** The analysis suite
  could previously only be driven over a whole parent directory
  (`parent_sweeper.py`). It now takes `-i/--run_dir` plus independent
  `--analysis/--no-analysis` and `--vis/--no-vis` switches, so a caller can request
  exactly the half of the suite a run is missing.

- **Bug fix.** `2026/analyzing_order_disorder.py`'s `__main__` block called
  `analyze_directory(data_path)` on a module-level constant pointing at one hard-coded
  run directory, so running the file as a script raised `NameError`. Replaced by the
  CLI above.

- **Refactor.** `plot_lattice_overviews()` moved from `2026/parent_sweeper.py` into
  `2026/analyzing_order_disorder.py`, next to `analyze_directory()`, so the new
  single-run CLI can call it without a circular import. `parent_sweeper.py` now
  imports it from there; its behaviour is unchanged.

### 0.9.1

- **Documentation.** Recorded the curated shell one-liners for inspecting a run
  directory in `CLAUDE.md` (new "Quick shell inspection of a run directory" section
  under *Data model*): reading the nesspy version out of an `out.csv` banner,
  counting the independent trajectories in it, and checking the Slurm logs
  (`slurm_error.err` / `slurm_report.out`) for failures such as `Out Of Memory`.
  These replace the more roundabout pipelines previously used for the same
  questions. No code changes.

### 0.9.0

- **Bug fix — a single unfinished µ no longer makes a run directory unanalyzable.**
  `DynamicalOrderDisorder.get_thermos_from_file()` read *every* `out.csv` under the run
  directory, including those that contain only the `#` header block and the column names
  (a µ whose simulations wrote no measurement rows, e.g. because they hit `max_time`
  before the interface finished). Such a file reached the `hrc` consistency check with an
  empty column and raised the misleading `ValueError: Inconsistent 'hrc' within <file>:
  []`. `get_data()` already skipped those µ and carried on, so parameter detection now
  does the same: header-only files are logged and skipped, and the consistency checks
  quote the number of files that actually contributed. If *no* file carries measurement
  rows, the error now says so explicitly instead of reporting an empty parameter set.
- `2026/compare_order_disorder_runs.py` gained a `COMPARISONS` registry and a
  `run_comparison(key)` helper, so each figure in `RETHINKING_SUPERSAT` is regenerated by
  name (`python compare_order_disorder_runs.py <comparison>`) rather than by editing the
  `__main__` block. The previous `s3_d0_vs_baseline` comparison is unchanged and remains
  the default.
- Analyzed `RETHINKING_SUPERSAT/X_320_Y_80_3.0_D0.5_JHOM_-3.50_F0.0_K1.0` (nesspy 1.9.1,
  `hrc_method = 3.0 → S3`, Δμ = 0.5, Δf = 0, k = 1) and compared it against the otherwise
  identical Δμ = 0 run from 0.8.0 — same 320×80 lattice, same `jhom = −3.5`,
  `jhet = −2.0`, same scheme — as the new `s3_drive` comparison
  (`comparison_S3_D0.5_vs_D0.0.{png,csv}`).
  - **Turning the S3 drive on shifts the order/disorder transition to higher
    supersaturation:** Δφ_c = 0.290 ± 0.018 → 0.347 ± 0.018, a shift of +0.058. That is
    2.2σ against the conservative µ-grid sampling resolution but 7.4σ against the
    sigmoid fit covariance (σ = 0.0063 and 0.0047), i.e. the shift is well resolved by
    the fit and limited by how finely µ was scanned. In terms of the supersaturation
    itself, S_c = 1.336 → 1.415 (+5.9 %).
  - The drive **stabilizes the ordered phase at every shared µ**: e.g. at µ = −6.70,
    `m` = 0.53 → 0.96. The cluster observables agree — the wrong-bond fraction `q` is
    uniformly lower and the normalized cluster size `r` uniformly higher with the drive,
    so this is genuine ordering rather than flopping finite domains.
  - The drive **slows interface growth at fixed µ** by 25–45 % (`v(Δμ=0.5)/v(Δμ=0)` runs
    from 0.79 near the transition down to 0.55 at the disordered end). Because the
    critical point moves to higher supersaturation, the growth speed *at* Δφ_c is
    nonetheless higher: 9.64×10⁻³ → 1.14×10⁻², +18 %.
  - Caveats recorded with the data: the Δμ = 0.5 run has at most 16 seeds per µ against
    64–80 for Δμ = 0, so its error bars are correspondingly larger; and its two deepest
    chemical potentials (µ = −6.90, −6.85) produced **no** measurement rows at all while
    µ = −6.80…−6.65 completed only 6–13 of 16 seeds — a direct consequence of the slower
    driven growth hitting `max_time = 10⁷`. The driven ordered branch is therefore more
    thinly sampled than the undriven one, and Δφ_c for Δμ = 0.5 rests on 14 µ points
    rather than 16.

### 0.8.0

- New `2026/compare_order_disorder_runs.py`: overlays two (or more) already-analyzed run
  directories in one four-panel figure — (a) order parameter `m` vs `log S` with the
  logistic fit and each run's critical supersaturation, (b) susceptibility, (c) interface
  growth speed (log ordinate) with the speed at Δφ_c marked, (d) the cluster observables
  `q` (left axis, filled) and `r` (right axis, open).
- It reads the caches that `analyzing_order_disorder.analyze_directory()` writes
  (`order_disorder_analysis.csv`, `critical_supersat.txt`) and **never re-runs the w(q)
  scan**, so both runs are guaranteed to have been processed by the identical pipeline; a
  directory without those caches raises `FileNotFoundError` rather than being silently
  recomputed with different settings. Each run's driving scheme is re-resolved from the
  raw `out.csv` headers via `get_thermos_from_file()`, so a legacy run is remapped onto
  its `S*` name in the legend too. `summarize()` returns the parameters and critical
  values as a one-row-per-run DataFrame.
- Analyzed `RETHINKING_SUPERSAT/X_320_Y_80_3.0_D0.0_JHOM_-3.50_F0.0_K1.0` (nesspy 1.9.1,
  i.e. **modern** scheme numbering, `hrc_method = 3.0 → S3`, Δμ = 0, Δf = 0, k = 1) and
  compared it against `RETHINKING_SUPERSAT/BASELINE_JHOM_35` (nesspy 1.4.1, legacy
  numbering, `hrc = False → S1`, Δμ = 0, Δf = −20, k = 0). Δφ_c = 0.290 ± 0.018 vs
  0.304 ± 0.018 — consistent within the sampling resolution, as expected for two undriven
  systems. Outputs written next to the data as `comparison_S3_D0_vs_baseline.{png,csv}`.

### 0.7.0

- Reads the **inverse (backward) chemical drive** that `nesspy` 1.10.0 introduced and
  1.10.1 records in `out.csv` as the `inverse_drive` / `inverse_scheme` columns (written
  after `k`). It drives the inactive → active reaction (`-1 → 1`, `-2 → 2`), multiplying
  that rate by `exp(inverse_drive)`, with its own Δμ-family scheme.
- `Thermos` gained two fields: `drive_reverse` (float) and `drive_scheme_reverse`
  (canonical `S*` name, normalised like `method`). `DynamicalOrderDisorder.get_thermos_from_file()`
  detects both and requires them to be consistent across a run directory, and
  `read_csv()` reports them in its `header_info` dict.
- **Nothing changes for any data analyzed so far.** Output without those columns —
  everything written before nesspy 1.10.1 — reads as `drive_reverse = 0.0` and
  `drive_scheme_reverse = "S0"`, i.e. an undriven backward channel, which is exactly what
  such runs did (`exp(0.0) == 1.0`). Verified against the legacy S6 growth runs on
  `/Volumes/2025`: identical `m`, `growth_speed` and forward scheme.
- New readers `get_inverse_drive()` (the raw `(inverse_drive, inverse_scheme)` pair, from
  the columns, falling back to the `# inverse_drive` / `# inverse_drive_scheme` header
  entries) and `get_inverse_drive_and_scheme()` (the resolved `(drive_reverse,
  drive_scheme_reverse)` pair) in `read_csv.py`, plus `inverse_scheme_from_hrc()` in
  `schemes.py`. The resolver mirrors `nesspy`: `hrc` inactive → S1 (nesspy only perturbs
  the inverse drive inside its `if hrc:` branch), a k-family number (S2/S3) raises
  `ValueError` as `hrc.spatial_dmu` does, a zero drive reads as S0, and there is no legacy
  catalogue — the inverse drive is newer than the 1.9.0 renaming, so its number is always
  the manuscript numbering.
- **These values are stored for provenance only.** No consumer uses them yet: `flex.py`
  and `get_steady_state_probabilities_numerical()` still model the forward drive alone, so
  a nonzero inverse drive is not currently reflected in any theory curve.
- New tests in `tests/test_inverse_drive.py` pin the scheme resolution, both read paths,
  the legacy defaults, and the run-level consistency check.

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
- `2026/wq.py` carried its own drifted copy of
  `get_steady_state_probabilities_numerical()` that never grew an S4 or S6 branch
  — so an S6 run there silently got **no** perturbation — and whose single `M`
  could not express a colour-conditioned drive at all. It now uses the package
  function, which is the one the test suite covers.

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