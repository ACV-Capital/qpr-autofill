#!/usr/bin/env bash
# verify.sh: confirm a value is on a saved page
# usage: ./verify.sh <saved_page.html> <value> [period]

set -euo pipefail

PAGE="$1"
VALUE="$2"
PERIOD="${3:-}"

if [ -z "$PAGE" ] || [ -z "$VALUE" ]; then
    echo "Usage: $0 <saved_page.html> <value> [period]" >&2
    exit 1
fi

# Find the right Python — prefer the macro-research venv (Python 3.11+)
PYTHON="${PYTHON:-/Users/acvcapital/Documents/Projects/macro-research/.venv/bin/python}"

if [ ! -x "$PYTHON" ]; then
    PYTHON="$(command -v python3)"
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Make the qpr package importable (in case the install was in a different venv)
QPR_PATH="$REPO_ROOT"
if [ -d "$REPO_ROOT/.venv" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
fi

exec "$PYTHON" -c "
import sys
sys.path.insert(0, '$QPR_PATH')
from qpr.verify import verify_value_on_page
res = verify_value_on_page('$PAGE', '$VALUE', period_hint='$PERIOD', allow_pp=True)
print(f'Found: {res.found}')
print(f'Matched text: {res.matched_text}')
print(f'Reason: {res.reason}')
print(f'Warning: {res.warning}')
if res.context_snippet:
    print(f'Context: {res.context_snippet}')
"
