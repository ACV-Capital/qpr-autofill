# QPR Auto-Fill

> Quarterly research auto-fill for SEA-5 macro and retail SSSG.
> One Claude Code plugin + Python package. Self-defensible research, no hidden answer keys.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What

QPR (Quarterly Research) Auto-Fill is a research workflow for ACV Capital's
quarterly SEA-5 (Indonesia, Thailand, Philippines, Malaysia, Vietnam) coverage:

- **Macro panel**: Real GDP growth, private consumption, FX — for each of the
  5 countries, sourced from primary statistical agencies.
- **Retail SSSG panel**: Same-store sales growth for ~20 retail tickers across
  the 5 countries, sourced from company MD&A, IR pages, and respected business
  news.

The workflow was first built during a Q4'25 + Q1'26 research cycle and is now
encoded as a Claude Code plugin (agents + skills) plus a Python package that
handles cell-level grading, source verification, and per-ticker channel memory.

## Why

A reference sheet is a development-time artifact, not a permanent fixture.
This plugin produces research that is **self-defensible** without a hidden
answer key: every value cites a public source, and a built-in check flags any
cell whose only source is a broker (those need a primary cross-check).

After the v0.1 release, the reference sheet is gone. The plugin stands on its
methodology alone.

## Install

```bash
git clone https://github.com/ACV-Capital/qpr-autofill.git
cd qpr-autofill
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

For Claude Code users, drop the repo into your plugins directory and
`.claude-plugin/plugin.json` will be picked up automatically.

## Quickstart

Run a quarterly research cycle:

```bash
# Render a brief per agent (SSSG + macro), with channel memory cheat sheet
.venv/bin/python -m qpr run-quarter 2026Q2

# Dispatch 2 subagents with the briefs. They return JSON results.
# (See docs/E2E.md for how to spawn a secluded fresh agent for validation.)

# After agents return, verify each URL and run the self-defensibility gate
.venv/bin/python -m qpr verify-results results/agent1.json results/agent2.json
.venv/bin/python -m qpr preflight --sheet-id <working_sheet_id>

# Write verified values to the working sheet
.venv/bin/python -m qpr write-sheet --sheet-id <working_sheet_id> --from-json results/verified.json

# Update the channel memory for next cycle
.venv/bin/python -m qpr update-channel-memory --sheet-id <working_sheet_id> --memory-file qpr/data/channel_memory.json
```

## Architecture

- **`.claude-plugin/plugin.json`** — plugin manifest for Claude Code
- **`agents/`** — two agents: `qpr-macro` and `qpr-sssg`
- **`skills/`** — three skills:
  - `qpr-research-rules` — the 9 hard rules (loaded by both agents)
  - `qpr-sheets-api` — read/write/color a working Google Sheet
  - `qpr-source-verification` — open a URL, confirm a value, classify its tier
  - `qpr-source-verification/scripts/verify.sh` — runnable shell wrapper
- **`qpr/`** — Python package:
  - `classify.py` — cell-level match/differ/null with tolerance
  - `tickers.py` — canonical SEA-5 retail ticker manifest loader
  - `verify.py` — confirm a value is on a saved page with rounding tolerance
  - `brief.py` — render an agent brief with channel memory cheat sheet
  - `channel_memory.py` — per-ticker source memory with auto promote/demote
  - `grade_e2e.py` — E2E grader (match + leakage + self-defensible check)
  - `sheets.py` — gspread wrapper (read/write cell, set fill)
  - `cli.py` — entry point: `run-quarter`, `verify-results`, `preflight`, `write-sheet`, `update-channel-memory`, `grade`, `grade-e2e`, `e2e-run`
- **`qpr/data/channel_memory.json`** — the "try this first" list per ticker,
  seeded from the Q1'26 cycle (17 retail + 5 macro entries)
- **`examples/tickers.yaml`** — SEA-5 retail universe (25 tickers)
- **`examples/working_q1_2026.json`** — redacted Q1'26 working data
- **`tests/`** — pytest suite, 61 tests, all passing

## Hard Rules

These live in `skills/qpr-research-rules/SKILL.md` and are loaded by every
agent. They are the actual IP of the project:

1. **Reference sheet is a HIDDEN GRADING ARTIFACT.** Never read it during
   research. Never copy it. (Used only for the E2E; not present in production.)
2. **Subagents do all research from public sources** (regulator sites, IR
   pages, financial reports). Subagents never see the reference sheet ID.
3. **Every value must come with a specific source URL.** "BPS" or "quarterly
   earnings presentation" is NOT a source.
4. **Hermes opens each URL itself** and confirms the value is on the page
   before writing.
5. **Reference is consulted only at the end** for grading, never as a source.
6. **Copy exact underlying numeric value** (e.g. 32.54, not "32.5").
7. **3-layer verification** before any write: period (Q1'26, not FY25),
   metric (SSSG, not revenue growth), scope (brand vs consolidated).
8. **Tolerance** is 0.5pp for rounded SSSG, 0.05pp for primary-source 2-decimal.
   "Both null" is success, not a gap.
9. **Self-defensible research.** Every cell must be defensible on its own.
   Macro: primary statistical agency or major news wire. SSSG: company MD&A
   or quarterly results presentation; respected business news as fallback;
   broker research only as cross-check. Two-source rule for values >±5pp
   or partner-facing.

## Tickers Manifest

The canonical SEA-5 retail universe is `examples/tickers.yaml`. Add or remove
tickers as the universe evolves. Each entry has:

```yaml
- exchange: IDX          # IDX, SET, KLSE, PSE, HSX, SGX
  ticker: ACES
  company: Ace Hardware Indonesia
  subsector: specialty retail (home improvement)
  sssg_applicable: true
  notes: "Consolidated SSSG via Bisnis/CGS; brand-only SSSG via kontan.co.id"
```

## Channel Memory

`qpr/data/channel_memory.json` is the "try this first" list per ticker. After
every cycle, run `qpr update-channel-memory` to:

- Increment `success_count` for channels that produced a value
- Demote channels that failed 2 cycles in a row (tier 1 → tier 3)
- Add new domains to tier 3 (promote to tier 2 after one success)

The next cycle's brief starts each ticker search from the highest-priority
working channel. Channels that fail 2+ times in a row get downgraded
automatically.

## E2E Test

`docs/E2E.md` walks through setting up a secluded sandbox, creating a separate
service account, and running a fresh agent in a totally isolated environment
to validate that the plugin works without leaking your prior cycle's results.

## Contributing

The reference sheet is gone after v0.1. To extend the plugin:

- Add new tickers to `examples/tickers.yaml`
- Add new channels to `qpr/data/channel_memory.json` after each successful cycle
- Improve the hard rules in `skills/qpr-research-rules/SKILL.md` only with
  care — they encode the methodology that makes the plugin work

## License

MIT — see [LICENSE](./LICENSE).
