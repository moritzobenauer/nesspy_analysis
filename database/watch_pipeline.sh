#!/usr/bin/env bash
#
# Run the whole pipeline (sync -> catalog -> analyze) every
# PIPELINE_INTERVAL_MIN minutes, forever. Meant to be left running in the
# background while jobs are still finishing on della.
#
#   # start it in the background, detached from this terminal
#   nohup bash database/watch_pipeline.sh > /dev/null 2>&1 &
#
#   # watch what it is doing
#   tail -f <LOCAL_DIR>/_logs/watch.log
#
#   # stop it
#   kill "$(cat <LOCAL_DIR>/_logs/watch.pid)"
#
# Notes on the two things that matter for something long-running:
#
#   - Deliberately no `set -e`: a failed cycle (della unreachable, one run that
#     cannot be fitted) must not kill the watcher. Failures are logged and the
#     next cycle goes ahead.
#   - A lock directory makes sure only one watcher runs per LOCAL_DIR, so a
#     second accidental start cannot have two analyses writing into the same run
#     directory at once.
#
# Usage: watch_pipeline.sh [-f]     -f forces a full re-catalog/re-analysis every cycle

set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
check_config

# The interval must be a positive whole number of minutes. The :- default keeps
# this a readable error rather than an "unbound variable" crash when an older
# config.sh has no PIPELINE_INTERVAL_MIN at all.
if ! [[ "${PIPELINE_INTERVAL_MIN:-}" =~ ^[0-9]+$ ]] || [[ "${PIPELINE_INTERVAL_MIN}" -lt 1 ]]; then
    echo "ERROR: PIPELINE_INTERVAL_MIN must be a positive integer (minutes), got '${PIPELINE_INTERVAL_MIN:-unset}'." >&2
    echo "Set it in ${REPO_DIR}/database/config.sh." >&2
    exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCH_LOG="${LOG_DIR}/watch.log"
LOCK_DIR="${LOG_DIR}/watch.lock"
PID_FILE="${LOG_DIR}/watch.pid"
INTERVAL=$((PIPELINE_INTERVAL_MIN * 60))

# mkdir is atomic, so this is a race-free "only one watcher" check.
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    echo "A watcher is already running for ${LOCAL_DIR} (lock: ${LOCK_DIR})." >&2
    echo "If that is stale — no process left — remove the lock directory and start again." >&2
    exit 1
fi
echo "$$" > "${PID_FILE}"

SLEEP_PID=""
cleanup() {
    if [[ -n "${SLEEP_PID}" ]]; then kill "${SLEEP_PID}" 2>/dev/null; fi
    rmdir "${LOCK_DIR}" 2>/dev/null
    rm -f "${PID_FILE}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] watcher stopped." | tee -a "${WATCH_LOG}"
}
# The removal happens once, on EXIT. INT/TERM just ask for a clean exit, which
# then triggers it — otherwise the message would be printed twice.
trap cleanup EXIT
trap 'exit 0' INT TERM

{
    echo
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] watcher started (pid $$, every ${PIPELINE_INTERVAL_MIN} min)"
    echo "  local dir: ${LOCAL_DIR}"
} | tee -a "${WATCH_LOG}"

cycle=0
while true; do
    cycle=$((cycle + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] --- cycle ${cycle} ---" | tee -a "${WATCH_LOG}"

    if bash "${HERE}/run_pipeline.sh" "$@" >> "${WATCH_LOG}" 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] cycle ${cycle} finished" | tee -a "${WATCH_LOG}"
    else
        # Nothing fatal: della may be down, or a single run may have failed to
        # fit. Both are worth reporting and both are worth retrying next cycle.
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] cycle ${cycle} reported errors — see above" | tee -a "${WATCH_LOG}"
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] sleeping ${PIPELINE_INTERVAL_MIN} min" | tee -a "${WATCH_LOG}"

    # Sleep in the background and wait for it, rather than sleeping directly:
    # bash defers a trap until the running foreground command finishes, so a
    # plain `sleep` would make `kill` take up to a full interval to be noticed
    # and would leave the lock directory behind. `wait` is interruptible.
    sleep "${INTERVAL}" &
    SLEEP_PID=$!
    wait "${SLEEP_PID}" || true
    SLEEP_PID=""
done
