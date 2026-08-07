#!/usr/bin/env bash
#
# The whole research-data pipeline in one command:
#   1. sync new results down from della
#   2. catalog them (parameters, scheme, trajectory counts, warnings)
#   3. run the order-disorder analysis on whatever still needs it
#   4. hand the freshly analyzed data to Claude, which fills in results.xlsx
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
echo "=== 3/4  analyze ==="
# analyze_new.sh exits non-zero when a run newly fails to analyze. That must not
# stop us from recording the runs that *did* succeed, so we hold on to its status
# and re-raise it at the very end instead of letting `set -e` abort here.
analyze_status=0
bash "${HERE}/analyze_new.sh" "$@" || analyze_status=$?

echo
echo "=== 4/4  fill in the spreadsheet ==="
# Claude reads the analysis output produced above and transcribes it into
# database/results.xlsx. Run from the repository root so that the `@database/...`
# file reference in the prompt resolves.
REPO_ROOT="$(cd "${HERE}/.." && pwd)"
(
  cd "${REPO_ROOT}"
  claude -p "Look at the @database/results.xlsx file. Based on the newly analyzed data fill out that spread sheet. Never touch the MLO_CHECK column." --model claude-sonnet-5
)

exit "${analyze_status}"
