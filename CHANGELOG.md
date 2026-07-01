# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-01

### Added
- Initial release
- `qpr/classify.py` — cell-level match/differ/missing/extra with 0.5pp tolerance
- `qpr/tickers.py` — SEA-5 retail ticker manifest loader
- `qpr/verify.py` — confirm a value is on a saved page (with ±0.1pp rounding tolerance)
- `qpr/brief.py` — render an SSSG agent brief with channel memory cheat sheet
- `qpr/channel_memory.py` — per-ticker source memory with auto promote/demote
- `qpr/sheets.py` — gspread wrapper (read/write cell, set color)
- `qpr/grade_e2e.py` — E2E grader (match + leakage + self-defensible check)
- `qpr/cli.py` — entry point: `run-quarter`, `verify-results`, `preflight`,
  `update-channel-memory`, `grade`, `grade-e2e`, `e2e-run`
- `qpr/data/channel_memory.json` — seeded from Q1'26 cycle (17 retail + 5 macro entries)
- `examples/tickers.yaml` — 25 tickers (17 retail + 5 macro + 3 banks)
- `examples/working_q1_2026.json` — sample working data, redacted, no reference
- `agents/qpr-macro.md` — macro research agent
- `agents/qpr-sssg.md` — SSSG research agent
- `skills/qpr-research-rules/` — the 9 hard rules (the actual IP of the project)
- `skills/qpr-sheets-api/` — how to read/write the working sheet
- `skills/qpr-source-verification/` — how to confirm a value is on a page
- `docs/E2E.md` — how to set up and run the E2E test

### Notes
- The reference sheet is a development-time artifact, not part of production.
  See README "Why" section.
- The E2E test is the only place a reference sheet is consulted, and only at
  release time.
- 61 unit tests pass; no integration tests run against Google Sheets without
  a real service account.
