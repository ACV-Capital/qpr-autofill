# E2E Test for QPR Auto-Fill

## Why

The E2E test proves that the plugin works for a **completely fresh agent** —
no memory of prior sessions, no access to prior research notes, no chance to
copy results. This is the only honest way to know the plugin will produce
defensible research in a future quarter when the reference sheet no longer
exists.

The E2E is run **once at plugin release time** to validate v0.1, then again
only when the plugin itself is updated (not when the data is updated).

## What it tests

A fresh subagent — spawned with `role="leaf"` and no `session_search` /
`memory` tools — is given:

- The freshly-built `qpr-autofill` plugin
- A Q2'26 brief (a quarter the prior cycle did NOT research)
- Public web access
- A separate Google service account with write access to a separate GSheet
- **No** access to `~/Documents/Projects/macro-research/`
- **No** access to prior `notes/agent_sssg_r*_*_results.json` files

The agent runs `/qpr-sssg 2026Q2` (or `/qpr-macro 2026Q2`) and writes its
findings to the E2E GSheet. A grader then compares the agent's output to a
hidden reference tab in the same GSheet.

## Pass thresholds

| Metric | Threshold |
|---|---|
| SSSG match rate (vs reference) | ≥ 80% |
| Macro primary-source rate | 100% (every macro cell cites BPS / NESDC / PSA / DOSM / GSO / BI / BOT or a news wire that quoted the agency) |
| Cells without source URL | 0 |
| Verbatim-copy warnings (proves secluded env leaked) | 0 |
| Cells not self-defensible (Tier 3 broker only) | ≤ 20% of cells with values |

The plugin is not "done" until all thresholds pass.

## Setup (one-time)

### 1. Create the secluded workdir

```bash
mkdir -p ~/Documents/Projects/qpr-autofill-e2e/secrets
cd ~/Documents/Projects/qpr-autofill-e2e
echo '*' > .gitignore  # nothing in this dir is committed
```

### 2. Create a separate service account

- Go to Google Cloud Console → IAM → Service Accounts
- Create `qpr-e2e-test@<your-project>.iam.gserviceaccount.com`
- Give it `Editor` on the E2E GSheet only (not the production sheet)
- Save the JSON key to `~/Documents/Projects/qpr-autofill-e2e/secrets/service-account.json`

### 3. Create the E2E GSheet

- Make a copy of the production Q1'26 working sheet
- Rename it to "QPR E2E — Q2 2026"
- Add a `reference_truth` tab with the expected Q2'26 values (you'll need
  to research these by hand from public sources before running the E2E;
  this is a one-time effort)
- Share the E2E GSheet with the new SA's email as Editor

### 4. Build the plugin as a wheel

```bash
cd ~/Documents/Projects/qpr-autofill
/Users/acvcapital/Documents/Projects/macro-research/.venv/bin/pip wheel . --no-deps -w /tmp/qpr-wheel
/Users/acvcapital/Documents/Projects/macro-research/.venv/bin/pip install /tmp/qpr-wheel/*.whl
```

## Run the E2E

```bash
cd ~/Documents/Projects/qpr-autofill

GOOGLE_APPLICATION_CREDENTIALS=$HOME/Documents/Projects/qpr-autofill-e2e/secrets/service-account.json \
QPR_TEST_SHEET_ID="<your-E2E-sheet-id>" \
/Users/acvcapital/Documents/Projects/macro-research/.venv/bin/python -m qpr e2e-run \
    --quarter 2026Q2 \
    --sheet-id "$QPR_TEST_SHEET_ID" \
    --workdir "$HOME/Documents/Projects/qpr-autofill-e2e"
```

The runner will spawn a subagent via `delegate_task` with:
- `role="leaf"` (no further delegation, no memory, no clarify)
- `toolsets=["web", "browser", "terminal", "file", "coding"]` (NO session_search, NO memory)
- `workdir=$HOME/Documents/Projects/qpr-autofill-e2e` (cannot cd to macro-research)

## Grade the E2E

After the agent finishes:

```bash
GOOGLE_APPLICATION_CREDENTIALS=$HOME/Documents/Projects/qpr-autofill-e2e/secrets/service-account.json \
/Users/acvcapital/Documents/Projects/macro-research/.venv/bin/python -m qpr grade-e2e \
    --e2e-sheet-id "$QPR_TEST_SHEET_ID" \
    --ref-sheet-id "$QPR_TEST_SHEET_ID" \
    --tab reference_truth \
    --prior-cycle-path /Users/acvcapital/Documents/Projects/macro-research/notes/agent_sssg_r5_a_results.json
```

The grader prints pass/fail per threshold and exits 0 on PASS.

## Common failure modes

| Failure | Likely cause | Fix |
|---|---|---|
| Agent can't find the test GSheet | Brief doesn't include the sheet ID | Add clearer GSheet access instructions to `qpr-sheets-api` skill |
| Agent uses revenue growth as SSSG | Hard rule 7 not loaded | Strengthen rule in `qpr-research-rules` skill |
| Agent uses FY25 data for a Q1'26 cell | Period check too soft | Strengthen rule 7 (3-layer verification) |
| Agent writes values without URLs | Rule 3 too soft | Add a "pre-flight" reminder in the agent prompt |
| Agent copies from `notes/agent_sssg_r5_*_results.json` | Secluded env leaked | Fix subagent's tool config in `qpr/cli.py` cmd_e2e_run |
| Only 30% of cells covered | Brief doesn't emphasize "do all cells" | Update template to show "do all cells" |
| High broker-only rate | Agent uses Tier 3 sources | Strengthen rule 9 (self-defensible research) |

Each fix is a new commit. Re-run the E2E. Stop when all thresholds pass.

## Worked example

(Fill in after the first successful E2E run.)

## After release

The E2E GSheet and reference truth are kept for **one cycle** to allow
re-runs if the plugin is updated. After that, the E2E artifacts can be
archived but are no longer needed in production.
