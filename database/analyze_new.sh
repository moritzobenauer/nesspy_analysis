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
    else
        n_failed=$((n_failed + 1))
        failed_runs+=("${name}")
        echo "  FAILED -- see ${log}:"
        tail -3 "${log}" | sed 's/^/    /'
    fi
done < <(find_run_dirs)

echo
echo "Analysis done: ${n_analyzed} analyzed, ${n_skipped} already complete, ${n_failed} failed."
if [[ "${n_failed}" -gt 0 ]]; then
    printf '  failed: %s\n' "${failed_runs[*]}"
    exit 1
fi
