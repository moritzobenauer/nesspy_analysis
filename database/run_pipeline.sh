#!/usr/bin/env bash
#
# The whole research-data pipeline in one command:
#   1. sync new results down from della
#   2. catalog them (parameters, scheme, trajectory counts, warnings)
#   3. run the order-disorder analysis on whatever still needs it
#
# Any -f is forwarded to stages 2 and 3, forcing a re-catalog and re-analysis of
# every run rather than only the ones that changed.
#
# Usage: run_pipeline.sh [-f]

set -euo pipefail
HERE="$(dirname "${BASH_SOURCE[0]}")"

echo "=== 1/3  sync ==="
bash "${HERE}/sync_from_della.sh"

echo
echo "=== 2/3  catalog ==="
bash "${HERE}/catalog.sh" "$@"

echo
echo "=== 3/3  analyze ==="
bash "${HERE}/analyze_new.sh" "$@"
