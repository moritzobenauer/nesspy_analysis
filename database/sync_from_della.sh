#!/usr/bin/env bash
#
# Stage 1: keep LOCAL_DIR in sync with DELLA_DIR on the cluster.
#
# A dry run goes first so we can see what would arrive before anything is
# transferred. If it lists nothing, we stop — there is no new data and no reason
# to run the rest of the pipeline.
#
# The copy is strictly one-directional and additive: no --delete, ever. That is
# what makes it safe for catalog.sh to write run_catalog.md / *.version /
# flagged_warning.md straight into the mirrored run folders — rsync leaves local
# files it does not know about alone.
#
# Usage: sync_from_della.sh

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
check_config

TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
SYNC_LOG="${LOG_DIR}/sync_${TIMESTAMP}.log"
NEW_LIST="${LOG_DIR}/new_${TIMESTAMP}.txt"

# BUGFIX 2026-08-07 the pipeline is meant to run *while* jobs are still going on
# della, so directories are created and removed under DELLA_DIR the whole time
# rsync is scanning it. When rsync notices a path it has already listed is gone
# it reports that and exits non-zero, and this script treated that as a fatal
# error — which aborted every single cycle of the watcher even though the
# listing/transfer was otherwise complete.
#
# Nothing is actually lost: whatever still existed was handled, and anything
# that moved is picked up by the next cycle. So this helper runs rsync and
# forgives exactly that one condition:
#
#   - GNU rsync (3.x) has a dedicated exit code for it, 24 ("partial transfer
#     due to vanished source files").
#   - openrsync — which is what macOS ships, see the note further down — has no
#     such code, so we fall back to reading its complaints: if every one of them
#     is a 'directory has vanished' line and nothing else went wrong, carry on.
#
# Output goes to the log only; a 168k-file listing would otherwise flood the
# terminal (and the watcher's log).
#
# Usage: run_rsync <log file> <rsync args...>
run_rsync() {
    local log="$1"; shift
    local status=0

    rsync "$@" >> "${log}" 2>&1 || status=$?
    if [[ "${status}" -eq 0 ]]; then
        return 0
    fi

    if [[ "${status}" -eq 24 ]]; then
        echo "  note: source files vanished on della mid-sync (rsync exit 24) — continuing."
        return 0
    fi

    if grep -q 'has vanished' "${log}" \
       && ! grep -qiE 'error|failed|refused|denied|usage: rsync' "${log}"; then
        echo "  note: source paths vanished on della mid-sync (openrsync, exit ${status}) — continuing."
        return 0
    fi

    return "${status}"
}

echo "Syncing ${DELLA_HOST}:${DELLA_DIR}/ -> ${LOCAL_DIR}/"

# --- dry run -------------------------------------------------------------
# -i (itemize) prints one line per file that would change, prefixed by a change
# code such as '>f+++++++++' (new/updated file) or 'cd+++++++++' (new directory).
echo "Checking for new data (dry run)..."
if ! run_rsync "${SYNC_LOG}" -ai --dry-run "${DELLA_HOST}:${DELLA_DIR}/" "${LOCAL_DIR}/"; then
    echo "ERROR: rsync dry run failed. See ${SYNC_LOG}:" >&2
    tail -5 "${SYNC_LOG}" >&2
    exit 1
fi

# Keep only the file transfers (change code starting with '>'), dropping the
# directory entries and rsync's own summary lines.
grep '^>' "${SYNC_LOG}" | awk '{print $2}' > "${NEW_LIST}" || true
NEW_COUNT=$(wc -l < "${NEW_LIST}" | tr -d ' ')

if [[ "${NEW_COUNT}" -eq 0 ]]; then
    echo "No new data on della. Nothing to transfer."
    exit 0
fi

# --- real transfer -------------------------------------------------------
# BUGFIX 2026-08-07 this used --info=progress2, which only exists in rsync 3.x.
# macOS ships openrsync ("rsync version 2.6.9 compatible"), which rejects it and
# prints its usage instead of transferring. The dry run above uses -ai, which
# openrsync does support, so the failure only showed up on the real transfer.
# --stats works on both and reports a compact summary instead of a per-file
# progress stream (a 168k-file transfer would otherwise flood the log).
echo "${NEW_COUNT} new/updated file(s). Transferring..."
if ! run_rsync "${SYNC_LOG}" -a --stats "${DELLA_HOST}:${DELLA_DIR}/" "${LOCAL_DIR}/"; then
    echo "ERROR: rsync transfer failed. See ${SYNC_LOG}:" >&2
    tail -5 "${SYNC_LOG}" >&2
    exit 1
fi

# run_rsync logs instead of printing, so surface rsync's own summary here.
sed -n '/^Number of files:/,/^Total bytes received:/p' "${SYNC_LOG}" | sed 's/^/  /'

echo "Sync complete. ${NEW_COUNT} file(s) transferred."
echo "  log:       ${SYNC_LOG}"
echo "  new files: ${NEW_LIST}"
