#!/usr/bin/env bash
# Shared configuration for the research-data pipeline in database/.
#
# This file holds paths only. It is sourced by sync_from_della.sh, catalog.sh and
# analyze_new.sh, so retargeting the pipeline to a different campaign means
# editing the two values below and nothing else.

# ---------------------------------------------------------------------------
# FILL IN: the directory on della to sync FROM.
# Downloads are only allowed from /home/mo9089/... or /scratch/gpfs/WJACOBS/MLO/...
# Point this at a whole project (e.g. .../MLO/NEW_EXPS) to sync one campaign.
# ---------------------------------------------------------------------------
DELLA_DIR="/scratch/gpfs/WJACOBS/MLO/MANUSCRIPT_2026"

# ---------------------------------------------------------------------------
# FILL IN: the local directory to sync INTO. This becomes a verbatim mirror of
# DELLA_DIR — nothing is ever moved or renamed inside it, so a later re-sync
# never re-downloads data. The cataloging step writes its report files directly
# into the run folders here.
# ---------------------------------------------------------------------------
LOCAL_DIR="/Volumes/2025/MANUSCRIPT_2026"

# SSH alias for the cluster (configured in ~/.ssh/config).
DELLA_HOST="della"

# How often watch_pipeline.sh runs a full sync/catalog/analyze cycle, in minutes.
# The clock starts when a cycle *finishes*, so cycles never overlap however long
# the analysis takes.
PIPELINE_INTERVAL_MIN=60

# Repo root, derived from this file's location — used to locate the analysis
# scripts in 2026/ and the helper in database/.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Where the pipeline writes its own logs (kept out of the mirrored data).
LOG_DIR="${LOCAL_DIR}/_logs"

# Filenames written into each run directory by catalog.sh.
CATALOG_FILE="run_catalog.md"
WARNING_FILE="flagged_warning.md"

# Written into a run directory by analyze_new.sh when the analysis of that run
# fails. Its presence is what stops the watcher from retrying a hopeless run on
# every cycle; it is removed again as soon as the run analyses successfully.
FAILED_FILE="analysis_failed.md"

# Abort early with a clear message if LOCAL_DIR has not been set up yet.
check_config() {
    if [[ -z "${LOCAL_DIR}" ]]; then
        echo "ERROR: LOCAL_DIR is empty. Edit ${REPO_DIR}/database/config.sh." >&2
        exit 1
    fi
    if [[ ! -d "${LOCAL_DIR}" ]]; then
        echo "ERROR: LOCAL_DIR '${LOCAL_DIR}' does not exist." >&2
        exit 1
    fi
    mkdir -p "${LOG_DIR}"
}

# Every run directory in the local mirror, one per line.
#
# A run directory is the parent of the mu subfolders, i.e. the grandparent of an
# out.csv (LOCAL_DIR/<...>/<run>/<mu>/out.csv). Deriving it this way instead of
# assuming a fixed depth is what lets the same script handle both
# RETHINKING_SUPERSAT/<run>/<mu>/ and COMPARING_SCHEMES/SCHEME6/D05/<mu>/.
find_run_dirs() {
    find "${LOCAL_DIR}" -name out.csv -not -path "${LOG_DIR}/*" -print0 \
        | xargs -0 -n1 dirname \
        | xargs -n1 dirname \
        | sort -u
}
