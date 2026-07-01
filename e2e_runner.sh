#!/usr/bin/env bash
# e2e_runner.sh — convenience wrapper for the QPR E2E test.
#
# Usage:
#   cd ~/Documents/Projects/qpr-autofill
#   ./e2e_runner.sh 2026Q2
#
# Prerequisites (one-time setup, see docs/E2E.md):
#   1. ~/Documents/Projects/qpr-autofill-e2e/secrets/service-account.json exists
#   2. The E2E GSheet is shared with that SA as Editor
#   3. The plugin is built and installed: pip install -e ".[dev]"

set -euo pipefail

QUARTER="${1:-2026Q2}"
E2E_DIR="$HOME/Documents/Projects/qpr-autofill-e2e"
PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SA="$E2E_DIR/secrets/service-account.json"

# Default sheet — replace with your actual E2E GSheet ID
SHEET_ID="${QPR_TEST_SHEET_ID:-1G-2Ph56pH5jB7G3GefIv9xXb65A1txH_Dhz9JJLepgg}"

if [ ! -f "$SA" ]; then
    echo "ERROR: E2E service account not found at $SA" >&2
    echo "       See docs/E2E.md for one-time setup." >&2
    exit 1
fi

# Use the E2E SA, not the production one
export GOOGLE_APPLICATION_CREDENTIALS="$SA"

# Python — use the macro-research venv (Python 3.11+)
PYTHON="${QPR_PYTHON:-/Users/acvcapital/Documents/Projects/macro-research/.venv/bin/python}"

echo "QPR E2E runner"
echo "  Quarter: $QUARTER"
echo "  Sheet: $SHEET_ID"
echo "  Workdir: $E2E_DIR"
echo "  Plugin: $PLUGIN_DIR"
echo "  SA: $SA"
echo

# Phase 1: render the brief and print dispatch instructions
"$PYTHON" -m qpr e2e-run \
    --quarter "$QUARTER" \
    --sheet-id "$SHEET_ID" \
    --workdir "$E2E_DIR" \
    --plugin-dir "$PLUGIN_DIR" \
    --write-brief-only

echo
echo "Brief written to: $E2E_DIR/AGENT_SSSG_${QUARTER}_E2E_BRIEF.md"
echo
echo "NEXT STEPS (see docs/E2E.md for full details):"
echo
echo "  1. Spawn a fresh subagent (Hermes / Claude Code) with:"
echo "       delegate_task("
echo "           goal='Research SSSG for $QUARTER per the brief',"
echo "           workdir='$E2E_DIR',"
echo "           toolsets=['web', 'browser', 'file', 'coding'],"
echo "           role='leaf',"
echo "       )"
echo
echo "  2. After the subagent finishes, grade the E2E:"
echo "       GOOGLE_APPLICATION_CREDENTIALS=$SA \\"
echo "         $PYTHON -m qpr grade-e2e \\"
echo "           --e2e-sheet-id $SHEET_ID \\"
echo "           --ref-sheet-id $SHEET_ID \\"
echo "           --tab reference_truth \\"
echo "           --prior-cycle-path ~/Documents/Projects/macro-research/notes/agent_sssg_r5_a_results.json"
