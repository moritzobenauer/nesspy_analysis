#!/usr/bin/env bash
#
# Stage 2: catalog every run directory in the local mirror.
#
# For each run it writes, into the run directory itself:
#   run_catalog.md       human-readable record of the parameters, the driving
#                        scheme, and the per-mu trajectory counts
#   <version>.version    empty marker naming the nesspy version that produced it
#   flagged_warning.md   only when something looks wrong (see check_run below)
#
# A run is re-catalogued when any of its out.csv is newer than its existing
# run_catalog.md, so extending a mu sweep refreshes the record automatically.
#
# Usage: catalog.sh [-f]     -f re-catalogs everything, ignoring the staleness check

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
check_config

FORCE=0
if [[ "${1:-}" == "-f" ]]; then FORCE=1; fi

# --- small helpers -------------------------------------------------------

# One value out of the '#' header block. The block is written twice by nesspy,
# so we deliberately take the first match.
header_value() {  # header_value <out.csv> <key>
    grep -m1 "^# $2:" "$1" 2>/dev/null | sed 's/^[^:]*: *//' | tr -d ' \r'
}

# The nesspy version banner (one-liner from useful_bash_commands.md).
nesspy_version() {  # nesspy_version <out.csv>
    grep -m1 -oE 'nesspy Version [^,]+' "$1" 2>/dev/null | awk '{print $3}'
}

# Number of independent trajectories = data rows, skipping the '#' header block
# and the CSV column-name line (one-liner from useful_bash_commands.md).
trajectory_count() {  # trajectory_count <out.csv>
    awk '!/^[[:space:]]*#/ && NF {if (header) rows++; else header=1} END {print rows+0}' "$1"
}

# Numeric equality, tolerant of "0" vs "0.0". Exit 2 if either side is empty, so
# a missing value is "unknown", never "mismatch".
same_number() {  # same_number <a> <b>
    awk -v a="$1" -v b="$2" 'BEGIN{ if (a=="" || b=="") exit 2; exit !(a+0 == b+0) }'
}

# Append one line to the run's advisory section when a value parsed out of the
# folder name disagrees with the header. Silent when they agree or when either
# side is missing. Relies on bash's dynamic scoping to reach the caller's
# `advisory` variable.
check_token() {  # check_token <label> <folder-name value> <header value>
    local status=0
    same_number "$2" "$3" || status=$?
    if [[ "${status}" -eq 1 ]]; then
        advisory+="- \`$1\` in the folder name is $2, header says $3"$'\n'
    fi
}

# --- per-run cataloging --------------------------------------------------

catalog_run() {
    local run_dir="$1"
    local catalog="${run_dir}/${CATALOG_FILE}"
    local warnings="${run_dir}/${WARNING_FILE}"
    local warn_tmp; warn_tmp="$(mktemp)"

    # Every immediate subdirectory is a mu folder in this data model
    # (LOCAL_DIR/<...>/<run>/<mu>/out.csv).
    local mu_dirs=()
    while IFS= read -r d; do mu_dirs+=("$d"); done < <(find "${run_dir}" -mindepth 1 -maxdepth 1 -type d | sort)

    # Reference out.csv: the first mu folder that actually has one. Its header is
    # the ground truth for the run's parameters.
    local ref_csv=""
    local d
    for d in "${mu_dirs[@]}"; do
        if [[ -f "${d}/out.csv" ]]; then ref_csv="${d}/out.csv"; break; fi
    done
    if [[ -z "${ref_csv}" ]]; then
        echo "  no out.csv found, skipping"
        rm -f "${warn_tmp}"
        return
    fi

    # --- parameters from the header --------------------------------------
    local jhom jhet fres drive rate xsize ysize hrc hrc_method rsampling rswidth source_path
    jhom=$(header_value "${ref_csv}" jhom)
    jhet=$(header_value "${ref_csv}" jhet)
    fres=$(header_value "${ref_csv}" fres)
    drive=$(header_value "${ref_csv}" drive)
    rate=$(header_value "${ref_csv}" rate)
    xsize=$(header_value "${ref_csv}" xsize)
    ysize=$(header_value "${ref_csv}" ysize)
    hrc=$(header_value "${ref_csv}" hrc)
    hrc_method=$(header_value "${ref_csv}" hrc_method)
    rsampling=$(header_value "${ref_csv}" restrictedsampling)
    rswidth=$(header_value "${ref_csv}" rswidth)
    source_path=$(header_value "${ref_csv}" out)

    local ref_version scheme
    ref_version=$(nesspy_version "${ref_csv}")
    # Resolved through schemes.py, never re-implemented here: the hrc_method ->
    # scheme mapping changed at nesspy 1.9.0 and depends on the version.
    scheme=$(uv run --project "${REPO_DIR}" python "${REPO_DIR}/database/resolve_scheme.py" \
                 "${hrc:-False}" "${hrc_method:-1.0}" "${ref_version}" 2>/dev/null || echo "UNRESOLVED")

    # --- per-mu table, collected once and reused for the warnings ---------
    local rows="" versions=""
    local mu_names=() mu_trajs=()
    for d in "${mu_dirs[@]}"; do
        local mu csv version traj reps lattices
        mu="$(basename "${d}")"
        csv="${d}/out.csv"
        if [[ ! -f "${csv}" ]]; then
            echo "- mu folder \`${mu}\` has no out.csv (run never completed?)" >> "${warn_tmp}"
            rows+="| ${mu} | - | - | - | - |"$'\n'
            continue
        fi
        version=$(nesspy_version "${csv}")
        traj=$(trajectory_count "${csv}")
        reps=$(find "${d}" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
        lattices=$(find "${d}" -name lattice_final.npy | wc -l | tr -d ' ')
        rows+="| ${mu} | ${version:-unknown} | ${traj} | ${reps} | ${lattices} |"$'\n'
        versions+="${version:-unknown}"$'\n'
        mu_names+=("${mu}")
        mu_trajs+=("${traj}")

        if [[ "${traj}" -eq 0 ]]; then
            echo "- mu folder \`${mu}\`: out.csv has no data rows" >> "${warn_tmp}"
        fi
        if [[ "${lattices}" -lt "${reps}" ]]; then
            echo "- mu folder \`${mu}\`: ${lattices} lattice_final.npy for ${reps} replicate folder(s)" >> "${warn_tmp}"
        fi

        # header parameters must agree across every mu folder of one run
        local key ref_val this_val
        for key in jhom jhet fres drive rate xsize ysize hrc_method; do
            ref_val=$(header_value "${ref_csv}" "${key}")
            this_val=$(header_value "${csv}" "${key}")
            if [[ "${ref_val}" != "${this_val}" ]]; then
                echo "- mu folder \`${mu}\`: ${key} = ${this_val} but the run's reference says ${ref_val}" >> "${warn_tmp}"
            fi
        done
    done

    # A short trajectory count is what an out-of-memory kill looks like on disk.
    # The yardstick is the MODAL count across the run, not the maximum: a mu that
    # was deliberately resampled twice (64 rows where the rest have 32) would
    # otherwise make every healthy folder look short.
    local modal_traj=0 i
    if [[ "${#mu_trajs[@]}" -gt 0 ]]; then
        modal_traj=$(printf '%s\n' "${mu_trajs[@]}" \
            | sort -n | uniq -c | sort -k1,1rn -k2,2rn | head -1 | awk '{print $2}')
    fi
    for i in "${!mu_names[@]}"; do
        if [[ "${mu_trajs[$i]}" -gt 0 && "${mu_trajs[$i]}" -lt "${modal_traj}" ]]; then
            echo "- mu folder \`${mu_names[$i]}\`: only ${mu_trajs[$i]} trajectories (most folders in this run have ${modal_traj})" >> "${warn_tmp}"
        fi
    done

    # --- version marker files ---------------------------------------------
    local uniq_versions
    uniq_versions=$(printf '%s' "${versions}" | sort -u | grep -v '^$' || true)
    rm -f "${run_dir}"/*.version
    local v n_versions=0
    while IFS= read -r v; do
        if [[ -n "${v}" ]]; then
            touch "${run_dir}/${v}.version"
            n_versions=$((n_versions + 1))
        fi
    done <<< "${uniq_versions}"
    if [[ "${n_versions}" -gt 1 ]]; then
        echo "- run mixes several nesspy versions: ${uniq_versions//$'\n'/ }" >> "${warn_tmp}"
    fi

    # --- slurm logs, if the run has any -----------------------------------
    # Jobs currently write their logs to ~/slurm_reports/ on della, so most runs
    # have none. Future runs are expected to keep them next to the data.
    local slurm_logs slurm_note="none found"
    slurm_logs=$(find "${run_dir}" -maxdepth 2 -type f -name 'slurm*' | sort)
    if [[ -n "${slurm_logs}" ]]; then
        slurm_note="checked $(printf '%s\n' "${slurm_logs}" | grep -c .) file(s)"
        while IFS= read -r log; do
            if grep -qiE 'error|out of memory|oom|cancelled|time limit' "${log}"; then
                echo "- slurm log \`$(basename "${log}")\` reports an error:" >> "${warn_tmp}"
                grep -iE 'error|out of memory|oom|cancelled|time limit' "${log}" | head -3 | sed 's/^/    /' >> "${warn_tmp}"
            fi
        done <<< "${slurm_logs}"
    fi

    # --- advisory: folder name vs header ----------------------------------
    # Run folder names use several different encodings, some with the decimal
    # point dropped (K0001 = 0.001, JHOM_285 = -2.85). This comparison is
    # therefore ADVISORY ONLY and expected to be noisy on older directories; the
    # header is always the authority.
    local name advisory=""
    name="$(basename "${run_dir}")"
    # DRIVE is checked before the shorter D so that "DRIVE10" is not read as "D".
    if [[ "${name}" =~ (^|_)DRIVE(-?[0-9.]+)(_|$) ]]; then
        check_token "DRIVE" "${BASH_REMATCH[2]}" "${drive}"
    elif [[ "${name}" =~ (^|_)D(-?[0-9.]+)(_|$) ]]; then
        check_token "D (drive)" "${BASH_REMATCH[2]}" "${drive}"
    fi
    if [[ "${name}" =~ (^|_)K(-?[0-9.]+)(_|$) ]]; then
        check_token "K (rate)" "${BASH_REMATCH[2]}" "${rate}"
    fi
    if [[ "${name}" =~ (^|_)F(-?[0-9.]+)(_|$) ]]; then
        check_token "F (fres)" "${BASH_REMATCH[2]}" "${fres}"
    fi
    if [[ "${name}" =~ X_([0-9]+)_Y_([0-9]+) ]]; then
        check_token "X (xsize)" "${BASH_REMATCH[1]}" "${xsize}"
        check_token "Y (ysize)" "${BASH_REMATCH[2]}" "${ysize}"
    fi
    if [[ "${name}" =~ SCHEME_?([0-9]+) ]]; then
        check_token "SCHEME (hrc_method)" "${BASH_REMATCH[1]}" "${hrc_method}"
    fi
    if [[ -z "${advisory}" ]]; then
        advisory="- nothing to compare, or folder name and header agree."$'\n'
    fi

    # --- write the catalog -------------------------------------------------
    {
        echo "# Run catalog: ${name}"
        echo
        echo "Catalogued: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Path: \`${run_dir}\`"
        echo "Source on della: \`${source_path:-unknown}\`"
        echo
        echo "## Parameters (from the out.csv header)"
        echo
        echo "| Parameter | Value |"
        echo "|---|---|"
        echo "| driving scheme | **${scheme}** |"
        echo "| nesspy version | ${ref_version:-unknown} |"
        echo "| jhom | ${jhom:-?} |"
        echo "| jhet | ${jhet:-?} |"
        echo "| fres | ${fres:-?} |"
        echo "| drive (dmu) | ${drive:-?} |"
        echo "| rate (k) | ${rate:-?} |"
        echo "| xsize x ysize | ${xsize:-?} x ${ysize:-?} |"
        echo "| hrc / hrc_method | ${hrc:-?} / ${hrc_method:-?} |"
        echo "| restricted sampling | ${rsampling:-?} (width ${rswidth:-?}) |"
        echo "| slurm logs | ${slurm_note} |"
        echo
        echo "## Data per chemical potential"
        echo
        echo "One out.csv per mu; 'trajectories' is the number of independent data rows in it."
        echo
        echo "${#mu_names[@]} chemical potential(s) sampled, typically ${modal_traj} trajectories each."
        echo
        echo "| mu | nesspy version | trajectories | replicate folders | lattice_final.npy |"
        echo "|---|---|---|---|---|"
        printf '%s' "${rows}"
        echo
        echo "## Advisory: folder name vs header"
        echo
        echo "The header is authoritative. Folder names use several encodings and some drop"
        echo "the decimal point, so mismatches here are informational, not errors."
        echo
        printf '%s' "${advisory}"
    } > "${catalog}"

    # --- write (or clear) the warning file ---------------------------------
    if [[ -s "${warn_tmp}" ]]; then
        {
            echo "# Flagged warnings: ${name}"
            echo
            echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
            echo
            cat "${warn_tmp}"
        } > "${warnings}"
        echo "  catalogued -- ${WARNING_FILE} written ($(grep -c '^- ' "${warn_tmp}") issue(s))"
    else
        rm -f "${warnings}"
        echo "  catalogued -- no warnings"
    fi
    rm -f "${warn_tmp}"
}

# --- main loop -----------------------------------------------------------

n_done=0
n_skipped=0
while IFS= read -r run_dir; do
    catalog="${run_dir}/${CATALOG_FILE}"
    # up to date when the catalog exists and no out.csv is newer than it
    if [[ "${FORCE}" -eq 0 && -f "${catalog}" ]] && \
       [[ -z "$(find "${run_dir}" -name out.csv -newer "${catalog}" -print -quit)" ]]; then
        n_skipped=$((n_skipped + 1))
        continue
    fi
    echo "$(basename "${run_dir}")"
    catalog_run "${run_dir}"
    n_done=$((n_done + 1))
done < <(find_run_dirs)

echo
echo "Cataloging done: ${n_done} run(s) catalogued, ${n_skipped} already up to date."
