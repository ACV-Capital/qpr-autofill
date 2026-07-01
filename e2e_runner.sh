#!/usr/bin/env bash
# e2e_runner.sh — convenience wrapper for the QPR E2E test.
#
# Usage:
#   cd ~/Documents/Projects/qpr-autofill
#   ./e2e_runner.sh 2026Q2
#
# SA resolution (in order):
#   1. $E2E_SA env var if set
#   2. ~/Documents/Projects/qpr-autofill-e2e/secrets/service-account.json (separate E2E SA)
#   3. ~/Documents/Projects/macro-research/service-account.json (production SA — same as prod)
#
# IMPORTANT: the E2E was designed to use a separate SA so a buggy subagent
# can't write to the production sheet. If you point this at the production
# SA, the secluded env loses that safety property — make sure you trust the
# fresh agent to behave.
#
# Prerequisites (one-time setup, see docs/E2E.md):
#   1. A service account JSON (separate E2E or same as production)
#   2. The E2E GSheet is shared with that SA as Editor
#   3. The plugin is built and installed: pip install -e ".[dev]"

set -euo pipefail

QUARTER="${1:-2026Q2}"
E2E_DIR="$HOME/Documents/Projects/qpr-autofill-e2e"
PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"

# Default sheet — replace with your actual E2E GSheet ID
SHEET_ID="${QPR_TEST_SHEET_ID:-1G-2Ph56pH5jB7G3GefIv9xXb65A1txH_Dhz9JJLepgg}"

# Resolve SA path: env var > E2E dir > production
if [ -n "${E2E_SA:-}" ] && [ -f "$E2E_SA" ]; then
    SA="$E2E_SA"
elif [ -f "$E2E_DIR/secrets/service-account.json" ]; then
    SA="$E2E_DIR/secrets/service-account.json"
elif [ -f "$HOME/Documents/Projects/macro-research/service-account.json" ]; then
    SA="$HOME/Documents/Projects/macro-research/service-account.json"
    echo "WARNING: using PRODUCTION service account. E2E secluded-env safety is reduced."
    echo "         a buggy subagent could write to the production working sheet."
    echo "         set E2E_SA=... to use a separate SA, or copy the prod SA to:"
    echo "         $E2E_DIR/secrets/service-account.json"
    echo
else
    echo "ERROR: no service account found." >&2
    echo "  Set E2E_SA=/path/to/sa.json, OR" >&2
    echo "  Copy your SA to: $E2E_DIR/secrets/service-account.json" >&2
    exit 1
fi

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
