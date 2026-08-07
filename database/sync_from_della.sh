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

echo "Syncing ${DELLA_HOST}:${DELLA_DIR}/ -> ${LOCAL_DIR}/"

# --- dry run -------------------------------------------------------------
# -i (itemize) prints one line per file that would change, prefixed by a change
# code such as '>f+++++++++' (new/updated file) or 'cd+++++++++' (new directory).
echo "Checking for new data (dry run)..."
if ! rsync -ai --dry-run "${DELLA_HOST}:${DELLA_DIR}/" "${LOCAL_DIR}/" > "${SYNC_LOG}" 2>&1; then
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
echo "${NEW_COUNT} new/updated file(s). Transferring..."
if ! rsync -a --info=progress2 "${DELLA_HOST}:${DELLA_DIR}/" "${LOCAL_DIR}/" 2>&1 | tee -a "${SYNC_LOG}"; then
    echo "ERROR: rsync transfer failed. See ${SYNC_LOG}." >&2
    exit 1
fi

echo "Sync complete. ${NEW_COUNT} file(s) transferred."
echo "  log:       ${SYNC_LOG}"
echo "  new files: ${NEW_LIST}"
