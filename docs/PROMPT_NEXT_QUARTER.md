# Q2 2026 SEA-5 research — agent prompt

You are running the next-quarter research cycle for ACV Capital's SEA-5 (Indonesia, Thailand, Philippines, Malaysia, Vietnam) coverage. The prior cycle (Q1 2026) is done; you are researching Q2 2026.

## Context

1. The plugin is at: https://github.com/ACV-Capital/qpr-autofill
2. Clone it: `git clone https://github.com/ACV-Capital/qpr-autofill.git ~/Documents/Projects/qpr-autofill && cd ~/Documents/Projects/qpr-autofill`
3. Install: `python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]`
   (Or reuse the existing `~/Documents/Projects/macro-research/.venv` which already has gspread, pyyaml, bs4, pytest.)
4. Load the `qpr-research-rules` skill — the 9 hard rules. They are non-negotiable.
5. Also load `qpr-source-verification` for how to confirm a value is on a page.

## Task

Run `qpr run-quarter 2026Q2` to render the SSSG + macro briefs. The SSSG brief includes a **channel memory cheat sheet** — a per-ticker list of known-working channels from the Q1 2026 cycle. Use those channels first. Only deep-research when they come up empty.

For each retail ticker, find the SSSG (same-store sales growth, YoY %) for Q2 2026. For each macro country, find GDP yoy, private consumption yoy, and FX. Every value must have a specific public source URL.

## Output

Write a JSON file per agent:
- `notes/agent_sssg_2026q2_<your_id>_results.json` (SSSG, ~20 tickers)
- `notes/agent_macro_2026q2_<your_id>_results.json` (5 countries)

Each result must include `channel_used` (one of: `tier_1`, `tier_2`, `tier_3`, `deep_research`) so the post-cycle refresher can update the channel memory.

## Critical: there is no reference sheet in production

This is a production run, not a graded test. There is no hidden answer key. Do not look for one. Every value must be defensible on its own:
- **Macro** (GDP, FX, private consumption): cite a primary statistical agency (BPS, NESDC, PSA, DOSM, GSO, BI, BOT) or a major news wire (Reuters, Bloomberg) that quoted the agency release.
- **SSSG**: cite the company's own quarterly results presentation or annual report MD&A when possible; fall back to respected business news (Bisnis, Kontan, The Edge, Insider Retail, Kaohoon, InsiderPH); use broker research (CGS, Indo Premier, Avrist, UOBKH, KGI) only as a secondary cross-check, never as the sole source.
- **Two-source rule** for any value above ±5pp or any value that drives a partner-facing claim.
- **Notes column** is mandatory: flag period, scope (brand vs consolidated), rounding, source disagreement.

## After you finish

1. Print a summary table: ticker | value | source domain | channel_used
2. The values will be verified URL-by-URL and run through a self-defensibility gate before being written to the working sheet.
3. Run `qpr update-channel-memory --results notes/agent_sssg_2026q2_<your_id>_results.json` to grow the memory for the next quarter.
4. Commit the new memory: `git commit -am "chore(memory): Q2'26 cycle update"`
5. Push the commit: `git push origin main`
