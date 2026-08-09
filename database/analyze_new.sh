#!/usr/bin/env bash
#
# Stage 3: run the order-disorder analysis suite on every run that needs it.
#
# Each run directory gets its results written in place by
# 2026/analyzing_order_disorder.py:
#   order_disorder_analysis.csv, critical_supersat.txt,
#   order_parameter_vs_supersat.png, cluster_observables_vs_supersat.png
#   lattice_overview.png (per mu folder and one for the run)
#
# Work is only ever done once: a run is analyzed when its analysis CSV is
# missing or older than its newest out.csv, and the (slow) lattice plots are
# rendered when lattice_overview.png is missing. A run that already has both is
# skipped without launching python at all.
#
# A run whose analysis FAILS is a third case. It writes no analysis CSV and no
# lattice_overview.png, so by the rule above it looks outstanding forever — and
# the watcher would re-run the whole thing, lattice rendering included, on every
# cycle, only to fail again. Some failures are genuinely permanent (a
# susceptibility fit that will not converge for the mu range sampled), so a
# failing run drops an analysis_failed.md marker and is left alone until its
# data actually changes. Any new out.csv makes it worth another try; so does -f.
#
# Runs are processed one at a time because the analysis itself spawns a
# multiprocessing Pool internally.
#
# Usage: analyze_new.sh [-f]     -f re-analyzes everything from scratch

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
check_config

FORCE=0
if [[ "${1:-}" == "-f" ]]; then FORCE=1; fi

ANALYSIS_CSV="order_disorder_analysis.csv"
LATTICE_PNG="lattice_overview.png"
ANALYZER="${REPO_DIR}/2026/analyzing_order_disorder.py"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"

n_analyzed=0
n_skipped=0
n_failed=0
n_known_bad=0
failed_runs=()

while IFS= read -r run_dir; do
    name="$(basename "${run_dir}")"

    # Decide what this run is missing.
    needs_analysis=0
    needs_vis=0
    if [[ "${FORCE}" -eq 1 ]]; then
        needs_analysis=1
        needs_vis=1
    else
        if [[ ! -f "${run_dir}/${ANALYSIS_CSV}" ]]; then
            needs_analysis=1
        elif [[ -n "$(find "${run_dir}" -name out.csv -newer "${run_dir}/${ANALYSIS_CSV}" -print -quit)" ]]; then
            # new chemical potentials arrived since the last analysis
            needs_analysis=1
        fi
        if [[ ! -f "${run_dir}/${LATTICE_PNG}" ]]; then
            needs_vis=1
        fi

        # Known-bad: it failed before and nothing has arrived since, so there is
        # no reason to expect a different outcome. -f skips this check, which is
        # how a run gets retried on demand after the cause has been dealt with.
        if [[ -f "${run_dir}/${FAILED_FILE}" ]] && \
           [[ -z "$(find "${run_dir}" -name out.csv -newer "${run_dir}/${FAILED_FILE}" -print -quit)" ]]; then
            echo "Skipping ${name} -- failed before, no new data since (see ${FAILED_FILE})"
            n_known_bad=$((n_known_bad + 1))
            continue
        fi
    fi

    if [[ "${needs_analysis}" -eq 0 && "${needs_vis}" -eq 0 ]]; then
        n_skipped=$((n_skipped + 1))
        continue
    fi

    # Ask for exactly the missing half (or both).
    flags=()
    if [[ "${needs_analysis}" -eq 1 ]]; then flags+=(--analysis); else flags+=(--no-analysis); fi
    if [[ "${needs_vis}" -eq 1 ]]; then flags+=(--vis); fi

    log="${LOG_DIR}/analyze_${name}_${TIMESTAMP}.log"
    echo "Analyzing ${name} (${flags[*]})"
    if uv run --project "${REPO_DIR}" python "${ANALYZER}" -i "${run_dir}" -v "${flags[@]}" \
            > "${log}" 2>&1; then
        n_analyzed=$((n_analyzed + 1))
        echo "  done -- log: ${log}"
        # Whatever was wrong before is evidently fixed.
        rm -f "${run_dir}/${FAILED_FILE}"
    else
        n_failed=$((n_failed + 1))
        failed_runs+=("${name}")
        echo "  FAILED -- see ${log}:"
        tail -3 "${log}" | sed 's/^/    /'

        # Leave the reason in the run directory, next to run_catalog.md, so the
        # failure is visible where the data is and not only in a pipeline log
        # that gets harder to find with every cycle.
        {
            echo "# Analysis failed: ${name}"
            echo
            echo "Failed: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "Full log: \`${log}\`"
            echo
            echo "This run is skipped on later cycles until a new out.csv arrives for it."
            echo "To retry by hand once the cause is dealt with:"
            echo
            echo '```bash'
            echo "rm '${run_dir}/${FAILED_FILE}'"
            echo "bash database/analyze_new.sh"
            echo '```'
            echo
            echo "## Last lines of the log"
            echo
            echo '```'
            tail -20 "${log}"
            echo '```'
        } > "${run_dir}/${FAILED_FILE}"
    fi
done < <(find_run_dirs)

echo
echo "Analysis done: ${n_analyzed} analyzed, ${n_skipped} already complete," \
     "${n_known_bad} known-failing (skipped), ${n_failed} failed."
if [[ "${n_failed}" -gt 0 ]]; then
    printf '  failed: %s\n' "${failed_runs[*]}"
    exit 1
fi
